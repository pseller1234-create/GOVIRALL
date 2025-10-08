"""Feature engineering heuristics for ViralNOW scoring."""
from __future__ import annotations

import math
from typing import Dict

from app.domain.schemas import ContentPayload


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def derive_feature_vector(payload: ContentPayload) -> Dict[str, float]:
    """Construct a normalized feature vector from the payload."""

    features: Dict[str, float] = {}
    features["hook_strength"] = _score_hook(payload)
    features["pacing"] = _score_pacing(payload)
    features["clarity"] = _score_clarity(payload)
    features["emotional_pull"] = _score_emotion(payload)
    features["novelty"] = _score_novelty(payload)
    features["social_proof"] = _score_social_proof(payload)
    features["optimization_maturity"] = _score_optimization(payload)
    features["brand_safety"] = _score_brand_safety(payload)
    return features


def _score_hook(payload: ContentPayload) -> float:
    creative = payload.creative
    transcript = (payload.transcript or "").lower()
    hook_seconds = creative.hook_seconds or 3.0
    opener = transcript[:140]
    has_question = "?" in opener
    urgency = any(word in opener for word in ("now", "today", "secret", "stop"))
    pacing_modifier = 0.1 if creative.pacing_label == "slow" else 0.0
    base = 1.0 - _clamp(hook_seconds / 8.0)
    adjustments = 0.1 if has_question else 0.0
    adjustments += 0.1 if urgency else 0.0
    adjustments -= pacing_modifier
    return _clamp(base + adjustments)


def _score_pacing(payload: ContentPayload) -> float:
    creative = payload.creative
    if creative.avg_scene_length_seconds is None:
        return 0.6
    scale = _clamp(1.5 / (creative.avg_scene_length_seconds + 0.5))
    if creative.pacing_label == "fast":
        scale += 0.1
    elif creative.pacing_label == "slow":
        scale -= 0.2
    return _clamp(scale)


def _score_clarity(payload: ContentPayload) -> float:
    transcript = payload.transcript or payload.description or ""
    word_count = len(transcript.split())
    if word_count == 0:
        return 0.5
    if word_count < 60:
        base = 0.8
    elif word_count < 200:
        base = 0.7
    else:
        base = 0.55
    if payload.creative.captions_present:
        base += 0.1
    if payload.creative.narration_present:
        base += 0.05
    return _clamp(base)


def _score_emotion(payload: ContentPayload) -> float:
    tone = payload.creative.emotional_tone or "medium"
    mapping = {"high": 0.9, "medium": 0.7, "low": 0.45}
    return mapping.get(tone, 0.6)


def _score_novelty(payload: ContentPayload) -> float:
    title = (payload.title or "").lower()
    transcript = (payload.transcript or "").lower()
    keywords = set(word.strip("#") for word in payload.hashtags)
    contrarian = any(phrase in transcript for phrase in ("nobody told you", "against the rules"))
    data_point = "data" in transcript or any(word in transcript for word in ("study", "report"))
    base = 0.55
    if contrarian:
        base += 0.2
    if data_point:
        base += 0.1
    if "2024" in title or transcript:
        base += 0.05
    if len(keywords) >= 4:
        base += 0.05
    return _clamp(base)


def _score_social_proof(payload: ContentPayload) -> float:
    if not payload.audience_pulse:
        return 0.55
    lifts = [pulse.lift for pulse in payload.audience_pulse]
    avg_lift = sum(lifts) / len(lifts)
    log_lift = math.log1p(avg_lift)
    return _clamp(0.45 + log_lift / 3)


def _score_optimization(payload: ContentPayload) -> float:
    optimization = payload.optimization
    score = 0.4
    if optimization.call_to_action and optimization.call_to_action != "none":
        score += 0.15
    if optimization.has_thumbnail_variant:
        score += 0.1
    if optimization.crosspost_targets:
        score += 0.1
    if optimization.posting_window:
        score += 0.1
    return _clamp(score)


def _score_brand_safety(payload: ContentPayload) -> float:
    flags = payload.creative.brand_safety_flags or 0
    if flags == 0:
        return 0.9
    if flags == 1:
        return 0.7
    if flags == 2:
        return 0.5
    return 0.3
