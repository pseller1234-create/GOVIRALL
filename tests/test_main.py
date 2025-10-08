from pathlib import Path
import sys
from typing import Dict

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def _auth_headers(token: str = "demo") -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["docs"] == "/docs"
    assert payload["health"] == "/health"


def test_analyze_requires_authorization():
    response = client.post("/api/analyze", json={})
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or bad token"


def test_analyze_returns_mock_payload(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main, "USE_OPENAI", False, raising=False)
    response = client.post("/api/analyze", json={"media": {}}, headers=_auth_headers())
    assert response.status_code == 200
    payload = response.json()
    assert payload["viral_score"] == 84
    assert payload["confidence"] == "92%"
    assert payload["platform_ranking"]["TikTok"] == 90
    assert payload["hook_variations_tagged"][0]["pattern"] == "contrarian"


def test_safe_json_parse_extracts_embedded_json():
    noisy_content = "Some prefix {\"viral_score\": 75, \"confidence\": \"80%\"} trailing"
    parsed = main._safe_json_parse(noisy_content)
    assert parsed == {"viral_score": 75, "confidence": "80%"}

