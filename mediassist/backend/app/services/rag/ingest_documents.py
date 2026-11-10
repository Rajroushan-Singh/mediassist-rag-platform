import logging

from app.services.rag.document_loader import prepare_chunks
from app.services.rag.retrieval_service import retrieval_service

logger = logging.getLogger(__name__)


def ingest_documents() -> int:
    chunks = prepare_chunks()
    if not chunks:
        logger.warning("No readable PDF/JSON knowledge chunks found; FAISS index was not changed.")
        return 0
    retrieval_service.replace_documents(chunks)
    logger.info("Built FAISS index with %s chunks.", len(chunks))
    return len(chunks)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingest_documents()
