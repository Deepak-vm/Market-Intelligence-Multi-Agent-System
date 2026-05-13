import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    NEWSAPI_KEY: str = ""
    GNEWS_KEY: str = ""
    
    # DB configuration (default to local SQLite file)
    DATABASE_URL: str = "sqlite:///./market_intel.db"
    
    # LLM Models
    SEARCHER_MODEL: str = "llama-3.1-8b-instant"
    ANALYST_MODEL: str = "llama-3.1-70b-versatile"
    
    # Tunable Dedup & Verification Thresholds
    DEDUP_EPS: float = 0.35
    DEDUP_DATE_WINDOW_DAYS: int = 7
    AUTO_PUBLISH_CONFIDENCE_THRESHOLD: float = 0.75
    AUTO_PUBLISH_MIN_SOURCES: int = 2
    DISCARD_CONFIDENCE_FLOOR: float = 0.40
    
    # Watchlist Default
    DEFAULT_WATCHLIST: List[str] = [
        "OpenAI",
        "Stripe",
        "Anthropic",
        "Figma",
        "Replit",
        "Perplexity",
        "Cohere",
        "ElevenLabs"
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
