import os
from pydantic_settings import BaseSettings
from typing import List, Dict


class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = "postgresql://username:password@localhost:5432/expense_reconciliation"
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: str = "3b946f73ad4544e2a3ee86c3e32e7866"
    AZURE_OPENAI_BASE_URL: str = "https://703227482-dall-e3.openai.azure.com/"
    AZURE_OPENAI_API_VERSION: str = "2025-01-01-preview"
    AZURE_OPENAI_MODEL: str = "703227482-GPT-4o-mini"
    
    # Email Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    FROM_EMAIL: str = ""
    
    # File Processing
    UPLOAD_DIR: str = "data/uploads"
    PROCESSED_DIR: str = "data/processed"
    REPORTS_DIR: str = "data/reports"
    
    # Matching Thresholds
    AMOUNT_TOLERANCE: float = 0.01  # 1% tolerance for amount matching
    DATE_TOLERANCE_DAYS: int = 3    # 3 days tolerance for date matching
    FUZZY_MATCH_THRESHOLD: int = 80  # 80% similarity for text matching
    
    class Config:
        env_file = ".env"


# Global LLM Config for AutoGen agents
def get_llm_config() -> Dict:
    settings = Settings()
    return {
        "config_list": [{
            "model": settings.AZURE_OPENAI_MODEL,
            "api_type": "azure",
            "base_url": settings.AZURE_OPENAI_BASE_URL,
            "api_key": settings.AZURE_OPENAI_API_KEY,
            "api_version": settings.AZURE_OPENAI_API_VERSION,
        }],
        "temperature": 0.1,
        "timeout": 120,
    }


# Initialize settings
settings = Settings() 