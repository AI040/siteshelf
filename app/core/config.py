"""Application settings, loaded from environment variables / a .env file."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- general ---
    app_name: str = "Website Uploader"
    environment: str = "local"
    log_level: str = "INFO"

    # --- database ---
    # Either set DATABASE_URL (e.g. postgresql://user:pass@host:5432/dbname)
    # or the individual DB_* values below.
    database_url: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "postgres"
    db_user: str = "postgres"
    db_password: SecretStr = SecretStr("")
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # --- uploads ---
    max_upload_mb: int = 20
    upsert_batch_size: int = 5000
    rejected_preview_limit: int = 50

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def sqlalchemy_url(self) -> str | URL:
        if self.database_url:
            url = make_url(self.database_url)
            if url.drivername in {"postgres", "postgresql"}:
                url = url.set(drivername="postgresql+psycopg2")
            return url
        # URL.create escapes special characters in the password for us
        return URL.create(
            "postgresql+psycopg2",
            username=self.db_user,
            password=self.db_password.get_secret_value() or None,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
