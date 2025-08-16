"""
Environemnt & Configuration settings for Airo Cyber Scout - Cybairo
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Environment settings for Airo Cyber Scout - Cybairo
    """
    
    # Application settings
    APP_NAME: str 
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # API settings
    GROQ_API_KEY: str
    GROQ_MODEL_ID: str

    class Config:
        env_file = ".env"
        extra = "allow"
        case_sensitive = False
        
# Global settings instance
settings = Settings()