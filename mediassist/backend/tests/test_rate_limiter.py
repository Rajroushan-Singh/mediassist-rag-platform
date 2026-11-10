from fastapi.testclient import TestClient
import pytest

from app.config import settings
from app.main import app
from app.services.rate_limiter import rate_limiter


@pytest.fixture(autouse=True)
def clean_rate_limiter():
    rate_limiter.reset()
    yield
    rate_limiter.reset()


def test_rate_limiter_allows_10_requests_then_blocks_11th(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 10)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)

    client = TestClient(app)

    # First 10 requests should succeed (or return 401/404 depending on auth, but NOT 429)
    for i in range(1, 11):
        response = client.get("/api/v1/consent")
        assert response.status_code != 429, f"Request {i} should not be rate-limited"
        assert response.headers.get("X-RateLimit-Limit") == "10"
        assert int(response.headers.get("X-RateLimit-Remaining", -1)) == 10 - i

    # The 11th request must be rejected with 429 Too Many Requests
    response11 = client.get("/api/v1/consent")
    assert response11.status_code == 429
    assert response11.headers.get("X-RateLimit-Limit") == "10"
    assert response11.headers.get("X-RateLimit-Remaining") == "0"
    assert "Retry-After" in response11.headers
    retry_after = int(response11.headers["Retry-After"])
    assert 1 <= retry_after <= 60

    payload = response11.json()
    assert "Rate limit exceeded" in payload["detail"]
    assert "maximum 10 requests per minute" in payload["detail"]


def test_exempt_endpoints_are_never_rate_limited(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 10)

    client = TestClient(app)

    # Health check and root should never be blocked even after 15 calls
    for _ in range(15):
        res_health = client.get("/api/v1/health")
        assert res_health.status_code == 200

        res_root = client.get("/")
        assert res_root.status_code == 200


def test_cors_options_preflight_is_exempt(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 10)

    client = TestClient(app)

    # OPTIONS preflight requests should never be blocked
    for _ in range(15):
        res = client.options("/api/v1/conversations")
        assert res.status_code != 429

