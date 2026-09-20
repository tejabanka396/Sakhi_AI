import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sakhi AI"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Database
    DATABASE_URL: str = Field(
        default="mysql+pymysql://root:root@localhost:3306/sakhi_ai?charset=utf8mb4",
        description="MySQL connection string with utf8mb4"
    )
    MYSQL_SSL_CA: str = Field(
        default="",
        description="Path to CA certificate file or raw PEM certificate content for MySQL SSL verification"
    )
    DATABASE_SSL_CA: str = Field(
        default="",
        description="Alias for MYSQL_SSL_CA"
    )

    # JWT Authentication
    JWT_SECRET: str = "sakhi_ai_super_secret_jwt_key_please_change_in_production_32chars_minimum"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"

    # Google OAuth (Optional)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Voice / TTS / STT
    EDGE_TTS_VOICE_FEMALE: str = "te-IN-ShrutiNeural"
    EDGE_TTS_VOICE_MALE: str = "te-IN-MohanNeural"
    EDGE_TTS_VOICE_EN_FEMALE: str = "en-IN-NeerjaNeural"
    EDGE_TTS_VOICE_EN_MALE: str = "en-IN-PrabhatNeural"

    # SMS / OTP Gateway Configuration
    SMS_PROVIDER: str = "msg91"  # 'dev' (local development), 'msg91' (real SMS), 'twilio', or 'mock'
    MSG91_AUTH_KEY: str = ""
    MSG91_TEMPLATE_ID: str = ""
    MSG91_SENDER_ID: str = "SAKHIA"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_PHONE: str = ""
    OTP_RATE_LIMIT_SECONDS: int = 60
    OTP_EXPIRE_MINUTES: int = 5

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower().strip() in ["production", "prod"]

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
