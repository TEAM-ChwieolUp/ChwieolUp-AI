from __future__ import annotations

import os

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:
    from pydantic import BaseModel

    class Settings(BaseModel):
        app_env: str = os.getenv("APP_ENV", "local")
        ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model: str = os.getenv("OLLAMA_MODEL", "gemma4:e2b")

else:
    class Settings(BaseSettings):
        app_env: str = "local"
        ollama_base_url: str = "http://localhost:11434"
        ollama_model: str = "gemma4:e2b"

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )


settings = Settings()
