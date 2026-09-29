import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "BhuSetu"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "bhusetu-hackathon-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = "sqlite:///./bhusetu.db"
    STORAGE_DIR: str = "data/storage"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    TESSERACT_CMD: Optional[str] = None

    AUTO_ACCEPT_THRESHOLD: float = 0.90
    FIELD_REVIEW_THRESHOLD: float = 0.60
    MOCK_OCR_MODE: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
