"""Application configuration utilities for ViralNOW."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    app_name: str = "ViralNOW API"
    environment: Literal["local", "staging", "production"] = "local"
    jwt_secret: str = "change_me_to_a_long_random_string"
    default_region: str = "na"
    enable_openai: bool = False
    openai_model: str = "gpt-4o-mini"

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            app_name=os.getenv("VIRALNOW_APP_NAME", "ViralNOW API"),
            environment=os.getenv("VIRALNOW_ENVIRONMENT", "local"),
            jwt_secret=os.getenv("VIRALNOW_JWT_SECRET", "change_me_to_a_long_random_string"),
            default_region=os.getenv("VIRALNOW_DEFAULT_REGION", "na"),
            enable_openai=os.getenv("USE_OPENAI", "0") not in {"0", "false", "False"},
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )


@lru_cache()
def get_settings() -> Settings:
    """Cached accessor to application settings."""

    return Settings.from_env()
