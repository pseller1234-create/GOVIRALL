from __future__ import annotations

import asyncio
import pathlib
import sys

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import app


def test_pipeline_endpoint_runs_all_lanes() -> None:
    payload = {
        "creator_id": "cr_123",
        "asset_reference": "vid_456",
    }
    async def _run() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/pipeline",
                json=payload,
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        lane_names = {lane["lane"] for lane in data["lanes"]}
        assert lane_names == {"backend", "dashboard", "model_training", "academy"}

    asyncio.run(_run())


def test_pipeline_endpoint_honors_lane_filter() -> None:
    payload = {
        "creator_id": "cr_789",
        "asset_reference": "vid_101112",
        "lanes": ["backend", "model_training"],
    }
    async def _run() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/pipeline",
                json=payload,
                headers={"Authorization": "Bearer test-token"},
            )
        assert response.status_code == 200
        data = response.json()
        lane_names = {lane["lane"] for lane in data["lanes"]}
        assert lane_names == {"backend", "model_training"}

    asyncio.run(_run())
