import asyncio
from io import BytesIO
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import text
from starlette.datastructures import UploadFile

from app.config import settings
from app.database import engine
from app.main import app
from app.routers import documents
from app.services.gemini_service import GeminiService
from app.services.metrics import (
    DATABASE_STATEMENTS_TOTAL,
    HTTP_REQUESTS_TOTAL,
    LLM_REQUESTS_TOTAL,
    LLM_TOKENS_TOTAL,
    OCR_REQUESTS_TOTAL,
    RATE_LIMIT_REJECTIONS_TOTAL,
)
from app.services.rate_limiter import rate_limiter


def _value(metric, **labels):
    return metric.labels(**labels)._value.get()


def test_metrics_endpoint_exposes_route_template_counters_and_excludes_itself(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", False)
    monkeypatch.setattr(settings, "METRICS_ENABLED", True)
    route = "/api/v1/health"
    before = _value(HTTP_REQUESTS_TOTAL, method="GET", route=route, status_code="200")
    client = TestClient(app)
    response = client.get(route)
    assert response.status_code == 200
    after_health = _value(HTTP_REQUESTS_TOTAL, method="GET", route=route, status_code="200")
    assert after_health == before + 1

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert "text/plain" in metrics_response.headers["content-type"]
    assert 'route="/api/v1/health"' in metrics_response.text
    assert "mediassist_http_request_duration_seconds_bucket" in metrics_response.text
    # Scraping the endpoint itself does not increment the application request counter.
    assert not any('route="/metrics"' in line for line in metrics_response.text.splitlines())


def test_metrics_endpoint_can_be_disabled(monkeypatch):
    monkeypatch.setattr(settings, "METRICS_ENABLED", False)
    response = TestClient(app).get("/metrics")
    assert response.status_code == 404


def test_http_metrics_use_route_templates_not_conversation_ids(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", False)
    monkeypatch.setattr(settings, "METRICS_ENABLED", True)
    secret_id = "987654321"
    response = TestClient(app).get(f"/api/v1/conversations/{secret_id}/messages")
    assert response.status_code == 401
    exposition = TestClient(app).get("/metrics").text
    assert 'route="/api/v1/conversations/{conversation_id}/messages"' in exposition
    assert secret_id not in exposition


def test_rate_limit_rejection_increments_bounded_counter(monkeypatch):
    rate_limiter.reset()
    monkeypatch.setattr(settings, "ENABLE_RATE_LIMIT", True)
    monkeypatch.setattr(settings, "RATE_LIMIT_PER_MINUTE", 1)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)
    route = "/api/v1/consent"
    before = _value(RATE_LIMIT_REJECTIONS_TOTAL, route=route)
    client = TestClient(app)
    client.get(route)
    blocked = client.get(route)
    assert blocked.status_code == 429
    assert _value(RATE_LIMIT_REJECTIONS_TOTAL, route=route) == before + 1
    rate_limiter.reset()


def test_database_statement_metrics_do_not_include_sql_text():
    before = _value(DATABASE_STATEMENTS_TOTAL, operation="SELECT", outcome="success")
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    assert _value(DATABASE_STATEMENTS_TOTAL, operation="SELECT", outcome="success") == before + 1


def test_llm_metrics_record_provider_usage_without_prompt_labels(monkeypatch):
    service = GeminiService()
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GROQ_API_KEY", None)
    monkeypatch.setattr(settings, "GEMINI_MODEL", "metrics-test-model")

    class FakeChain:
        async def ainvoke(self, payload):
            return SimpleNamespace(
                content="General information response.",
                usage_metadata={"input_tokens": 17, "output_tokens": 9},
            )

    monkeypatch.setattr(service, "_get_chain", lambda: FakeChain())
    requests_before = _value(
        LLM_REQUESTS_TOTAL,
        provider="gemini",
        model="metrics-test-model",
        outcome="success",
    )
    input_before = _value(
        LLM_TOKENS_TOTAL,
        provider="gemini",
        model="metrics-test-model",
        direction="input",
    )
    output_before = _value(
        LLM_TOKENS_TOTAL,
        provider="gemini",
        model="metrics-test-model",
        direction="output",
    )
    result = asyncio.run(service.generate_response("test question"))
    assert "General information response" in result
    assert _value(
        LLM_REQUESTS_TOTAL,
        provider="gemini",
        model="metrics-test-model",
        outcome="success",
    ) == requests_before + 1
    assert _value(
        LLM_TOKENS_TOTAL,
        provider="gemini",
        model="metrics-test-model",
        direction="input",
    ) == input_before + 17
    assert _value(
        LLM_TOKENS_TOTAL,
        provider="gemini",
        model="metrics-test-model",
        direction="output",
    ) == output_before + 9


def test_ocr_metrics_record_only_detected_type_and_outcome(monkeypatch):
    async def fake_extract_image(payload, content_type):
        return "sample extracted content", None

    monkeypatch.setattr(documents, "_extract_image", fake_extract_image)
    before = _value(OCR_REQUESTS_TOTAL, content_type="image/png", outcome="success")
    upload = UploadFile(filename="private-medical-document.png", file=BytesIO(b"\x89PNG\r\n\x1a\nimage"))
    response = asyncio.run(documents.extract_document_text(file=upload, current_user=None))
    assert response.content_type == "image/png"
    assert response.extracted_text == "sample extracted content"
    assert _value(OCR_REQUESTS_TOTAL, content_type="image/png", outcome="success") == before + 1
