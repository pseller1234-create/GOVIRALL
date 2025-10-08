"""FastAPI routes exposing the ViralNOW analysis pipeline."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_bearer
from app.domain.schemas import AnalyzeResponse, ContentPayload
from app.services.score_engine import generate_report

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(payload: ContentPayload, _principal: dict = Depends(require_bearer)) -> AnalyzeResponse:
    """Analyze multi-format creative and return actionable report."""

    return generate_report(payload)
