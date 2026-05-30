"""Application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    postgres_user: str = "docuask"
    postgres_password: str = "docuask_password"
    postgres_db: str = "docuask"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    database_url: str = ""

    redis_url: str = "redis://redis:6379/0"

    llm_api_key: str = "sk-mock"
    llm_api_base: str = "http://mock-llm:8888/v1"
    llm_model: str = "gpt-3.5-turbo"

    vector_db_host: str = "postgres"
    vector_db_port: int = 5432

    api_port: int = 8080
    worker_concurrency: int = 2
    max_upload_size: int = Field(default=10 * 1024 * 1024, gt=0)

    def generate_database_url(self) -> str:
        """Generate an async SQLAlchemy database URL from component settings."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
