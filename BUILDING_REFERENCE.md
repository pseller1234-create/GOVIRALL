# ViralNow Platform Building Reference

## Vision & Product Pillars
- **Mission**: Deliver actionable pre-launch intelligence that predicts whether a creative asset will go viral.
- **Primary Users**: Creators, growth teams, agencies, and educators who need rapid iteration loops.
- **Value Props**: Early viral score, explainable insights, optimization playbooks, and longitudinal creator coaching.

## Stage Blueprint
| Stage | Key Responsibilities | Example Services |
| --- | --- | --- |
| Acquisition | Capture uploads, URLs, or text scripts from web/mobile clients. | Ingestion API, file storage, webhook listeners |
| Onboarding | Validate asset metadata, detect platform, collect audience targets. | FastAPI validation layer, user-preferences service |
| Upload-to-Score | Run asynchronous preprocessing and scoring pipelines. | Media transcoder, feature extractor, scoring orchestrator |
| Analysis Engines | Apply CV/NLP/audio models to derive features. | Whisper, CLIP, sentiment & pacing analyzers |
| Viral Score | Fuse features into 0–100 score with confidence. | Ensemble scorer, calibration store |
| Share Wizard | Generate shareable cards, exports, and embeds. | Report generator, templating engine |
| Recommendations | Suggest hooks, hashtags, posting windows. | Prompt templates, retrieval-augmented generator |
| Infrastructure | Observability, autoscaling, job queueing, secrets management. | Redis, Postgres, OpenTelemetry, Vault |
| Admin / Moderation | Policy enforcement, abuse detection, audit logs. | Admin portal, rules engine |
| Academy / Pro Tier | Premium curriculum, labs, leaderboard. | Learning service, gamification engine |
| Security | Authentication, token issuance, permissions. | JWT auth, API key registry |

## Service Topology
```
clients (web, mobile, partner API)
  │
  ├─► FastAPI edge (auth, validation, routing)
  │     ├─► Media ingestion worker (uploads, normalization)
  │     ├─► Scoring orchestrator (Celery/RQ)
  │     │     ├─► Feature extractors (CV, NLP, audio)
  │     │     ├─► Trend radar retriever (niche comps)
  │     │     └─► Scoring ensemble (weights + calibration)
  │     └─► Insights generator (LLM prompts + heuristics)
  └─► Creator dashboard API (history, leaderboards)
```

## Data Contracts
- **Analyze Request** (`POST /api/analyze`)
  ```json
  {
    "media": {
      "type": "video|text|link",
      "url": "https://...",
      "language": "en",
      "duration_seconds": 32.4
    },
    "platform_focus": "tiktok|youtube|instagram|x",
    "audience": {
      "persona": "creator|brand|agency",
      "niche": "marketing/ai"
    }
  }
  ```
- **Analyze Response**
  ```json
  {
    "viral_score": 0-100,
    "confidence": "0-100%",
    "why_it_will_hit": "<=40 words",
    "why_it_wont_hit": "<=40 words",
    "improvement_suggestions": ["..."],
    "hook_variations": ["..."],
    "hook_variations_tagged": [{"pattern": "...", "text": "..."}],
    "recommended_hashtags": ["#..."],
    "best_post_times": ["..."],
    "platform_ranking": {"TikTok": 90, "YouTube": 82},
    "next_actions": ["..."]
  }
  ```

## Build Targets & Roadmap
1. **MVP Hardening**
   - Implement background task queue for scoring.
   - Add persistent storage for analyses (Postgres + SQLModel).
   - Wire OpenAI + vision/audio models with feature fallback path.
2. **Creator Dashboard**
   - Build React dashboard with history, score trendlines, insights diffing.
   - Add auth tiers (free, pro) with rate limits and feature gating.
3. **Trend Radar & Academy**
   - Integrate external APIs for trending benchmarks.
   - Author curriculum modules and gamified challenges.
4. **Observability & Ops**
   - Add tracing, metrics, alerting.
   - Security hardening (CSP, rate limiting, audit logging).

## Deployment Reference
- **Runtime**: FastAPI + Uvicorn on Render.
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**:
  - `OPENAI_API_KEY` – optional; enables real completions.
  - `OPENAI_MODEL` – override model name (default `gpt-4o-mini`).
  - `JWT_SECRET` – required for secure auth in production.
- **Scaling Notes**:
  - Enable Render background workers for heavy media processing.
  - Use object storage (S3-compatible) for raw uploads.
  - Cache hot trend data in Redis with TTL.

## Testing & Quality Gates
- `pytest` for unit/integration coverage of scoring logic.
- `ruff` / `black` for lint and style.
- `mypy` for type safety.
- `bandit` + `pip-audit` for security and dependency hygiene.

## Future Considerations
- Multi-language support via translation layer.
- Partner API with usage-based billing.
- Experiment tracking for model iterations.
- Privacy guardrails for user-generated content.

