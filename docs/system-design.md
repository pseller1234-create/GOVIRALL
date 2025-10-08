# GoViralNow System Design

## High-Level Architecture
```mermaid
graph TD
    subgraph Client
        A[Web App]
        B[Mobile App]
        A -.->|WS / SSE| A2[Live Updates]
    end

    subgraph Edge
        C[API Gateway / FastAPI]
        D[Auth Service\nJWT + API Keys]
        C -->|Observability| C2[OTel Collector]
    end

    subgraph Backend
        E[Task Orchestrator\nCelery / FastAPI Background Tasks]
        F[Feature Extractor\nPython Workers]
        G[AI Inference Layer\nOpenAI + Custom Models]
        H[(PostgreSQL)]
        I[(Redis Queue + Cache)]
        Q[Vector Store\n(Phase 2)]
    end

    subgraph External APIs
        J[OpenAI APIs]
        K[Social APIs\n(TikTok, YouTube, Instagram, X)]
        R[Trust & Safety APIs\n(Moderation)]
    end

    subgraph Storage & Analytics
        L[Object Storage\n(S3-compatible)]
        M[Analytics Warehouse\nFuture: BigQuery/Snowflake]
        N[BI / Dashboards]
    end

    A -->|HTTPS| C
    B -->|HTTPS| C
    C --> D
    D --> C
    C -->|Sync| H
    C -->|Enqueue| I
    I --> E
    E --> F
    F --> G
    G -->|Insights| H
    G -->|Artifacts| L
    F -->|External Data| K
    G -->|LLM Calls| J
    G -->|Moderation| R
    E -->|Embeddings| Q
    Q --> G
    H -->|Dashboards| A
    H -->|Dashboards| B
    H --> M
    M --> N
```

**Flow Summary:**
1. Clients call FastAPI endpoints with JWT or API key authentication (all traffic through API gateway enforcing rate limits & WAF rules).
2. FastAPI performs schema validation (Pydantic), persists request metadata, emits OpenTelemetry spans, and enqueues heavy processing in Redis streams.
3. Background workers pull tasks, fetch enriched context via external social APIs, run multimodal feature extraction, and call the inference layer (OpenAI, custom CV/NLP) with deterministic prompts and safety guardrails.
4. Inference outputs and telemetry persist in PostgreSQL; large media artifacts land in object storage; embeddings optionally written to the vector store for retrieval-augmented follow-ups.
5. Clients poll, receive webhooks, or subscribe to SSE/WebSocket channels for completion status and render analytics dashboards.

### Component Responsibilities

| Component | Responsibilities | Tech Notes |
|-----------|-----------------|------------|
| API Gateway / FastAPI | Input validation, auth enforcement, routing, request throttling, API documentation | FastAPI + Uvicorn, rate limiting via Redis, OTel instrumentation |
| Auth Service | JWT issuing, API key rotation, RBAC policies, audit logging | OAuth2 password + client credentials grants; hashed API keys stored using Argon2 |
| Task Orchestrator | Dispatch async jobs, retries, dead-letter queue, metrics | Celery + Redis streams; exponential backoff; Prometheus exporter |
| Feature Extractor Workers | Download media, transcription, feature engineering, metadata normalization | ffmpeg, Whisper, spaCy; deterministic pipelines packaged in Docker |
| AI Inference Layer | Prompt templating, model selection, response validation, moderation | OpenAI GPT-4o mini/omni, on-device models for fallback, schema validation with Pydantic |
| Storage | Durable persistence for structured + unstructured data | PostgreSQL (HA), MinIO/S3, pg_partman for large tables |
| Observability | Monitoring, logging, alerting, anomaly detection | OpenTelemetry, Loki, Grafana, PagerDuty integration |

