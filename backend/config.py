"""
config.py — Application settings loaded from .env
"""
from pydantic_settings import BaseSettings
from pathlib import Path

_PLACEHOLDERS = {
    "MOCK", "",
    "your_google_places_api_key_here",
    "your_openai_api_key_here",
    "your_twilio_account_sid_here",
    "your_twilio_auth_token_here",
    "your_serpapi_key_here",
}


class Settings(BaseSettings):
    # External APIs
    google_places_api_key: str = "MOCK"
    serpapi_key: str = "MOCK"          # Alternative to Google Places (free tier available)
    openai_api_key: str = "MOCK"
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = "MOCK"    # Read by anthropic SDK from env automatically;
                                       # declared here so pydantic Settings accepts it from .env
    twilio_account_sid: str = "MOCK"
    twilio_auth_token: str = "MOCK"
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    # Infrastructure
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite+aiosqlite:///./data/leadgen.db"

    # Paths
    data_dir: str = "./data"
    generated_sites_dir: str = "./data/generated_sites"
    videos_dir: str = "./data/videos"

    # Business logic
    website_quality_threshold: int = 30

    # CORS
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def is_real(self, key: str) -> bool:
        """Returns True if the config key holds a real API key (not a placeholder)."""
        return getattr(self, key, "MOCK") not in _PLACEHOLDERS

    def ensure_dirs(self):
        """Create data directories if they don't exist."""
        for d in [self.data_dir, self.generated_sites_dir, self.videos_dir]:
            Path(d).mkdir(parents=True, exist_ok=True)


settings = Settings()
