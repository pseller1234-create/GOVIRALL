# System Design Overview

## High-Level Architecture
```mermaid
graph LR
    subgraph Clients
        W[Web Client]
        M[Mobile Client]
    end
    subgraph Backend
        APIGW[FastAPI Service]
        AUTH[Auth Service]
        AI[AI Inference Worker]
        QUEUE[Task Queue (Redis)]
    end
    subgraph DataStores
        PG[(PostgreSQL)]
        OBJ[(Object Storage)]
    end
    subgraph ExternalIntegrations
        OPENAI[(OpenAI API)]
        SOCIAL[(External Social APIs)]
    end

    W -->|HTTPS/REST| APIGW
    M -->|HTTPS/REST| APIGW
    APIGW --> AUTH
    AUTH --> APIGW
    APIGW -->|Persist Metadata| PG
    APIGW -->|Enqueue Job| QUEUE
    QUEUE --> AI
    AI -->|Fetch Prompt & Artifacts| PG
    AI -->|Inference| OPENAI
    AI -->|Store Outputs| OBJ
    AI -->|Update Status| PG
    APIGW -->|Retrieve Result| PG
    APIGW -->|Publish| SOCIAL
```

## Request Flow Summary
1. Client (web or mobile) sends an authenticated request to FastAPI (for example `/api/analyze`).
2. FastAPI validates the session via the auth service and persists request metadata in PostgreSQL.
3. FastAPI enqueues a background job in Redis for AI inference.
4. The AI worker dequeues the job, assembles prompt/context from PostgreSQL and object storage, then
   calls the OpenAI API.
5. The worker stores generated outputs (structured data, media) in PostgreSQL and object storage,
   updates job status, and emits optional notifications.
6. Client polls or receives webhook/push with completion data. FastAPI can optionally syndicate
   results to external social APIs.

## API Surface
- **POST `/api/auth/login`**
  - **Auth**: None.
  - **Request**: `{ "email": string, "password": string }`.
  - **Response**: `{ "access_token": string, "refresh_token": string, "expires_in": number }`.
  - **Notes**: Delegates to auth service; tokens are JWTs signed by Auth.
- **POST `/api/auth/refresh`**
  - **Auth**: Refresh token.
  - **Request**: `{ "refresh_token": string }`.
  - **Response**: `{ "access_token": string, "expires_in": number }`.
  - **Notes**: Access tokens are short-lived; refresh rotates secrets.
- **POST `/api/analyze`**
  - **Auth**: Bearer token.
  - **Request**:
    - `source_urls`: string[]
    - `analysis_type`: "misinformation" | "sentiment"
    - `options`?: object
  - **Response**:
    `{ "job_id": string, "status": "queued" }`.
  - **Notes**: Persists request, enqueues job.
- **GET `/api/analyze/{job_id}`**
  - **Auth**: Bearer token.
  - **Response**:
    ```json
    {
      "job_id": "string",
      "status": "queued" | "processing" | "completed" | "failed",
      "result"?: AnalysisResult
    }
    ```
  - **Notes**: Polling endpoint; surfaces errors.
- **GET `/api/insights/feed`**
  - **Auth**: Bearer token.
  - **Response**: `{ "items": InsightSummary[], "next_cursor"?: string }`.
  - **Notes**: Fetches curated analysis summaries.
- **POST `/api/webhooks/social`**
  - **Auth**: HMAC header.
  - **Request**: Provider payload.
  - **Response**: `200 OK`.
  - **Notes**: Receives callbacks from social APIs; validates HMAC signature.

### AnalysisResult Schema
```json
{
  "summary": "string",
  "confidence": 0.0,
  "themes": ["string"],
  "sources": [
    {
      "url": "string",
      "verdict": "true" | "false" | "mixed",
      "evidence": "string"
    }
  ],
  "generated_at": "ISO8601 timestamp"
}
```

### InsightSummary Schema
```json
{
  "id": "string",
  "title": "string",
  "highlights": ["string"],
  "published_at": "ISO8601 timestamp"
}
```

## Core Data Models
- **User**
  - `id`: UUID
  - `email`: string
  - `hashed_password`: string
  - `role`: "analyst" | "admin"
  - `created_at`: timestamp
  - `last_login_at`: timestamp
- **Session**
  - `id`: UUID
  - `user_id`: UUID
  - `refresh_token_hash`: string
  - `expires_at`: timestamp
  - `created_at`: timestamp
- **AnalysisJob**
  - `id`: UUID
  - `user_id`: UUID
  - `status`: "queued" | "processing" | "completed" | "failed"
  - `analysis_type`: string
  - `payload`: JSONB
  - `created_at`: timestamp
  - `started_at`?: timestamp
  - `completed_at`?: timestamp
  - `error`?: JSONB
- **AnalysisResult**
  - `job_id`: UUID
  - `summary`: text
  - `confidence`: numeric
  - `themes`: text[]
  - `sources`: JSONB
  - `generated_at`: timestamp
- **Insight**
  - `id`: UUID
  - `job_id`: UUID
  - `title`: text
  - `highlights`: text[]
  - `published_at`: timestamp
  - `distribution_targets`: JSONB
- **AuditEvent**
  - `id`: UUID
  - `actor_id`: UUID
  - `action`: string
  - `metadata`: JSONB
  - `created_at`: timestamp

## Integration Contracts
- **Auth Service**
  - Endpoint: `/verify`
  - Response: `{ "sub": UUID, "roles": string[] }`
  - Notes: FastAPI caches validation results and rotates JWT signing keys.
- **OpenAI API**
  - Endpoint: `POST https://api.openai.com/v1/responses`
  - Model: `gpt-4.1-mini`
  - Notes: Worker assembles prompts from persisted payloads.
    Expects streamed completions and retries with exponential backoff on `429` or `5xx` responses.
- **Redis (Task Queue)**
  - Stream: `analysis_jobs`
  - Enqueued payload: `{ job_id, user_id, analysis_type, payload }`
  - Notes: Workers acknowledge via `analysis_jobs:processed`.
    Monitoring consumes latency metrics from stream lengths.
- **PostgreSQL**
  - Role: Primary metadata store with transactional writes.
  - Notes: Row-level security enforces per-user access and CDC feeds downstream analytics.
- **Object Storage**
  - Role: S3-compatible bucket for large artifacts referenced by URL in PostgreSQL.
  - Notes: Objects versioned with lifecycle policies for retention.
- **External Social APIs**
  - Role: Optional publishing and webhook ingestion.
  - Notes: Provider SDK integrations require encrypted OAuth tokens.
    Per-provider shared secrets enforce webhook validation.

## Sequencing & Rollout Plan
1. **Phase 1 – Backend Foundations**
   - Stand up PostgreSQL schema, auth integration, and FastAPI skeleton with `/api/auth/*`
     and `/api/analyze` (queue stubbed).
   - Implement CI with linting, testing, and security scans.
     Add observability (structured logging, metrics).
2. **Phase 2 – AI Pipeline**
   - Provision Redis queue and AI worker service.
     Integrate OpenAI API with prompt templates and retry policy.
   - Add object storage support for artifacts. Define `AnalysisResult` persistence.
     Expose job polling endpoint.
3. **Phase 3 – Frontend & Integrations**
   - Build web/mobile clients for submission and insights feed. Implement push/polling UX.
   - Integrate social APIs for optional content distribution.
     Harden webhook security and rate limiting.
4. **Phase 4 – Hardening & Scale**
   - Add autoscaling, multi-region failover, and compliance guardrails
     (audit logging, PII redaction).
   - Conduct load tests, chaos drills, and finalize rollout checklist for GA.
