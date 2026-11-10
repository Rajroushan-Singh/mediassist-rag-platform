import pytest

from app.services.gemini_service import GeminiService
from app.services.metrics import RAG_SEARCHES_TOTAL
from app.services.rag.retrieval_service import RetrievalService


def test_search_returns_no_results_if_index_has_not_been_built(tmp_path):
    service = RetrievalService(index_path=tmp_path / "missing-index")
    before = RAG_SEARCHES_TOTAL.labels(outcome="index_unavailable")._value.get()
    assert service.search("general health information") == []
    assert RAG_SEARCHES_TOTAL.labels(outcome="index_unavailable")._value.get() == before + 1


def test_refuses_to_build_an_empty_faiss_index(tmp_path):
    service = RetrievalService(index_path=tmp_path / "index")
    with pytest.raises(ValueError, match="empty FAISS index"):
        service.replace_documents([])


def test_formats_retrieved_passage_with_page_source():
    formatted = GeminiService._format_documents([
        {
            "content": "Reviewed passage content",
            "metadata": {"title": "Reference title", "source": "guide.pdf", "page": 4},
        }
    ])
    assert "Reference title" in formatted
    assert "guide.pdf, page 4" in formatted
    assert "Reviewed passage content" in formatted


def test_no_results_are_explicitly_marked_in_prompt_context():
    assert "No relevant curated" in GeminiService._format_documents([])
