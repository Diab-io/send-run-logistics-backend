from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    RESET_PASSWORD_SECRET: str
    VERIFICATION_SECRET: str
    GOOGLE_MAPS_API_KEY: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    ML_MODEL_PATH: str = "app/trained_models/pricing_pipeline.joblib"
    OTP_EXPIRY_SECONDS: int = 600
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()