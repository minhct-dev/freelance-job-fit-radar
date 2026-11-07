from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str | None = None
    telegram_chat_id: int | None = None
    database_url: str = "sqlite:///./radar.db"
    scan_interval_minutes: int = 15
    min_fit_score: int = 70
    scheduler_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

