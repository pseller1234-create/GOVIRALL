from importlib import util
from pathlib import Path

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
    response = client.post("/api/analyze", json={"media": {}})
    assert response.status_code == 401


def test_analyze_returns_mock_payload_when_authorized(monkeypatch):
    response = client.post(
        "/api/analyze",
        headers={"Authorization": "Bearer test-token"},
        json={"media": {"type": "video"}},
    )
    assert response.status_code == 200
    assert response.json() == main._mock_response()
