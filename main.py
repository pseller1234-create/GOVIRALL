# main.py — ViralNOW API (with Swagger "Authorize" button)
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

app = FastAPI(title="ViralNOW API (Root Layout)")

# --- Security (adds the Authorize button) ---
security = HTTPBearer(auto_error=False)

def require_bearer(creds: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not creds or not creds.scheme.lower() == "bearer" or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing or bad token")
    # TODO: verify JWT if you want (using your JWT_SECRET)
    return {"user_id": "demo-user", "tier": "free"}

# --- Routes ---
@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/analyze")
async def analyze(payload: dict, _user = Depends(require_bearer)):
    # mock response; swap for real OpenAI when ready
    return JSONResponse({
        "ok": True,
        "viral_score": 82,
        "confidence": "91%",
        "summary": "Tight hook and clean pacing; clear payoff.",
        "why_it_will_hit": "Immediate tension, readable captions, beat-matched edits.",
        "why_it_wont_hit": "Minor lull at 0:06; CTA only in caption.",
        "improvement_suggestions": [
            "Trim 1.0–1.5s from intro",
            "Add on-screen CTA at 0:04",
            "Punch-in on payoff line"
        ],
        "improvement_suggestions_tagged": [
            {"text":"Trim 1.0–1.5s from intro","maps_to":"retention_0_3s"},
            {"text":"Add on-screen CTA at 0:04","maps_to":"avd"}
        ],
        "hook_variations": [
            "I did the opposite—and it worked.",
            "This myth kills your views.",
            "Give me 7 seconds."
        ],
        "hook_variations_tagged": [
            {"pattern":"contrarian","text":"I did the opposite—and it worked."},
            {"pattern":"myth_bust","text":"This myth kills your views."},
            {"pattern":"countdown","text":"Give me 7 seconds."}
        ],
        "recommended_hashtags": ["#MindsetFuel","#ViralNOW","#AIHustle","#Motivation","#CreatorTips","#Shorts"],
        "best_post_times": ["8:00 PM CST","11:00 AM CST"],
        "platform_ranking": {"TikTok":90,"YouTube":82,"Instagram":78,"X":66},
        "comparables": [{"title":"From 0 to 1 with AI","why_similar":"confession hook","delta":"+faster cuts"}],
        "next_actions": ["Export tighter intro","Schedule 8 PM CST","Share score card on profile"],
        "pro_features_used": [],
        "compliance_notes_applied": []
    })
