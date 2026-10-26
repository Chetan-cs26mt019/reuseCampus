from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "ReUse Campus API"
    app_version: str = "0.1.0"

    database_url: str = (
        "mysql+pymysql://reuse_user:change_me"
        "@localhost:3306/reuse_campus"
    )

    secret_key: str = "development-only-change-this-key"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
