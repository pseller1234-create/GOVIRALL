"""Emotion Factor scoring engine.

This module implements the Emotion Factor (EF) algorithm described in the
project specification.  It fuses per-window modality features into an emotion
curve, derives secondary metrics, and returns an overall EF score together
with qualitative insights.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from pydantic import BaseModel, Field, model_validator


WINDOW_SECONDS = 0.5


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _zscore(series: Sequence[float]) -> List[float]:
    if not series:
        return []
    mean = statistics.fmean(series)
    stdev = statistics.pstdev(series)
    if stdev == 0:
        return [0.0 for _ in series]
    return [(value - mean) / stdev for value in series]


def _dtw_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    n, m = len(a), len(b)
    dtw = [[math.inf] * (m + 1) for _ in range(n + 1)]
    dtw[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(a[i - 1] - b[j - 1])
            dtw[i][j] = cost + min(dtw[i - 1][j], dtw[i][j - 1], dtw[i - 1][j - 1])
    distance = dtw[n][m] / (n + m)
    return 1.0 / (1.0 + distance)


def _normalized_corr(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    mean_a = statistics.fmean(a)
    mean_b = statistics.fmean(b)
    var_a = statistics.pvariance(a)
    var_b = statistics.pvariance(b)
    if var_a == 0 or var_b == 0:
        return 0.0
    cov = sum((ai - mean_a) * (bi - mean_b) for ai, bi in zip(a, b)) / len(a)
    return max(-1.0, min(1.0, cov / math.sqrt(var_a * var_b)))


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


class Timeline(BaseModel):
    audio: List[float]
    prosody: List[float]
    lexical: List[float]
    visual: List[float]
    contextual: Optional[List[float]] = None
    music_energy: Optional[List[float]] = None
    edit_cadence: Optional[List[float]] = None
    beat_onsets: Optional[List[float]] = None
    cut_markers: Optional[List[float]] = None
    emphasis_hits: Optional[List[float]] = None

    @model_validator(mode="after")
    def validate_lengths(self) -> "Timeline":
        required = [self.audio, self.prosody, self.lexical, self.visual]
        base_len = {len(seq) for seq in required}
        if len(base_len) != 1:
            raise ValueError("Audio, prosody, lexical, and visual series must align")
        target_len = base_len.pop()
        optional = [
            self.contextual,
            self.music_energy,
            self.edit_cadence,
            self.beat_onsets,
            self.cut_markers,
            self.emphasis_hits,
        ]
        for seq in optional:
            if seq is not None and len(seq) != target_len:
                raise ValueError("Optional series must match primary series length")
        return self


class EmotionFactorRequest(BaseModel):
    platform: str = Field(default="tiktok")
    niche: Optional[str] = None
    timeline: Timeline
    weights: Optional[Dict[str, float]] = None
    alpha: Optional[Dict[str, float]] = None
    beta0: Optional[float] = None


@dataclass
class EmotionMetrics:
    peak: float
    rise_time: float
    volatility: float
    coherence: float
    payoff: float
    beat_sync: float
    prosody_hits: float
    emotion_switch_quality: float
    coh_guard: float


DEFAULT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "tiktok": {"audio": 0.28, "prosody": 0.22, "lexical": 0.18, "visual": 0.22, "contextual": 0.10},
    "shorts": {"audio": 0.25, "prosody": 0.20, "lexical": 0.20, "visual": 0.25, "contextual": 0.10},
    "reels": {"audio": 0.27, "prosody": 0.20, "lexical": 0.18, "visual": 0.25, "contextual": 0.10},
}

DEFAULT_ALPHA: Dict[str, Dict[str, float]] = {
    "tiktok": {
        "peak": 1.6,
        "rise_time": 1.2,
        "volatility": 0.9,
        "coherence": 1.0,
        "payoff": 1.3,
        "beat_sync": 0.9,
        "prosody_hits": 0.7,
        "emotion_switch": 0.8,
    },
    "shorts": {
        "peak": 1.5,
        "rise_time": 1.3,
        "volatility": 0.8,
        "coherence": 1.1,
        "payoff": 1.2,
        "beat_sync": 0.8,
        "prosody_hits": 0.6,
        "emotion_switch": 0.7,
    },
    "reels": {
        "peak": 1.4,
        "rise_time": 1.2,
        "volatility": 0.9,
        "coherence": 1.0,
        "payoff": 1.4,
        "beat_sync": 0.7,
        "prosody_hits": 0.6,
        "emotion_switch": 0.8,
    },
}

DEFAULT_BETA0: Dict[str, float] = {
    "tiktok": -3.8,
    "shorts": -3.6,
    "reels": -3.7,
}


class EmotionFactorCalculator:
    def __init__(self) -> None:
        self.weight_profiles = DEFAULT_WEIGHTS
        self.alpha_profiles = DEFAULT_ALPHA
        self.beta0_profiles = DEFAULT_BETA0

    def _resolve_weights(self, request: EmotionFactorRequest) -> Dict[str, float]:
        if request.weights:
            return request.weights
        return self.weight_profiles.get(request.platform.lower(), self.weight_profiles["tiktok"])

    def _resolve_alpha(self, request: EmotionFactorRequest) -> Dict[str, float]:
        if request.alpha:
            return request.alpha
        return self.alpha_profiles.get(request.platform.lower(), self.alpha_profiles["tiktok"])

    def _resolve_beta0(self, request: EmotionFactorRequest) -> float:
        if request.beta0 is not None:
            return request.beta0
        return self.beta0_profiles.get(request.platform.lower(), self.beta0_profiles["tiktok"])

    def _fuse_modalities(self, timeline: Timeline, weights: Dict[str, float]) -> List[float]:
        contextual = timeline.contextual or [0.0] * len(timeline.audio)
        weighted = []
        audio = _zscore(timeline.audio)
        prosody = _zscore(timeline.prosody)
        lexical = _zscore(timeline.lexical)
        visual = _zscore(timeline.visual)
        contextual_z = _zscore(contextual)
        for idx in range(len(audio)):
            value = (
                weights.get("audio", 0.0) * audio[idx]
                + weights.get("prosody", 0.0) * prosody[idx]
                + weights.get("lexical", 0.0) * lexical[idx]
                + weights.get("visual", 0.0) * visual[idx]
                + weights.get("contextual", 0.0) * contextual_z[idx]
            )
            weighted.append(value)
        return weighted

    def _compute_metrics(self, curve: Sequence[float], timeline: Timeline) -> EmotionMetrics:
        if not curve:
            raise ValueError("Curve cannot be empty")
        peak = max(curve)
        threshold = 0.8 * peak if peak > 0 else 0.0
        rise_index = next((i for i, value in enumerate(curve) if value >= threshold), len(curve) - 1)
        rise_time = rise_index * WINDOW_SECONDS
        post_hook_start = int(3 / WINDOW_SECONDS)
        tail = curve[post_hook_start:] if post_hook_start < len(curve) else curve[-1:]
        volatility = statistics.pstdev(tail) if len(tail) > 1 else 0.0
        coherence = 0.0
        if timeline.music_energy and timeline.edit_cadence:
            coherence = _dtw_similarity(timeline.music_energy, timeline.edit_cadence)
        payoff_baseline_index = min(len(curve) - 1, int(3 / WINDOW_SECONDS))
        payoff = curve[-1] - curve[payoff_baseline_index]
        beat_sync = 0.0
        if timeline.beat_onsets:
            beat_sync = _normalized_corr(curve, timeline.beat_onsets)
        prosody_hits = 0.0
        if timeline.emphasis_hits and timeline.cut_markers:
            aligned = sum(
                hit for hit, cut in zip(timeline.emphasis_hits, timeline.cut_markers) if cut > 0
            )
            total_cuts = sum(1 for cut in timeline.cut_markers if cut > 0)
            if total_cuts:
                prosody_hits = _clip(aligned / (total_cuts + 1e-6))
        diffs = [curve[i + 1] - curve[i] for i in range(len(curve) - 1)]
        if diffs:
            sign_changes = sum(
                1
                for prev, curr in zip(diffs, diffs[1:])
                if prev * curr < 0 and abs(prev) > 0.05 and abs(curr) > 0.05
            )
            density = sign_changes / max(1, len(diffs) - 1)
            # Ideal switch density around 0.2 with soft tolerance.
            emotion_switch_quality = math.exp(-((density - 0.2) ** 2) / (2 * 0.12 ** 2))
        else:
            emotion_switch_quality = 0.0
        coh_guard = 0.25 + 0.75 * coherence
        return EmotionMetrics(
            peak=peak,
            rise_time=rise_time,
            volatility=volatility,
            coherence=coherence,
            payoff=payoff,
            beat_sync=beat_sync,
            prosody_hits=prosody_hits,
            emotion_switch_quality=_clip(emotion_switch_quality),
            coh_guard=coh_guard,
        )

    def _score(self, metrics: EmotionMetrics, alpha: Dict[str, float], beta0: float) -> float:
        inv_rise = 1.0 / (metrics.rise_time + 1e-6)
        raw = (
            alpha.get("peak", 0.0) * metrics.peak
            + alpha.get("rise_time", 0.0) * inv_rise
            + alpha.get("volatility", 0.0) * metrics.volatility * metrics.coh_guard
            + alpha.get("coherence", 0.0) * metrics.coherence
            + alpha.get("payoff", 0.0) * metrics.payoff
            + alpha.get("beat_sync", 0.0) * metrics.beat_sync
            + alpha.get("prosody_hits", 0.0) * metrics.prosody_hits
            + alpha.get("emotion_switch", 0.0) * metrics.emotion_switch_quality
        )
        return 100.0 * _sigmoid(beta0 + raw)

    def _confidence(self, metrics: EmotionMetrics, timeline: Timeline) -> float:
        coverage = 1.0
        optional_series = [
            timeline.contextual,
            timeline.music_energy,
            timeline.edit_cadence,
            timeline.beat_onsets,
            timeline.cut_markers,
            timeline.emphasis_hits,
        ]
        missing = sum(1 for seq in optional_series if not seq)
        coverage -= 0.05 * missing
        coherence_term = 0.5 * metrics.coherence
        volatility_term = 0.2 * _clip(metrics.volatility / 1.5)
        payoff_term = 0.3 * _clip((metrics.payoff + abs(metrics.payoff)) / (2.0 + abs(metrics.peak)))
        confidence = _clip(0.5 * coverage + coherence_term + volatility_term + payoff_term, 0.0, 0.99)
        return round(confidence, 2)

    def _insights(self, metrics: EmotionMetrics) -> Dict[str, List[str]]:
        why_it_works: List[str] = []
        what_to_fix: List[str] = []
        prescriptions: List[str] = []

        if metrics.rise_time <= 2.5:
            why_it_works.append(f"fast rise to peak in {metrics.rise_time:.1f}s")
        if metrics.beat_sync > 0.35:
            why_it_works.append("beat-synced cuts")
        if metrics.prosody_hits > 0.45:
            why_it_works.append("prosody emphasis aligned to edits")
        if metrics.payoff > 0.2:
            why_it_works.append("strong payoff energy")

        if metrics.payoff < 0:
            what_to_fix.append("ending energy trails off")
            prescriptions.append("Add stinger or CTA to lift final seconds")
        if metrics.prosody_hits < 0.3:
            what_to_fix.append("prosody monotone around key edits")
            prescriptions.append("Coach talent to add emphasis on scene changes")
        if metrics.beat_sync < 0.2:
            what_to_fix.append("cuts drift from beat grid")
            prescriptions.append("Tighten edit cadence to quarter-beat timing")
        if metrics.rise_time > 4.0:
            what_to_fix.append("slow hook ramp")
            prescriptions.append("Condense intro to spike energy sooner")
        if metrics.volatility > 1.5 and metrics.coherence < 0.4:
            what_to_fix.append("energy feels chaotic")
            prescriptions.append("Smooth transitions or add motif to unify sections")

        if not why_it_works:
            why_it_works.append("solid baseline energy distribution")
        if not prescriptions:
            prescriptions.append("Maintain current pacing while layering payoff CTA")

        return {
            "why_it_works": why_it_works[:3],
            "what_to_fix": what_to_fix[:3],
            "prescriptions": prescriptions[:3],
        }

    def score(self, request: EmotionFactorRequest) -> Dict[str, object]:
        weights = self._resolve_weights(request)
        alpha = self._resolve_alpha(request)
        beta0 = self._resolve_beta0(request)

        curve = self._fuse_modalities(request.timeline, weights)
        metrics = self._compute_metrics(curve, request.timeline)
        ef_score = round(self._score(metrics, alpha, beta0))
        confidence = self._confidence(metrics, request.timeline)
        insights = self._insights(metrics)

        curve_export = [round(value, 4) for value in curve]

        return {
            "emotion_factor": int(_clip(ef_score, 0, 100)),
            "confidence": confidence,
            "curve": curve_export,
            "metrics": {
                "peak": round(metrics.peak, 3),
                "rise_time": round(metrics.rise_time, 2),
                "volatility": round(metrics.volatility, 3),
                "coherence": round(metrics.coherence, 3),
                "payoff": round(metrics.payoff, 3),
                "beat_sync": round(metrics.beat_sync, 3),
                "prosody_hits": round(metrics.prosody_hits, 3),
                "emotion_switch_quality": round(metrics.emotion_switch_quality, 3),
            },
            "why_it_works": insights["why_it_works"],
            "what_to_fix": insights["what_to_fix"],
            "prescriptions": insights["prescriptions"],
        }


calculator = EmotionFactorCalculator()

