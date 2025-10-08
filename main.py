# main.py — ViralNOW API (Render-ready, clean)
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Literal, Optional
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, HttpUrl, model_validator

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


class TextAmplifyRequest(BaseModel):
    """Payload contract for duplicating text exactly four times."""

    text: str = Field(..., min_length=1, max_length=4000)
    separator: str = Field(
        default=" ",
        min_length=0,
        max_length=8,
        description="Glue applied between repeated snippets.",
    )

    @property
    def normalized_text(self) -> str:
        """Collapse internal whitespace for deterministic responses."""

        return " ".join(self.text.split())


class TextAmplifyResponse(BaseModel):
    """Response returned by the four-times text amplifier."""

    text: str
    items: list[str]
    count: int


def _amplify_text(payload: TextAmplifyRequest) -> TextAmplifyResponse:
    """Repeat text four times while preserving deterministic ordering."""

    normalized = payload.normalized_text
    items = [normalized] * 4
    joined = payload.separator.join(items)
    return TextAmplifyResponse(text=joined, items=items, count=len(items))


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


class AnalyzeRequest(BaseModel):
    """Request payload contract for `/api/v1/analyze`."""

    content_type: Literal["video", "post", "text"]
    source_url: HttpUrl | None = Field(default=None, description="Public source URL")
    upload_id: UUID | None = Field(default=None, description="Identifier for uploaded media")
    caption: str | None = Field(default=None, max_length=4000)
    platform_hint: Literal["tiktok", "youtube", "instagram", "x"] | None = None
    user_id: UUID
    notify_webhook: HttpUrl | None = Field(
        default=None,
        description="Callback URL invoked when the analysis is complete.",
    )

    @model_validator(mode="after")
    def ensure_submission_context(self) -> AnalyzeRequest:
        if not (self.source_url or self.upload_id or self.caption):
            raise ValueError(
                "At least one of source_url, upload_id, or caption must be provided."
            )
        return self


class AnalyzeResponse(BaseModel):
    """Response contract for queued analysis jobs."""

    job_id: UUID
    status: Literal["queued", "processing", "complete", "failed"]
    estimated_completion_sec: int = Field(ge=0, le=86_400)

# ---- Health & Home ----
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def home():
    return {"status": "ok", "docs": "/docs", "health": "/health"}

def _safe_json_parse(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.S)
        if not m:
            raise
        return json.loads(m.group(0))

@app.post(
    "/api/v1/analyze",
    response_model=AnalyzeResponse,
    status_code=201,
)
async def analyze(
    payload: AnalyzeRequest,
    _auth: Dict[str, Any] = Depends(require_bearer),
) -> AnalyzeResponse:
    """Queue an analysis job and return its tracking metadata."""

    estimated_completion = 75 if payload.content_type == "video" else 45
    return AnalyzeResponse(
        job_id=uuid4(),
        status="queued",
        estimated_completion_sec=estimated_completion,
    )


@app.post("/api/text-amplify", response_model=TextAmplifyResponse)
async def text_amplify(
    payload: TextAmplifyRequest,
    _auth: Dict[str, Any] = Depends(require_bearer),
) -> TextAmplifyResponse:
    """Return the provided text repeated four times per product requirement."""

    return _amplify_text(payload)
