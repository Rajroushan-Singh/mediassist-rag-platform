import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_public_jwt_placeholder():
    with pytest.raises(ValidationError, match="unique secret"):
        Settings(
            APP_ENV="production",
            JWT_SECRET="replace-with-a-unique-secret-at-least-32-characters",
        )


def test_production_accepts_non_placeholder_long_jwt_secret():
    settings = Settings(
        APP_ENV="production",
        JWT_SECRET="Z9w7H2k5Q8m1P4r6T3y0V5c8N2b7L4s9X1q6A3d5F8k0",
    )
    assert settings.APP_ENV == "production"
