# main.py — ViralNOW API (Render-ready, clean)
from __future__ import annotations
import os, json, re
from typing import Optional, Dict, Any, Iterable, Tuple
from math import sqrt

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(title="ViralNOW API")

# CORS (open for now; tighten to your domain later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Auth: adds Swagger "Authorize" button ----
security = HTTPBearer(auto_error=False)
JWT_SECRET = os.getenv("JWT_SECRET", "change_me_to_a_long_random_string")

def require_bearer(creds: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    if not creds or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing or bad token")
    # (Optional strict JWT verify)
    # from jose import jwt, JWTError
    # try:
    #     payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    # except JWTError:
    #     raise HTTPException(status_code=401, detail="Invalid token")
    return {"user": {"sub": "demo-user", "tier": "free"}}

# ---- Health & Home ----
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def home():
    return {"status": "ok", "docs": "/docs", "health": "/health"}

# ---- OpenAI (real) or mock fallback ----
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
if USE_OPENAI:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = (
    "You are ViralNOW, an elite viral-intelligence engine. "
    "Return STRICT JSON with keys: viral_score, confidence, why_it_will_hit, "
    "why_it_wont_hit, improvement_suggestions, hook_variations, "
    "hook_variations_tagged, recommended_hashtags, best_post_times, "
    "platform_ranking, next_actions. "
    "For hooks, include A/B tagging objects like "
    '{"pattern":"contrarian","text":"..."} . '
    "Keep summary ≤ 28 words; rationales ≤ 40 words; grade 6–8 readability."
)

def _safe_json_parse(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if not m:
            raise
        return json.loads(m.group(0))

def _mock_response() -> Dict[str, Any]:
    return {
        "viral_score": 84,
        "confidence": "92%",
        "why_it_will_hit": "Strong first 2s hook, clean captions, beat-matched jump cuts.",
        "why_it_wont_hit": "Tiny dip around 0:06; CTA only in caption.",
        "improvement_suggestions": [
            "Trim 1.0–1.5s from intro",
            "Add on-screen CTA at 0:04",
            "End with a share/save prompt",
        ],
        "hook_variations": [
            "I did the opposite—and it worked.",
            "This myth kills your views.",
            "Give me 7 seconds.",
        ],
        "hook_variations_tagged": [
            {"pattern": "contrarian", "text": "I did the opposite—and it worked."},
            {"pattern": "myth_bust", "text": "This myth kills your views."},
            {"pattern": "countdown", "text": "Give me 7 seconds."},
        ],
        "recommended_hashtags": ["#MindsetFuel", "#ViralNOW", "#AIHustle", "#Motivation", "#CreatorTips", "#Shorts"],
        "best_post_times": ["8:00 PM CST", "11:00 AM CST"],
        "platform_ranking": {"TikTok": 90, "YouTube": 82, "Instagram": 78, "X": 66},
        "next_actions": ["Export tighter intro", "Schedule 8 PM CST", "Share score card on profile"],
    }

@app.post("/api/analyze")
async def analyze(payload: dict, _auth = Depends(require_bearer)):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Bad JSON")

    if not USE_OPENAI:
        return JSONResponse(_mock_response())

    # Real OpenAI path
    user_envelope = {
        "instruction": "Return STRICT JSON per contract; no code fences.",
        "media": payload.get("media", {}),
        "platform_focus": payload.get("platform_focus", "tiktok"),
        "controls": {
            "readability_grade": "6-8",
            "summary_max_words": 28,
            "rationale_max_words": 40,
            "ab_tagging_for_hooks": True,
        },
    }

    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0.6,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_envelope)},
        ],
    )
    content = completion.choices[0].message.content or "{}"
    try:
        data = _safe_json_parse(content)
    except Exception:
        data = _mock_response()
        data["why_it_wont_hit"] = "Model returned non-JSON; served robust fallback."
    return JSONResponse(data)


