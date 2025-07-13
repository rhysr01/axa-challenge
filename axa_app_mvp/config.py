"""Application configuration and settings."""
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseSettings, AnyHttpUrl, validator

class Settings(BaseSettings):
    # Application settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-here"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 10000
    WORKERS: int = 4
    TIMEOUT: int = 120
    RELOAD: bool = False
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # File storage
    STORAGE_TYPE: str = "local"  # 'local' or 's3'
    STORAGE_PATH: str = "outputs"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Security
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Validate CORS_ORIGINS
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

# Initialize settings
settings = Settings()

# Create storage directory if it doesn't exist
if settings.STORAGE_TYPE == "local":
    Path(settings.STORAGE_PATH).mkdir(exist_ok=True)
