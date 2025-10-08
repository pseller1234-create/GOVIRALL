"""FastAPI entrypoint for ViralNOW creator OS."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analyze import router as analyze_router
from app.core.config import get_settings


settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "environment": settings.environment}


@app.get("/")
def home() -> dict:
    return {"status": "ok", "docs": "/docs", "health": "/health"}


app.include_router(analyze_router)