def _pearson_correlation(a: Iterable[float], b: Iterable[float]) -> Optional[float]:
    a_list = [float(x) for x in a]
    b_list = [float(x) for x in b]
    if len(a_list) != len(b_list) or len(a_list) < 2:
        return None
    mean_a = sum(a_list) / len(a_list)
    mean_b = sum(b_list) / len(b_list)
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a_list, b_list))
    var_a = sum((x - mean_a) ** 2 for x in a_list)
    var_b = sum((y - mean_b) ** 2 for y in b_list)
    denom = sqrt(var_a) * sqrt(var_b)
    if denom == 0:
        return None
    return cov / denom


def _average(values: Iterable[Optional[float]]) -> Optional[float]:
    filtered = [v for v in values if isinstance(v, (int, float))]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)


def _compute_metric_correlations(predicted: Dict[str, Iterable[float]], actual: Dict[str, Iterable[float]]) -> Tuple[Dict[str, Optional[float]], Optional[float]]:
    correlations: Dict[str, Optional[float]] = {}
    for metric, predicted_series in predicted.items():
        actual_series = actual.get(metric)
        if actual_series is None:
            correlations[metric] = None
            continue
        correlations[metric] = _pearson_correlation(predicted_series, actual_series)
    overall = _average(correlations.values())
    if overall is not None:
        correlations["overall"] = overall
    return correlations, overall


def _validate_payload_section(section: Any, expected_type: type, name: str) -> Any:
    if section is None:
        raise HTTPException(status_code=400, detail=f"Missing {name} section")
    if not isinstance(section, expected_type):
        raise HTTPException(status_code=400, detail=f"{name} must be a {expected_type.__name__}")
    return section


@app.post("/api/validate")
async def validate_predictions(payload: dict, _auth = Depends(require_bearer)):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Bad JSON")

    predicted = _validate_payload_section(payload.get("predicted"), dict, "predicted")
    actual = _validate_payload_section(payload.get("actual"), dict, "actual")

    predicted_core = {
        key: value
        for key, value in predicted.items()
        if key in {"views", "likes", "comments"} and isinstance(value, list)
    }
    if not predicted_core:
        raise HTTPException(status_code=400, detail="predicted must include lists for views/likes/comments")

    public_api = _validate_payload_section(actual.get("public_api"), dict, "actual.public_api")
    trend_benchmarks = _validate_payload_section(actual.get("trend_benchmarks"), dict, "actual.trend_benchmarks")

    platform_scores = predicted.get("platform_scores", {})
    if platform_scores and not isinstance(platform_scores, dict):
        raise HTTPException(status_code=400, detail="platform_scores must be an object of lists")
    actual_platforms = actual.get("platform_specific", {})
    if actual_platforms and not isinstance(actual_platforms, dict):
        raise HTTPException(status_code=400, detail="actual.platform_specific must be an object")

    correlations = {}
    overall_scores = []

    public_corr, public_overall = _compute_metric_correlations(predicted_core, public_api)
    correlations["public_api"] = public_corr
    if public_overall is not None:
        overall_scores.append(public_overall)

    trend_corr, trend_overall = _compute_metric_correlations(predicted_core, trend_benchmarks)
    correlations["trend_benchmarks"] = trend_corr
    if trend_overall is not None:
        overall_scores.append(trend_overall)

    platform_corr = {}
    for platform, predicted_series in platform_scores.items():
        actual_series = None
        if isinstance(predicted_series, list):
            actual_series = actual_platforms.get(platform)
        if not isinstance(predicted_series, list) or not isinstance(actual_series, list):
            platform_corr[platform] = None
            continue
        platform_corr[platform] = _pearson_correlation(predicted_series, actual_series)
    platform_overall = _average(platform_corr.values())
    if platform_corr:
        if platform_overall is not None:
            platform_corr["overall"] = platform_overall
            overall_scores.append(platform_overall)
        correlations["platform_specific"] = platform_corr

    overall = _average(overall_scores)
    threshold = float(payload.get("threshold", 0.85))
    window_hours = int(payload.get("window_hours", 72))

    response = {
        "window_hours": window_hours,
        "threshold": threshold,
        "overall_correlation": overall,
        "correlations": correlations,
        "meets_threshold": overall is not None and overall >= threshold,
        "notes": "Correlations computed against public APIs, trend benchmarks, and platform models."
    }

    if overall is None:
        response["meets_threshold"] = False
        response["notes"] = "Insufficient data to evaluate correlation across sources."

    return JSONResponse(response)
