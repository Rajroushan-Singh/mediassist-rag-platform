import json
import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import settings

logger = logging.getLogger(__name__)


def load_source_documents(knowledge_base_path: Path | None = None) -> list[Document]:
    """Read selectable text from local PDFs and JSON knowledge files."""
    root = Path(knowledge_base_path or settings.KNOWLEDGE_BASE_PATH)
    documents: list[Document] = []
    if not root.exists():
        logger.warning("Knowledge source directory does not exist: %s", root)
        return documents

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".pdf":
            try:
                reader = PdfReader(str(path))
                for page_number, page in enumerate(reader.pages, start=1):
                    text = (page.extract_text() or "").strip()
                    if text:
                        documents.append(
                            Document(
                                page_content=text,
                                metadata={
                                    "title": path.stem,
                                    "source": path.name,
                                    "filename": path.name,
                                    "page": page_number,
                                    "source_type": "curated_knowledge",
                                },
                            )
                        )
            except Exception as exc:
                logger.warning("Skipping unreadable PDF %s (%s)", path.name, type(exc).__name__)
        elif path.suffix.lower() == ".json":
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    text = str(payload.get("content") or json.dumps(payload, ensure_ascii=False, indent=2))
                    source_url = str(payload.get("source_url") or "")
                    if "example.com" in source_url.lower():
                        source_url = ""
                    metadata = {
                        "title": str(payload.get("title") or path.stem),
                        "source": str(payload.get("source") or path.name),
                        "filename": path.name,
                        "source_type": "curated_knowledge",
                    }
                    if source_url:
                        metadata["url"] = source_url
                else:
                    text = json.dumps(payload, ensure_ascii=False, indent=2)
                    metadata = {
                        "title": path.stem,
                        "source": path.name,
                        "filename": path.name,
                        "source_type": "curated_knowledge",
                    }
                if text.strip():
                    documents.append(
                        Document(
                            page_content=text,
                            metadata=metadata,
                        )
                    )
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Skipping unreadable JSON %s (%s)", path.name, type(exc).__name__)
    return documents


def prepare_chunks(
    knowledge_base_path: Path | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 160,
) -> list[Document]:
    """Split source documents while carrying citation metadata forward."""
    sources = load_source_documents(knowledge_base_path)
    if not sources:
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(sources)
