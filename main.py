# main.py — minimal FastAPI app for Render root layout
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import json
import os

app = FastAPI(title="ViralNOW API (Root Layout)")

@app.get("/health")
def health():
    return {"ok": True}

# very light JWT check (dev-only)
def get_user_from_auth(authorization: Optional[str]):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or bad token")
    return {"user_id": "demo-user", "tier": "free"}

@app.post("/api/analyze")
async def analyze(payload: dict, authorization: Optional[str] = Header(None)):
    _ = get_user_from_auth(authorization)

    # If you have a real key set, you could call OpenAI here.
    # To keep it dead-simple, we return a realistic mock.
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
