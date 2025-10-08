"""Tests for the text amplification endpoint."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import app


client = TestClient(app)


def test_text_amplify_repeats_four_times() -> None:
    response = client.post(
        "/api/text-amplify",
        json={"text": "Boost   reach now"},
        headers={"Authorization": "Bearer token"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 4
    assert payload["items"] == ["Boost reach now"] * 4
    assert payload["text"] == "Boost reach now Boost reach now Boost reach now Boost reach now"


def test_text_amplify_honors_custom_separator() -> None:
    response = client.post(
        "/api/text-amplify",
        json={"text": "Focus", "separator": "|"},
        headers={"Authorization": "Bearer secure"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["text"] == "Focus|Focus|Focus|Focus"
    assert payload["items"] == ["Focus"] * 4
