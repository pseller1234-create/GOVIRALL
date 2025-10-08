"""Reusable dependencies for FastAPI routes."""
from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dataclasses import asdict

from app.core.config import get_settings


_security = HTTPBearer(auto_error=False)


def require_bearer(creds: HTTPAuthorizationCredentials = Depends(_security)) -> dict:
    settings = get_settings()
    if not creds or creds.scheme.lower() != "bearer" or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing or invalid bearer token")
    # In production we would verify JWT. For now return a deterministic principal.
    return {"user": {"sub": "demo-user", "tier": "free"}, "settings": asdict(settings)}
