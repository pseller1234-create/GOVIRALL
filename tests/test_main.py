"""Tests for FastAPI app behaviors and helper utilities."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

main = importlib.import_module("main")


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provide a FastAPI test client bound to the application."""
    return TestClient(main.app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_home_endpoint(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["docs"] == "/docs"
    assert payload["health"] == "/health"


def test_analyze_mock_response_structure(client: TestClient) -> None:
    headers = {"Authorization": "Bearer demo-token"}
    response = client.post("/api/analyze", headers=headers, json={"media": {}})
    assert response.status_code == 200
    body: Dict[str, Any] = response.json()
    expected_keys = {
        "viral_score",
        "confidence",
        "why_it_will_hit",
        "why_it_wont_hit",
        "improvement_suggestions",
        "hook_variations",
        "hook_variations_tagged",
        "recommended_hashtags",
        "best_post_times",
        "platform_ranking",
        "next_actions",
    }
    assert set(body) == expected_keys
    assert isinstance(body["improvement_suggestions"], list)
    assert all(isinstance(item, str) for item in body["improvement_suggestions"])


def test_safe_json_parse_allows_strict_json() -> None:
    payload = {"example": "value"}
    result = main._safe_json_parse(json.dumps(payload))
    assert result == payload


def test_safe_json_parse_falls_back_to_object_fragment() -> None:
    fragment = "Some prefix text {\"foo\": 1, \"bar\": 2} trailing garbage"
    result = main._safe_json_parse(fragment)
    assert result == {"foo": 1, "bar": 2}
