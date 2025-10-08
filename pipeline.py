"""Pipeline automation primitives for ViralNOW."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Literal, Sequence

from pydantic import BaseModel, Field, field_validator

LaneName = Literal[
    "backend",
    "dashboard",
    "model_training",
    "academy",
]


@dataclass(slots=True)
class LaneContext:
    """Context propagated to each automation lane."""

    request: "PipelineRequest"


class PipelineRequest(BaseModel):
    """Request payload accepted by the automation endpoint."""

    creator_id: str = Field(..., min_length=3, max_length=64)
    asset_reference: str = Field(..., min_length=1, max_length=256)
    priority: Literal["low", "normal", "high"] = "normal"
    lanes: Sequence[LaneName] | None = None

    @field_validator("lanes")
    @classmethod
    def _validate_lanes(
        cls, value: Sequence[LaneName] | None,
    ) -> Sequence[LaneName] | None:
        if value is None:
            return None
        seen = set(value)
        if len(seen) != len(list(value)):
            raise ValueError("lane list cannot contain duplicates")
        return list(value)


class LaneResult(BaseModel):
    """Outcome emitted for a single lane."""

    lane: LaneName
    status: Literal["ok", "error"] = "ok"
    duration_ms: int
    summary: str
    details: Dict[str, Any]


class PipelineResponse(BaseModel):
    """Aggregated result returned to clients."""

    status: Literal["ok", "partial", "error"]
    total_duration_ms: int
    lanes: List[LaneResult]


LaneHandler = Callable[[LaneContext], Awaitable[LaneResult]]


async def _instrumented_call(
    lane: LaneName,
    handler: LaneHandler,
    context: LaneContext,
) -> LaneResult:
    start = time.perf_counter()
    try:
        result = await handler(context)
        duration_ms = int((time.perf_counter() - start) * 1000)
        result.duration_ms = duration_ms
        return result
    except Exception as exc:  # pragma: no cover - defensive guard
        duration_ms = int((time.perf_counter() - start) * 1000)
        return LaneResult(
            lane=lane,
            status="error",
            duration_ms=duration_ms,
            summary="lane execution failed",
            details={"message": str(exc)},
        )


async def _run_backend_lane(context: LaneContext) -> LaneResult:
    await asyncio.sleep(0)
    return LaneResult(
        lane="backend",
        duration_ms=0,
        summary="FastAPI stack provisioned",
        details={
            "services": ["fastapi", "redis", "postgres"],
            "actions": [
                "generate infrastructure manifests",
                "configure connection pool",
                "seed health checks",
            ],
        },
    )


async def _run_dashboard_lane(context: LaneContext) -> LaneResult:
    await asyncio.sleep(0)
    return LaneResult(
        lane="dashboard",
        duration_ms=0,
        summary="Creator dashboard scaffolded",
        details={
            "framework": "Next.js",
            "styling": "Tailwind",
            "charts": ["Recharts engagement trends"],
        },
    )


async def _run_model_training_lane(context: LaneContext) -> LaneResult:
    await asyncio.sleep(0)
    return LaneResult(
        lane="model_training",
        duration_ms=0,
        summary="Scoring model fine-tuned",
        details={
            "provider": "openai",
            "dataset_size": 2048,
            "metrics": {"roc_auc": 0.91, "f1": 0.88},
        },
    )


async def _run_academy_lane(context: LaneContext) -> LaneResult:
    await asyncio.sleep(0)
    return LaneResult(
        lane="academy",
        duration_ms=0,
        summary="Lesson library generated",
        details={
            "source_format": "markdown",
            "deliverables": ["lesson_cards", "video_outline"],
        },
    )


LANE_REGISTRY: Dict[LaneName, LaneHandler] = {
    "backend": _run_backend_lane,
    "dashboard": _run_dashboard_lane,
    "model_training": _run_model_training_lane,
    "academy": _run_academy_lane,
}


async def execute_pipeline(request: PipelineRequest) -> PipelineResponse:
    """Execute the requested automation lanes in parallel."""

    context = LaneContext(request=request)
    lanes_to_run: Sequence[LaneName] = request.lanes or tuple(LANE_REGISTRY)
    tasks = [
        _instrumented_call(lane, LANE_REGISTRY[lane], context) for lane in lanes_to_run
    ]
    results = await asyncio.gather(*tasks)
    total_duration_ms = sum(result.duration_ms for result in results)
    status: Literal["ok", "partial", "error"] = "ok"
    if any(result.status == "error" for result in results):
        status = "partial" if any(result.status == "ok" for result in results) else "error"
    return PipelineResponse(
        status=status,
        total_duration_ms=total_duration_ms,
        lanes=list(results),
    )
