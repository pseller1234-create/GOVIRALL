"""Viral scoring orchestration for ViralNOW."""
from __future__ import annotations

from typing import Dict, List

from app.domain.schemas import (
    AnalyzeResponse,
    ContentPayload,
    HookVariation,
    ImprovementIdea,
    Platform,
    PlatformScore,
    ViralReport,
)
from app.services.feature_engineering import derive_feature_vector


_FEATURE_WEIGHTS: Dict[str, float] = {
    "hook_strength": 0.22,
    "pacing": 0.12,
    "clarity": 0.14,
    "emotional_pull": 0.12,
    "novelty": 0.14,
    "social_proof": 0.12,
    "optimization_maturity": 0.08,
    "brand_safety": 0.06,
}

_PLATFORM_BIASES: Dict[Platform, float] = {
    "tiktok": 1.05,
    "youtube": 1.0,
    "instagram": 0.97,
    "x": 0.92,
    "linkedin": 0.9,
    "newsletter": 0.88,
}


def _weighted_score(features: Dict[str, float]) -> float:
    total = 0.0
    for key, weight in _FEATURE_WEIGHTS.items():
        total += features.get(key, 0.0) * weight
    return total * 100


def _confidence_from_variance(features: Dict[str, float]) -> float:
    values = list(features.values())
    if not values:
        return 0.5
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    confidence = 0.8 - variance
    return max(0.35, min(0.95, confidence))


def _platform_scores(payload: ContentPayload, base_score: float) -> List[PlatformScore]:
    ranking: List[PlatformScore] = []
    for platform in payload.target_platforms:
        bias = _PLATFORM_BIASES.get(platform, 0.9)
        rationale = _platform_rationale(platform, bias, payload.format)
        ranking.append(
            PlatformScore(platform=platform, score=max(0.0, min(100.0, base_score * bias)), rationale=rationale)
        )
    ranking.sort(key=lambda item: item.score, reverse=True)
    return ranking


def _platform_rationale(platform: Platform, bias: float, content_format: str) -> str:
    if platform == "tiktok":
        return "Short-form friendly feed rewards swift hooks." if bias >= 1 else "Needs sharper hook for TikTok pace."
    if platform == "youtube":
        if content_format == "long_form_video":
            return "Session depth favors longer narratives."
        return "YT Shorts requires retention beyond first swipe."
    if platform == "instagram":
        return "Reels trending audio alignment is key." if bias >= 1 else "Add visual punch-ins for IG Reels."
    if platform == "x":
        return "Threads convert with contrarian framing." if bias >= 1 else "Lean into hot-take pacing for X."
    if platform == "linkedin":
        return "Professional proof points resonate on LinkedIn."
    if platform == "newsletter":
        return "Repurpose into story-driven newsletter issue."
    return "Optimize delivery for the platform algorithm."


def _derive_strengths(features: Dict[str, float]) -> List[str]:
    strengths = []
    if features.get("hook_strength", 0) > 0.75:
        strengths.append("Opens strong within first 3 seconds.")
    if features.get("emotional_pull", 0) > 0.8:
        strengths.append("High emotional charge keeps attention.")
    if features.get("clarity", 0) > 0.75:
        strengths.append("Messaging is concise and digestible.")
    if features.get("social_proof", 0) > 0.7:
        strengths.append("Early engagement outperforms baseline.")
    if not strengths:
        strengths.append("Solid baseline; prime for optimization tests.")
    return strengths


def _derive_risks(features: Dict[str, float]) -> List[str]:
    risks: List[str] = []
    if features.get("pacing", 1.0) < 0.55:
        risks.append("Pacing drags; tighten beats under 1.8s.")
    if features.get("novelty", 1.0) < 0.55:
        risks.append("Message blends with category noise; add contrarian proof.")
    if features.get("brand_safety", 1.0) < 0.6:
        risks.append("Potential brand safety friction detected.")
    if features.get("optimization_maturity", 1.0) < 0.5:
        risks.append("Optimize CTA, posting window, and thumbnail variants.")
    if not risks:
        risks.append("Monitor retention at 3s / 15s post-launch.")
    return risks


