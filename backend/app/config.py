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
    youtube_ingest_queries: str = (
        "Jesus Bible shorts|Christian prayer shorts|BibleProject shorts Jesus|"
        "Christian discipleship shorts|Scripture encouragement shorts|"
        "gospel encouragement shorts|Christian workplace faith shorts|"
        "Bible study shorts Jesus|worship shorts Christian|Christian testimony shorts"
    )
    youtube_ingest_pastor_queries: str = (
        "Philip Anthony Mitchell sermon clips|2819 Church Philip Anthony Mitchell shorts|"
        "Bryce Crawford Christian shorts|Bryce Crawford sermon clips|"
        "Cliffe Knechtle shorts|Give Me An Answer Cliffe Knechtle shorts|"
        "Tim Mackie BibleProject shorts|Gavin Ortlund Truth Unites clips|"
        "John Piper sermon clips|Tim Keller sermon clips|David Platt sermon clips|"
        "Matt Chandler sermon clips"
    )
    youtube_ingest_pastor_queries_per_cycle: int = 2
    youtube_ingest_max_results: int = 25
    youtube_ingest_interval_seconds: int = 60 * 60 * 2
    youtube_ingest_default_approve: bool = True
    auto_create_tables: bool = True
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def youtube_ingest_query_list(self) -> list[str]:
        return [query.strip() for query in self.youtube_ingest_queries.split("|") if query.strip()]

    @property
    def youtube_ingest_pastor_query_list(self) -> list[str]:
        return [
            query.strip()
            for query in self.youtube_ingest_pastor_queries.split("|")
            if query.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
