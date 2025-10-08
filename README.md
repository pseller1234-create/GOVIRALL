# ViralNOW API

ViralNOW is a multimodal creator operating system that predicts, explains, and improves the virality and ROI of any creative asset before it ships. The FastAPI service in this repository exposes the core scoring engine that powers actionable intelligence for shorts, long-form video, carousels, thumbnails, audio, scripts, and newsletters.

## Features

- **Unified Analysis Endpoint** – Submit cross-format creative payloads and receive a 360° viral intelligence report with strengths, risks, suggested experiments, hook variants, and scheduling guidance.
- **Multi-Platform Scorecard** – Weighted platform rankings incorporate format fit, heuristic biases, and audience signals so growth teams know where to launch first.
- **Actionable Recommendations** – Deterministic heuristics synthesize creative signals, optimization toggles, and benchmark lifts into next steps that can be automated in creator workflows.
- **Render Ready** – Ships with health endpoints, bearer auth dependency, and CORS configuration for deployment on Render or any container platform.

## Getting Started

```bash
./scripts/setup.sh  # provisions .venv and installs dependencies (requires network access)
source .venv/bin/activate
uvicorn main:app --reload
```

The analyze endpoint expects a JSON payload that matches `ContentPayload` in [`app/domain/schemas.py`](app/domain/schemas.py). Example request:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Authorization: Bearer demo" \
  -H "Content-Type: application/json" \
  -d '{
        "format": "short_form_video",
        "primary_platform": "tiktok",
        "target_platforms": ["tiktok", "youtube", "instagram"],
        "title": "This hook saved our launch",
        "transcript": "Nobody told you the 3-rule launch. Now fix your funnel.",
        "hashtags": ["growth", "launch"],
        "creative": {
          "hook_seconds": 2.4,
          "avg_scene_length_seconds": 1.1,
          "captions_present": true,
          "narration_present": true,
          "pacing_label": "fast",
          "emotional_tone": "high"
        },
        "optimization": {
          "call_to_action": "on_screen",
          "has_thumbnail_variant": true,
          "crosspost_targets": ["youtube"],
          "posting_window": ["Tuesday 8:00 PM"]
        },
        "audience_pulse": [
          {"metric": "views", "value": 45000, "benchmark": 23000},
          {"metric": "watch_time", "value": 62, "benchmark": 48}
        ]
      }'
```

## Testing

```bash
pytest
```

## Deployment

- Build an image using the provided `render.yaml` or your infrastructure pipeline.
- Configure environment variables (e.g., `VIRALNOW_APP_NAME`, `VIRALNOW_ENVIRONMENT`, `VIRALNOW_JWT_SECRET`).
- Frontload authentication in the calling service; upgrade the `require_bearer` dependency once JWT issuer is available.

Refer to [`BUILDING_REFERENCE.md`](BUILDING_REFERENCE.md) for system design notes and roadmap context.
