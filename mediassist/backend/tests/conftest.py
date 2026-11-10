import os

# Tests must never inherit provider credentials or production settings from the
# machine running pytest. Configure harmless local defaults before app imports.
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET"] = "mediassist-test-secret-for-local-pytest-only"
os.environ["DATABASE_URL"] = "sqlite:///./mediassist-test.db"
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("SERP_API_KEY", None)
os.environ["ENABLE_WEB_SEARCH"] = "false"
os.environ["ENABLE_RATE_LIMIT"] = "false"
