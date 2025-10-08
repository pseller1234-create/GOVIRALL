"""Integration tests for ViralNOW analyze endpoint."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import app  # noqa: E402


client = TestClient(app)


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}


def test_analyze_returns_scorecard() -> None:
    response = client.post(
        "/api/analyze",
        json={
            "format": "short_form_video",
            "primary_platform": "tiktok",
            "target_platforms": ["tiktok", "youtube", "instagram"],
            "title": "This hook saved our launch",
            "description": "We broke down the launch playbook.",
            "transcript": "Nobody told you the 3-rule launch. Now fix your funnel.",
            "hashtags": ["growth", "launch"],
            "creative": {
                "hook_seconds": 2.5,
                "avg_scene_length_seconds": 1.2,
                "captions_present": True,
                "narration_present": True,
                "pacing_label": "fast",
                "emotional_tone": "high",
            },
            "optimization": {
                "call_to_action": "on_screen",
                "has_thumbnail_variant": True,
                "crosspost_targets": ["youtube"],
                "posting_window": ["Tuesday 8:00 PM"],
            },
            "audience_pulse": [
                {"metric": "views", "value": 45000, "benchmark": 23000},
                {"metric": "watch_time", "value": 62, "benchmark": 48},
            ],
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert 0 <= payload["viral_score"] <= 100
    assert payload["confidence"] > 0
    assert len(payload["strengths"]) >= 1
    assert any(score["platform"] == "tiktok" for score in payload["platform_ranking"])


def test_requires_bearer_token() -> None:
    response = client.post(
        "/api/analyze",
        json={
            "format": "short_form_video",
            "primary_platform": "tiktok",
        },
    )
    assert response.status_code == 401
