from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT_ENV), extra="ignore")

    app_env: str = "development"
    secret_key: str = "dev-only-change-me"
    token_encryption_key: str = ""
    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"

    database_url: str = "sqlite:///./jobmail.db"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://jobmail-mq9i.onrender.com/api/auth/google/callback"

    default_send_delay_seconds: int = 10
    max_upload_mb: int = 5
    upload_dir: str = "./storage"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
