from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RBL Guard"
    app_env: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False
    api_prefix: str = "/api/v1"

    secret_key: str = Field(default="change-me", min_length=16)
    access_token_expire_minutes: int = 60

    database_url: str = "postgresql+psycopg://rblguard:rblguard@db:5432/rblguard"

    dns_default_timeout: float = 3.0
    dns_max_concurrency: int = 60
    dns_retries: int = 2

    scheduler_batch_size: int = 200
    scheduler_tick_seconds: int = 30
    list_health_degrade_threshold: int = 40

    smtp_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_starttls: bool = True
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: EmailStr | None = None

    default_webhook_timeout: float = 10.0
    app_base_url: AnyHttpUrl | None = None

    public_lookup_rate_per_minute: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
