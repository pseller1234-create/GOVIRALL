"""Pydantic schemas describing ViralNOW inputs and outputs."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


Platform = Literal["tiktok", "youtube", "instagram", "x", "linkedin", "newsletter"]
ContentFormat = Literal[
    "short_form_video",
    "long_form_video",
    "carousel",
    "thumbnail",
    "audio",
    "script",
    "newsletter",
]


class AudiencePulse(BaseModel):
    """Quantifies recent engagement relative to past performance."""

    metric: Literal["views", "likes", "comments", "shares", "watch_time", "retention"]
    value: float = Field(..., ge=0)
    benchmark: float = Field(
        ..., ge=0, description="Historical or industry benchmark for normalization."
    )

    @property
    def lift(self) -> float:
        if self.benchmark == 0:
            return 1.0 if self.value > 0 else 0.0
        return self.value / self.benchmark


class CreativeSignals(BaseModel):
    """Normalized descriptors of creative decisions."""

    hook_seconds: Optional[float] = Field(None, ge=0, le=15)
    avg_scene_length_seconds: Optional[float] = Field(None, ge=0, le=15)
    captions_present: Optional[bool] = None
    narration_present: Optional[bool] = None
    text_density: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Ratio of frames containing text overlays.",
    )
    pacing_label: Optional[Literal["slow", "balanced", "fast"]] = None
    emotional_tone: Optional[Literal["high", "medium", "low"]] = None
    brand_safety_flags: Optional[int] = Field(
        None,
        ge=0,
        description="Count of potential brand safety risks detected by heuristics.",
    )


class OptimizationControls(BaseModel):
    """Pre-publish optimization knobs toggled by the creator."""

    posting_window: Optional[List[str]] = None
    call_to_action: Optional[Literal["verbal", "on_screen", "caption", "none"]] = None
    has_thumbnail_variant: Optional[bool] = None
    crosspost_targets: Optional[List[Platform]] = None


class ContentPayload(BaseModel):
    """Primary payload accepted by the ViralNOW analyze endpoint."""

    format: ContentFormat
    primary_platform: Platform
    target_platforms: List[Platform] = Field(default_factory=list)
    title: Optional[str] = Field(None, max_length=140)
    description: Optional[str] = Field(None, max_length=1000)
    transcript: Optional[str] = Field(None, max_length=16000)
    audio_summary: Optional[str] = Field(None, max_length=4000)
    niche: Optional[str] = Field(None, max_length=80)
    hashtags: List[str] = Field(default_factory=list)
    publish_time_hint: Optional[datetime] = None
    creative: CreativeSignals = Field(default_factory=CreativeSignals)
    optimization: OptimizationControls = Field(default_factory=OptimizationControls)
    audience_pulse: List[AudiencePulse] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def ensure_platforms(cls, data: Dict[str, object]) -> Dict[str, object]:
        primary = data.get("primary_platform")
        targets = list(dict.fromkeys(data.get("target_platforms") or []))
        if primary and primary not in targets:
            targets.insert(0, primary)
        data["target_platforms"] = targets
        return data

    @field_validator("hashtags", mode="before")
    @classmethod
    def normalize_hashtags(cls, value: List[str]) -> List[str]:
        if value is None:
            return []
        normalized: List[str] = []
        for item in value:
            text = item.strip().lower()
            normalized.append(text if text.startswith("#") else f"#{text}")
        return normalized


class PlatformScore(BaseModel):
    """Scoring detail for a single platform."""

    platform: Platform
    score: float = Field(..., ge=0, le=100)
    rationale: str = Field(..., max_length=180)


class ImprovementIdea(BaseModel):
    """Concrete improvement experiment suggestion."""

    title: str = Field(..., max_length=60)
    description: str = Field(..., max_length=220)
    impact: Literal["low", "medium", "high"]
    effort: Literal["low", "medium", "high"]


class HookVariation(BaseModel):
    """Alternative hook copy ready for testing."""

    pattern: Literal["contrarian", "countdown", "question", "proof", "tease"]
    text: str = Field(..., max_length=120)


class ViralReport(BaseModel):
    """Primary response contract returned to clients."""

    viral_score: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    strengths: List[str]
    risks: List[str]
    improvement_suggestions: List[ImprovementIdea]
    hook_variations: List[HookVariation]
    recommended_hashtags: List[str]
    best_post_times: List[str]
    platform_ranking: List[PlatformScore]
    next_actions: List[str]
    feature_breakdown: Dict[str, float]


class AnalyzeResponse(BaseModel):
    """Wrapper API response that mirrors the legacy envelope."""

    data: ViralReport