## Core APIs
| Endpoint | Method | Purpose | Request Contract | Response Contract |
|----------|--------|---------|------------------|-------------------|
| `/api/v1/analyze` | POST | Submit content (URL, upload, or text) for viral scoring. | `{"content_type": "video|post|text", "source_url"?: "https://...", "upload_id"?: "uuid", "caption"?: str, "platform_hint"?: "tiktok|youtube|instagram|x", "user_id": "uuid", "notify_webhook"?: "https://..." }` | `201 Created` with body `{"job_id": "uuid", "status": "queued", "estimated_completion_sec": int }`; error: `422` validation, `429` rate limit, `401` invalid token |
| `/api/v1/analyze/{job_id}` | GET | Retrieve analysis results. | Path `job_id`, optional query `include_insights=true`, `expand=metrics`. | `200 OK` body `{"job_id": "uuid", "status": "queued|processing|complete|failed", "score"?: 0-100, "confidence"?: 0-1, "insights"?: [...], "metrics"?: {...}, "created_at": iso8601, "completed_at"?: iso8601 }`; `404` if unknown job |
| `/api/v1/hooks/completion` | POST | Webhook target for partner integrations. | Signed payload `{"job_id": ..., "status": ..., "score"?: ..., "signature": ..., "timestamp": iso8601 }`; expects `X-GVN-Signature` header (HMAC-SHA256). | `204 No Content`; `401` signature mismatch |
| `/api/v1/auth/token` | POST | Exchange credentials/API key for JWT. | `{"client_id": ..., "client_secret": ...}` or `{"api_key": ...}` using TLS (mTLS optional). | `200 OK` body `{"access_token": ..., "expires_in": ..., "token_type": "bearer" }`; `403` if revoked |
| `/api/v1/users/{user_id}/history` | GET | Fetch user analysis history. | Path `user_id`, query pagination (`limit`, `cursor`), optional `status`. | `200 OK` body `{"items": [ { "job_id": ..., "score": ..., "status": ..., "created_at": ... } ], "next_cursor"?: ... }`; `404` if user missing |
| `/api/v1/insights/templates` | GET | Enumerate available insight categories for UI mapping. | None. | `200 OK` body `{"categories": [ { "id": "hook", "label": "Hook" }, ... ] }` |
| `/api/v1/admin/jobs` | GET | Internal dashboard for support + SRE. | Query filters `status`, `from`, `to`. | `200 OK` body `{"items": [...], "totals": {...} }`; requires `admin` scope |

**Error Model:** Standard error payload `{"error": {"code": str, "message": str, "details"?: dict }}` with trace ID header `x-request-id` for correlation.

## Data Models
- **User**: `{ id: UUID, email: str, hashed_secret: str, plan: enum(free, pro, enterprise), is_active: bool, rbac_roles: array, created_at: timestamptz, updated_at: timestamptz }`
- **ContentSubmission**: `{ id: UUID, user_id: UUID, content_type: enum(video, post, text), source_url?: text, storage_key?: text, caption?: text, platform_hint?: enum, status: enum(draft, queued, processing, complete, failed), created_at: timestamptz, updated_at: timestamptz }`
- **AnalysisJob**: `{ id: UUID, submission_id: UUID, status: enum(queued, processing, complete, failed, archived), score?: numeric(5,2), confidence?: numeric(3,2), errors?: jsonb, metrics?: jsonb, moderation_flags?: jsonb, completed_at?: timestamptz }`
- **Insight**: `{ id: UUID, job_id: UUID, category: enum(hook, pacing, emotion, storytelling, cta), message: text, recommendations: jsonb, weight: numeric(3,2) }`
- **WebhookSubscription**: `{ id: UUID, user_id: UUID, target_url: text, secret: text, events: text[], active: bool, created_at: timestamptz }`
- **AuditLog**: `{ id: UUID, actor_id: UUID, action: text, payload: jsonb, ip_address: inet, created_at: timestamptz }`
- **ModelRun** (new): `{ id: UUID, job_id: UUID, model_name: text, latency_ms: int, token_usage: jsonb, prompt_hash: text, created_at: timestamptz }`

**Indexes & Constraints:**
- Partial index on `analysis_jobs (status)` for queued lookups.
- Unique constraint on `(user_id, target_url)` for webhook subscriptions.
- TimescaleDB or pg_partman partitioning for `audit_logs` and `model_runs` by month.
- Foreign keys with cascading soft deletes via `archived_at` flag.

