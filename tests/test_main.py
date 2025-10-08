from importlib import util
from pathlib import Path

from uuid import uuid4

from fastapi.testclient import TestClient


_ROOT = Path(__file__).resolve().parents[1]
_MAIN_PATH = _ROOT / "main.py"
_SPEC = util.spec_from_file_location("main", _MAIN_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - defensive guard
    raise RuntimeError("Unable to load main module for tests")
main = util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(main)  # type: ignore[assignment]


client = TestClient(main.app)


def test_safe_json_parse_handles_embedded_json():
    noisy_payload = "Noise before {\"value\": 42} trailing"
    parsed = main._safe_json_parse(noisy_payload)
    assert parsed == {"value": 42}


def test_health_endpoint_reports_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_analyze_requires_bearer_token():
    response = client.post(
        "/api/v1/analyze",
        json={
            "content_type": "video",
            "user_id": str(uuid4()),
            "source_url": "https://example.com/video.mp4",
        },
    )
    assert response.status_code == 401


def test_analyze_rejects_missing_submission_context():
    response = client.post(
        "/api/v1/analyze",
        headers={"Authorization": "Bearer token"},
        json={
            "content_type": "video",
            "user_id": str(uuid4()),
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("At least one" in err["msg"] for err in detail)


def test_analyze_rejects_invalid_content_type():
    response = client.post(
        "/api/v1/analyze",
        headers={"Authorization": "Bearer token"},
        json={
            "content_type": "audio",
            "caption": "Test caption",
            "user_id": str(uuid4()),
        },
    )
    assert response.status_code == 422


def test_analyze_returns_queued_job_metadata():
    response = client.post(
        "/api/v1/analyze",
        headers={"Authorization": "Bearer test-token"},
        json={
            "content_type": "video",
            "user_id": str(uuid4()),
            "source_url": "https://example.com/clip.mp4",
            "platform_hint": "tiktok",
            "notify_webhook": "https://example.com/hook",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "queued"
    assert isinstance(payload["estimated_completion_sec"], int)
    assert payload["estimated_completion_sec"] >= 0
