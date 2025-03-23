from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_DRIVER_NAME: str = "postgresql+asyncpg"
    DB_USERNAME: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_DATABASE: str = "talkushka_database"
    DB_SCHEMA: str = "talkushka_service"

    LOG_LEVEL: str = "DEBUG"

    UPDATE_LIMIT_HOUR_UTC: int = 0

    VIDEO_LIMIT: int = 10
    AUDIO_LIMIT: int = 30
    SUBTITLE_LIMIT: int = 100
    TRANSCRIPTION_LIMIT: int = 3


settings = Settings()

DSN = (
    f"{settings.DB_DRIVER_NAME}://{settings.DB_USERNAME}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"
)