## Integration Points
- **OpenAI**: `chat.completions`, `responses`, `embeddings`, `audio.transcriptions`; called via service account with per-request tracing, prompt hashing, deterministic temperature settings, and retry logic.
- **Redis**: Primary queue (Celery) and caching layer for auth sessions, rate limiting, and job status snapshots; configure persistence (AOF) and TLS in transit.
- **PostgreSQL**: Transactional store for users, submissions, jobs, insights, audits; use SQLAlchemy migrations (Alembic) and logical replication to downstream warehouse.
- **Vector Store (Phase 2)**: pgvector or Qdrant for storing embeddings that support comparative analysis and explanations.
- **Object Storage**: S3-compatible bucket for uploaded media, extracted frames, transcripts; enforce lifecycle policies and virus scanning pipeline.
- **External Social APIs**: YouTube Data API, TikTok Insights, Instagram Graph, X API; fetch engagement baselines, trending tags; add backoff and caching to respect quotas.
- **Analytics Warehouse (Phase 2)**: Replicate PostgreSQL via Debezium/Fivetran into BigQuery/Snowflake for cohort analysis and LTV modeling.
- **Trust & Safety**: Integrate with OpenAI Moderation plus optional Hive/ActiveFence for disallowed content checks before inference.

**Integration Matrix:**

| Integration | Authentication | Data Direction | Notes |
|-------------|----------------|----------------|-------|
| OpenAI | API key (env var) + optional Azure AD managed identity | Outbound | Circuit breaker + exponential backoff; redact PII before sending |
| Redis | TLS mutual auth | Bi-directional | Separate logical DBs for queue vs cache; telemetry via Redis exporter |
| PostgreSQL | IAM role or service user + password in secret manager | Bi-directional | Connection pooling via PgBouncer |
| Object Storage | S3 access key / IAM role | Outbound | Signed URLs for client uploads; antivirus lambda |
| External Social APIs | OAuth2 / App tokens | Outbound | Store tokens encrypted (KMS), refresh job |
| Analytics Warehouse | Service account JSON | Outbound | Batch replication nightly; CDC for enterprise tier |
| Trust & Safety APIs | API key | Outbound | Fail closed when moderation unavailable |

## Sequencing & Rollout Plan
1. **Backend Foundation (Weeks 1-2)**
   - [Milestone BF-1] Set up FastAPI skeleton, project scaffolding, auth plumbing, and request validation.
   - [Milestone BF-2] Provision PostgreSQL, Redis, object storage; create IaC templates and health checks.
   - [Milestone BF-3] Deliver `/api/v1/analyze` enqueue plus polling with mocked inference; acceptance test: job transitions `queued -> processing -> complete` within SLA.

2. **AI Pipeline (Weeks 3-5)**
   - [Milestone AI-1] Implement media ingestion workers, transcription, feature extraction pipelines with golden dataset regression tests.
   - [Milestone AI-2] Integrate OpenAI and baseline CV/NLP models; capture latency and token metrics; define fallback paths.
   - [Milestone AI-3] Add insight generation, scoring calibration, webhook callbacks; acceptance test: P95 latency < 45s, accuracy above baseline.

3. **Frontend & Mobile (Weeks 4-6)**
   - [Milestone FE-1] Build React dashboard for submissions, status, and history with SSE updates.
   - [Milestone FE-2] Implement React Native client for on-the-go submissions and notifications; integrate deep links.
   - [Milestone FE-3] Harden auth flows, rate limiting, observability dashboards; acceptance test: Lighthouse score > 80, error budget policy defined.

4. **Scale & Integrations (Weeks 6+)**
   - [Milestone SI-1] Connect external social APIs, enrich analytics, ensure quota monitoring and caching.
   - [Milestone SI-2] Stand up analytics warehouse, scheduled model retraining, model registry with approval workflow.
   - [Milestone SI-3] Perform load testing, security review (penetration test, threat modeling), and prepare go-to-market launch with incident response runbook.

### Security & Compliance Considerations
- Enforce least-privilege IAM roles across services; rotate secrets via secret manager (e.g., AWS Secrets Manager).
- Use customer-managed encryption keys for PostgreSQL, Redis, and object storage; enable TLS 1.2+ everywhere.
- Implement structured logging with redaction of PII; align with SOC2 controls and GDPR data retention policies.
- Maintain audit trails for all admin actions and model configuration changes (ModelRun plus AuditLog tables).
- Run vulnerability scans (Snyk/Trivy) and dependency review on every PR; integrate with CI gates.

### Testing Strategy
- **Unit Tests:** Pydantic schema validation, Celery task logic, prompt builders.
- **Integration Tests:** FastAPI endpoints hitting ephemeral PostgreSQL/Redis using docker-compose; mocked external APIs.
- **Load Tests:** k6/gatling scenarios for `/api/v1/analyze` workloads; ensure queue depth < threshold.
- **Monitoring Tests:** Synthetic probes verifying inference endpoints, webhook delivery, SSE stream health.
