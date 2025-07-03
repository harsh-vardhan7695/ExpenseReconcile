"""
SQLite Configuration for Immediate Testing
This version uses SQLite instead of PostgreSQL for quick setup
"""

import os
from typing import Dict, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Database Configuration - Using SQLite
    DATABASE_URL: str = "sqlite:///./expense_reconciliation.db"
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str = Field(default="3b946f73ad4544e2a3ee86c3e32e7866")
    AZURE_OPENAI_BASE_URL: str = Field(default="https://703227482-dall-e3.openai.azure.com/")
    AZURE_OPENAI_API_VERSION: str = Field(default="2025-01-01-preview")
    AZURE_OPENAI_MODEL: str = Field(default="703227482-GPT-4o-mini")
    
    # Email Configuration (optional for demo)
    SMTP_SERVER: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587)
    EMAIL_USERNAME: str = Field(default="demo@example.com")
    EMAIL_PASSWORD: str = Field(default="demo_password")
    FROM_EMAIL: str = Field(default="demo@example.com")
    
    # File Processing Directories
    UPLOAD_DIR: str = Field(default="data/uploads")
    PROCESSED_DIR: str = Field(default="data/processed")
    REPORTS_DIR: str = Field(default="data/reports")
    
    # Matching Algorithm Settings
    AMOUNT_TOLERANCE: float = Field(default=0.01)
    DATE_TOLERANCE_DAYS: int = Field(default=3)
    FUZZY_MATCH_THRESHOLD: int = Field(default=80)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_llm_config() -> Dict:
    """Get AutoGen LLM configuration"""
    return {
        "config_list": [
            {
                "model": settings.AZURE_OPENAI_MODEL,
                "api_key": settings.AZURE_OPENAI_API_KEY,
                "base_url": settings.AZURE_OPENAI_BASE_URL,
                "api_type": "azure",
                "api_version": settings.AZURE_OPENAI_API_VERSION,
            }
        ],
        "temperature": 0.1,
        "timeout": 60,
    }


def get_email_config() -> Dict:
    """Get email configuration"""
    return {
        "smtp_server": settings.SMTP_SERVER,
        "smtp_port": settings.SMTP_PORT,
        "username": settings.EMAIL_USERNAME,
        "password": settings.EMAIL_PASSWORD,
        "from_email": settings.FROM_EMAIL,
    }


# Ensure directories exist
def setup_directories():
    """Create necessary directories"""
    import os
    directories = [
        settings.UPLOAD_DIR,
        settings.PROCESSED_DIR,
        settings.REPORTS_DIR,
        "data/demo",
        "examples"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


# Run setup on import
setup_directories() 