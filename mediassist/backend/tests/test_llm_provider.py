import asyncio

import pytest

from app.config import settings
from app.services.gemini_service import GeminiService


def test_provider_selection_obeys_llm_provider_even_if_both_keys_are_present(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "groq-test-key")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    assert GeminiService._provider_model() == ("gemini", settings.GEMINI_MODEL)

    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    assert GeminiService._provider_model() == ("groq", settings.GROQ_MODEL)


def test_unsupported_provider_fails_with_actionable_configuration_message(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mystery-provider")
    with pytest.raises(RuntimeError, match="Set it to 'groq' or 'gemini'"):
        GeminiService._provider_model()


def test_groq_model_not_found_is_not_retried_and_returns_fix(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "groq-test-key")
    monkeypatch.setattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
    service = GeminiService()
    calls = 0

    class FakeNotFoundError(Exception):
        status_code = 404

    class FakeChain:
        async def ainvoke(self, payload):
            nonlocal calls
            calls += 1
            raise FakeNotFoundError(
                "model_not_found: The model does not exist or you do not have access."
            )

    monkeypatch.setattr(service, "_get_chain", lambda: FakeChain())

    with pytest.raises(RuntimeError, match="GROQ_MODEL=openai/gpt-oss-120b"):
        asyncio.run(service.generate_response("test question"))
    assert calls == 1
