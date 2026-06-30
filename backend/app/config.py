from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BIBLEMAXXING_", env_file=".env")

    env: str = "development"
    database_url: str = "sqlite:///./biblemaxxing-dev.db"
    secret_key: str = Field(default="dev-only-change-me")
    access_token_minutes: int = 60 * 24 * 30
    youtube_api_key: str | None = None
    auto_create_tables: bool = True
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
