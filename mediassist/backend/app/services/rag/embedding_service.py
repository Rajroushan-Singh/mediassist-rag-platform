from langchain_huggingface import HuggingFaceEmbeddings

class EmbeddingService:
    """Create local embeddings using HuggingFace without cloud rate limits."""
    def get_embeddings(self) -> HuggingFaceEmbeddings:
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

embedding_service = EmbeddingService()