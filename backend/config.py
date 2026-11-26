import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "TraceMind AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://tracemind:tracemind123@localhost:5432/tracemind_db"
    )
    
    # LLM Settings (Optional Groq / Google Gemini integration)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    ENABLE_LLM: bool = False

    def model_post_init(self, __context) -> None:
        if not self.ENABLE_LLM and (self.GROQ_API_KEY.strip() or self.GOOGLE_API_KEY.strip()):
            self.ENABLE_LLM = True

    # API & CORS (supports local dev + Render + Vercel deployments)
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ]
    CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app|https://.*\.onrender\.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
