from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Pydantic Settings v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # лишние переменные в .env не ломают запуск
    )

    # === GigaChat ===
    GIGACHAT_AUTH_KEY: str
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"
    GIGACHAT_OAUTH_URL: AnyHttpUrl = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    GIGACHAT_API_URL: AnyHttpUrl = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    GIGACHAT_MODEL: str = "GigaChat"

    # === Telegram ===
    TELEGRAM_BOT_TOKEN: str

    # === Email (SMTP) ===
    RESULT_EMAIL: str
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_USE_TLS: bool = True
    FROM_EMAIL: str


settings = Settings()
