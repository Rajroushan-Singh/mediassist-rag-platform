from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Environment-driven settings; defaults are for local development only."""

    APP_NAME: str = "MediAssist"
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./mediassist.db"
    JWT_SECRET: str = "unsafe-development-secret-change-before-deploy"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:5173"

    # LLM Providers (Groq & Gemini)
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_VISION_MODEL: str = "llama-3.2-11b-vision-preview"

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    FAISS_INDEX_PATH: Path = BACKEND_DIR / "data" / "faiss_index"
    KNOWLEDGE_BASE_PATH: Path = BACKEND_DIR / "app" / "data" / "medical_knowledge"

    SERP_API_KEY: str | None = None
    ENABLE_WEB_SEARCH: bool = False

    HEALTH_CONSENT_VERSION: str = "1.0"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    MAX_ATTACHMENT_CHARS: int = 40_000
    MAX_PDF_PAGES: int = 10
    MAX_IMAGE_PIXELS: int = 20_000_000

    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    METRICS_ENABLED: bool = True
    RERANKER_ENABLED: bool = False
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKER_DEVICE: str = "cpu"
    RERANKER_CANDIDATE_K: int = 10

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @property
    def allowed_origins(self) -> list[str]:
        values = [self.FRONTEND_URL, *self.CORS_ORIGINS.split(",")]
        return list(dict.fromkeys(item.strip() for item in values if item.strip()))

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.APP_ENV.lower() in {"prod", "production"}:
            secret = self.JWT_SECRET.strip()
            placeholder = secret.lower().startswith(("replace-with-", "change-me", "your-secret"))
            if secret == "unsafe-development-secret-change-before-deploy" or len(secret) < 32 or placeholder:
                raise ValueError("Production JWT_SECRET must be a unique secret of at least 32 characters.")
        return self


settings = Settings()
