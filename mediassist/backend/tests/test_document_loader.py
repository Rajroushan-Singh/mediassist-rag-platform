import json

from app.services.rag.document_loader import load_source_documents, prepare_chunks


def test_loads_json_content_and_source_metadata(tmp_path):
    source_file = tmp_path / "test-health.json"
    source_file.write_text(
        json.dumps({
            "title": "Test health topic",
            "source": "Test source",
            "content": "A test paragraph about health information.",
            "source_url": "https://health.example.org/topic",
        }),
        encoding="utf-8",
    )

    documents = load_source_documents(tmp_path)
    assert len(documents) == 1
    assert documents[0].page_content == "A test paragraph about health information."
    assert documents[0].metadata["title"] == "Test health topic"
    assert documents[0].metadata["url"] == "https://health.example.org/topic"


def test_prepare_chunks_preserves_source_metadata(tmp_path):
    (tmp_path / "topic.json").write_text(
        json.dumps({"title": "Topic", "content": "health information " * 60}),
        encoding="utf-8",
    )
    chunks = prepare_chunks(tmp_path, chunk_size=120, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(chunk.metadata["title"] == "Topic" for chunk in chunks)
