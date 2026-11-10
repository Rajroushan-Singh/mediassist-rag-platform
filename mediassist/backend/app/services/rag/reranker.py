from functools import lru_cache

from app.config import settings


@lru_cache(maxsize=1)
def _load_model():
    # Import lazily so the app can run with reranking disabled.
    from sentence_transformers import CrossEncoder

    return CrossEncoder(
        settings.RERANKER_MODEL,
        device=settings.RERANKER_DEVICE,
        max_length=512,
    )


class CrossEncoderReranker:
    def rerank(self, query: str, candidates: list[dict]) -> list[dict]:
        if not candidates:
            return []

        model = _load_model()
        pairs = [(query, item["content"]) for item in candidates]
        scores = model.predict(
            pairs,
            batch_size=8,
            show_progress_bar=False,
        )

        ranked = []
        for item, score in zip(candidates, scores):
            result = dict(item)
            result["rerank_score"] = float(score)
            ranked.append(result)

        return sorted(
            ranked,
            key=lambda item: item["rerank_score"],
            reverse=True,
        )


reranker_service = CrossEncoderReranker()
