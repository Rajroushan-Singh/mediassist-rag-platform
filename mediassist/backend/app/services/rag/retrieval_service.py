import logging
from pathlib import Path
import time
from time import perf_counter

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import settings
from app.services.rag.embedding_service import embedding_service
from app.services.metrics import RAG_SEARCHES_TOTAL, RAG_SEARCH_DURATION_SECONDS
from app.services.rag.reranker import reranker_service

logger = logging.getLogger(__name__)


class RetrievalService:
    """Persistent FAISS retrieval for curated, application-owned knowledge.

    FAISS.load_local uses a pickle-backed docstore. Only load the index created
    by this application's own ingestion command; never point this path at an
    uploaded or otherwise untrusted directory.
    """

    def __init__(self, index_path: Path | None = None):
        self.index_path = Path(index_path or settings.FAISS_INDEX_PATH)
        self._store: FAISS | None = None

    def _load_store(self) -> FAISS | None:
        if self._store is not None:
            return self._store
        if not (self.index_path / "index.faiss").is_file():
            return None
        try:
            self._store = FAISS.load_local(
                str(self.index_path),
                embedding_service.get_embeddings(),
                allow_dangerous_deserialization=True,
            )
        except Exception as exc:
            logger.warning("Unable to load configured FAISS index: %s", type(exc).__name__)
            return None
        return self._store

    def replace_documents(self, documents: list[Document]) -> None:
        import time
        if not documents:
            raise ValueError("Refusing to create an empty FAISS index.")
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        batch_size = 15  # Slightly smaller batch size to stay safer
        self._store = None
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        logger.info("Starting document ingestion: %s total documents across %s batches.", len(documents), total_batches)

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            current_batch = (i // batch_size) + 1
            
            success = False
            while not success:
                try:
                    logger.info("Processing batch %s of %s (size: %s)...", current_batch, total_batches, len(batch))
                    if self._store is None:
                        self._store = FAISS.from_documents(
                            batch,
                            embedding_service.get_embeddings(),
                        )
                    else:
                        self._store.add_documents(batch)
                    success = True
                except Exception as exc:
                    if "429" in str(exc) or "ResourceExhausted" in str(exc):
                        logger.warning("Rate limit hit on batch %s. Pausing for 25 seconds before retrying...", current_batch)
                        time.sleep(25)
                    else:
                        raise exc
            
            if i + batch_size < len(documents):
                time.sleep(8)  # Safe buffer between batches

        self._store.save_local(str(self.index_path))
        logger.info("Successfully built and saved FAISS index to %s", self.index_path)

    def add_documents(self, chunks: list[dict] | list[Document]) -> None:
        """Compatibility helper; ingestion replaces the complete index."""
        documents = []
        for item in chunks:
            if isinstance(item, Document):
                documents.append(item)
            else:
                documents.append(
                    Document(
                        page_content=item.get("content", ""),
                        metadata=item.get("metadata", {}),
                    )
                )
        self.replace_documents(documents)

    def search(
        self,
        query: str,
        limit: int = 4,
        *,
        candidate_k: int | None = None,
        use_reranker: bool = False,
    ) -> list[dict]:
        started = perf_counter()
        outcome = "error"

        try:
            if not query.strip() or limit < 1:
                outcome = "empty_query"
                return []

            store = self._load_store()
            if store is None:
                outcome = "index_unavailable"
                return []

            fetch_k = max(limit, candidate_k or limit) if use_reranker else limit
            matches = store.similarity_search_with_score(
                query[:4000],
                k=fetch_k,
            )

            candidates = [
                {
                    "content": document.page_content,
                    "metadata": document.metadata or {},
                    "distance": float(distance),
                }
                for document, distance in matches
            ]

            if use_reranker and candidates:
                try:
                    candidates = reranker_service.rerank(query, candidates)
                except Exception as exc:
                    # Keep the app usable if the reranker/model download fails.
                    logger.warning(
                        "Reranking failed; using FAISS order (%s)",
                        type(exc).__name__,
                    )

            outcome = "results" if candidates else "empty_results"
            return candidates[:limit]

        except Exception as exc:
            logger.warning("FAISS search failed: %s", type(exc).__name__)
            outcome = "error"
            return []
        finally:
            RAG_SEARCHES_TOTAL.labels(outcome=outcome).inc()
            RAG_SEARCH_DURATION_SECONDS.observe(perf_counter() - started)


retrieval_service = RetrievalService()