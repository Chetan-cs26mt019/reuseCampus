from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ReUse Campus API"
    app_version: str = "0.1.0"
    database_url: str = (
        "mysql+pymysql://reuse_user:change_me"
        "@127.0.0.1:3306/reuse_campus"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
