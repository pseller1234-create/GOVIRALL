# main.py — ViralNOW API (Render-ready, clean)
from __future__ import annotations
import os, json, re
from typing import Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from emotion_factor import EmotionFactorRequest, calculator

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


@app.post("/api/emotion-factor")
async def emotion_factor(request: EmotionFactorRequest, _auth = Depends(require_bearer)):
    try:
        result = calculator.score(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return JSONResponse(result)