def _suggestions(payload: ContentPayload, features: Dict[str, float]) -> List[ImprovementIdea]:
    suggestions: List[ImprovementIdea] = []
    if features.get("pacing", 1.0) < 0.6:
        suggestions.append(
            ImprovementIdea(
                title="Tighten Opening Beat",
                description="Trim 1.5s from intro and add kinetic text hits to accelerate swipe retention.",
                impact="high",
                effort="medium",
            )
        )
    if features.get("optimization_maturity", 1.0) < 0.6:
        suggestions.append(
            ImprovementIdea(
                title="Layer CTA",
                description="Add on-screen CTA at 0:04 and mirror in caption to reinforce action.",
                impact="medium",
                effort="low",
            )
        )
    if features.get("novelty", 1.0) < 0.65:
        suggestions.append(
            ImprovementIdea(
                title="Inject Contrarian Proof",
                description="Open with metric-driven contrast (e.g., 'This beat 92% of creators in 7 days').",
                impact="high",
                effort="medium",
            )
        )
    if payload.creative.brand_safety_flags:
        suggestions.append(
            ImprovementIdea(
                title="Review Brand Safety",
                description="Audit flagged frames and consider alternative visuals to avoid ad-suitability hits.",
                impact="medium",
                effort="medium",
            )
        )
    if not suggestions:
        suggestions.append(
            ImprovementIdea(
                title="Launch Iteration Sprint",
                description="Ship 3 hook variants in 48 hours to pressure-test platform resonance.",
                impact="medium",
                effort="medium",
            )
        )
    return suggestions


def _hook_variations(payload: ContentPayload, features: Dict[str, float]) -> List[HookVariation]:
    base_topic = payload.title or payload.niche or "this idea"
    return [
        HookVariation(pattern="contrarian", text=f"Everyone's doing {base_topic} wrong—here's proof."),
        HookVariation(pattern="countdown", text=f"Give me 7 seconds to 5x your {base_topic}."),
        HookVariation(pattern="question", text=f"What if your next {base_topic} landed 10x shares?"),
        HookVariation(pattern="proof", text=f"We hit 68% retention with this {base_topic}."),
        HookVariation(pattern="tease", text=f"Stay for the 0:07 switch-up that spikes saves."),
    ][:5]


def _recommended_hashtags(payload: ContentPayload) -> List[str]:
    base = payload.hashtags or []
    niche = (payload.niche or payload.primary_platform).replace(" ", "")
    augmented = list(dict.fromkeys(base + [f"#{niche}Growth", "#ViralNOW", "#CreatorOps"]))
    return augmented[:6]


def _best_post_times(payload: ContentPayload) -> List[str]:
    platform = payload.primary_platform
    if platform in ("tiktok", "instagram"):
        return ["Tuesday 8:00 PM", "Saturday 11:30 AM"]
    if platform == "youtube":
        return ["Thursday 5:00 PM", "Sunday 10:00 AM"]
    if platform == "x":
        return ["Monday 7:30 AM", "Wednesday 9:00 PM"]
    return ["Wednesday 7:00 AM", "Friday 1:00 PM"]


def _next_actions(payload: ContentPayload, features: Dict[str, float]) -> List[str]:
    actions: List[str] = ["Lock hook + CTA script", "Stage retention watch party 1h post-drop"]
    if features.get("optimization_maturity", 1.0) < 0.6:
        actions.append("Spin up thumbnail multivariate test")
    if payload.optimization.crosspost_targets:
        actions.append("Schedule cross-posts via automation queue")
    actions.append("Publish scorecard to growth workspace")
    return actions


def generate_report(payload: ContentPayload) -> AnalyzeResponse:
    features = derive_feature_vector(payload)
    viral_score = round(_weighted_score(features), 2)
    confidence = round(_confidence_from_variance(features), 2)
    platform_scores = _platform_scores(payload, viral_score)
    report = ViralReport(
        viral_score=viral_score,
        confidence=confidence,
        strengths=_derive_strengths(features),
        risks=_derive_risks(features),
        improvement_suggestions=_suggestions(payload, features),
        hook_variations=_hook_variations(payload, features),
        recommended_hashtags=_recommended_hashtags(payload),
        best_post_times=_best_post_times(payload),
        platform_ranking=platform_scores,
        next_actions=_next_actions(payload, features),
        feature_breakdown=features,
    )
    return AnalyzeResponse(data=report)
