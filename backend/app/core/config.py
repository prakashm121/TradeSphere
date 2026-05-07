from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./stock_market.db"
    
    # JWT Settings
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: str = "*"

    # Background services (v1: legacy random market maker disabled by default)
    ENABLE_LEGACY_MARKET_MAKER: bool = False
    
    # Public URL used in verification emails (set to deployed backend in production)
    VERIFICATION_BASE_URL: str = "http://127.0.0.1:5000"

    # Email settings (optional in local/mock mode)
    MAIL_SERVER: str = ""
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = "TradeSphere"
    MOCK_EMAIL: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()