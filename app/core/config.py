import os
from pathlib import Path
from pydantic import BaseSettings, PostgresDsn, validator, AnyUrl
from typing import Optional, Dict, Any, List


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):

    PROJECT_NAME: str = "Pass" # I will change that later
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SERVER_NAME: str = "server" # I will change that later
    SERVER_HOST: AnyUrl = "http://localhost:8000"
    
    
    SECRET_KEY: str = "your-secret-key-here"  # I will change that in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 дней
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # I will change that in production
    
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "visite_db"
    POSTGRES_PORT: str = "5432"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = "pass"
    EMAILS_FROM_NAME: Optional[str] = "Pass" # I will change that later
    
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    
    DEBUG: bool = True
    TESTING: bool = False
    
    class Config:
        case_sensitive = True
        env_file = os.path.join(BASE_DIR, ".env")
        env_file_encoding = "utf-8"


class DevelopmentSettings(Settings):
    
    DEBUG: bool = True
    BACKEND_CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


class ProductionSettings(Settings):

    DEBUG: bool = False
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    BACKEND_CORS_ORIGINS = [
        "https://your-production-domain.com",
        "https://www.your-production-domain.com"
    ]


class TestingSettings(Settings):

    TESTING: bool = True
    POSTGRES_DB: str = "test_visite_db"
    SQLALCHEMY_DATABASE_URI: str = "sqlite+aiosqlite:///./test.db"


def get_settings() -> Settings:
    env = os.getenv("ENV", "development").lower()
    
    settings_classes = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings
    }
    
    return settings_classes.get(env, DevelopmentSettings)()


settings = get_settings()
