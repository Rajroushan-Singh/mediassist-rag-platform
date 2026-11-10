#!/usr/bin/env python3
"""Evaluate MediAssist's persisted FAISS retriever against labeled JSONL queries.

Run from backend/ with its virtual environment active. The script requires the
application's own FAISS index and its configured embedding credentials to load
and query it. It does not call the chat LLM.

Privacy: use synthetic or approved evaluation questions only. Query text is
written to the optional results CSV, so do not put real patient information in
the evaluation set.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from statistics import fmean
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.rag.retrieval_service import retrieval_service  # noqa: E402


def chunk_id(metadata: dict[str, Any], content: str = "") -> str:
    """Build a human-readable ID from the same source metadata stored in FAISS."""
    filename = str(metadata.get("filename") or metadata.get("source") or "unknown-source")
    page = metadata.get("page") or 0
    start_index = metadata.get("start_index")
    if start_index is None:
        # Compatibility for indexes created before start_index metadata existed.
        import hashlib

        suffix = "sha256=" + hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    else:
        suffix = f"start={start_index}"
    return f"{filename}::page={page}::{suffix}"


def load_dataset(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Line {line_number} must contain a JSON object.")
            query = row.get("query")
            relevant = row.get("relevant_chunk_ids")
            if not isinstance(query, str) or not query.strip():
                raise ValueError(f"Line {line_number}: 'query' must be a non-empty string.")
            if not isinstance(relevant, list) or not relevant or not all(isinstance(x, str) and x.strip() for x in relevant):
                raise ValueError(
                    f"Line {line_number}: 'relevant_chunk_ids' must be a non-empty list of chunk ID strings."
                )
            rows.append(
                {
                    "query": query.strip(),
                    "relevant_chunk_ids": sorted(set(x.strip() for x in relevant)),
                }
            )
    if not rows:
        raise ValueError("The evaluation JSONL file contains no labeled questions.")
    return rows


def export_index_chunks(output_path: Path) -> int:
    """Export stable IDs and previews so a human can label relevant chunks."""
    store = retrieval_service._load_store()
    if store is None:
        raise RuntimeError(
            "The FAISS index is missing or could not be loaded. Build it first with "
            "'python -m app.services.rag.ingest_documents' and verify embedding settings."
        )

    docs = []
    for docstore_id in store.index_to_docstore_id.values():
        document = store.docstore.search(docstore_id)
        if not hasattr(document, "page_content"):
            continue
        metadata = document.metadata or {}
        docs.append(
            {
                "chunk_id": chunk_id(metadata, document.page_content),
                "filename": metadata.get("filename") or metadata.get("source") or "",
                "page": metadata.get("page") or "",
                "start_index": metadata.get("start_index", ""),
                "title": metadata.get("title") or "",
                "preview": " ".join(document.page_content.split())[:300],
            }
        )
    if not docs:
        raise RuntimeError("The configured FAISS index contains no readable document chunks.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(docs[0].keys()))
        writer.writeheader()
        writer.writerows(docs)
    return len(docs)


def evaluate(dataset: list[dict[str, Any]], k: int) -> tuple[list[dict[str, Any]], dict[str, float]]:
    store = retrieval_service._load_store()
    if store is None:
        raise RuntimeError(
            "The FAISS index is missing or could not be loaded. Build it first with "
            "'python -m app.services.rag.ingest_documents' and verify embedding settings."
        )

    # Check labels against this exact index to catch stale IDs after re-ingestion.
    indexed_ids: set[str] = set()
    for docstore_id in store.index_to_docstore_id.values():
        document = store.docstore.search(docstore_id)
        if hasattr(document, "page_content"):
            indexed_ids.add(chunk_id(document.metadata or {}, document.page_content))

    all_relevant = {chunk for row in dataset for chunk in row["relevant_chunk_ids"]}
    unknown = sorted(all_relevant - indexed_ids)
    if unknown:
        examples = ", ".join(unknown[:5])
        raise ValueError(
            f"{len(unknown)} labeled chunk ID(s) are not in the current FAISS index. "
            f"Re-export the chunk list and update labels after rebuilding the index. Examples: {examples}"
        )

    scored: list[dict[str, Any]] = []
    for row in dataset:
        results = retrieval_service.search(row["query"], limit=k)
        if not results:
            raise RuntimeError(
                "FAISS returned no results for a non-empty index. Check the embedding API key, "
                "model availability, and backend logs; an empty/error search should not be scored as zero."
            )
        retrieved_ids = [chunk_id(item.get("metadata") or {}, item.get("content", "")) for item in results]
        relevant = set(row["relevant_chunk_ids"])
        hit_ids = [identifier for identifier in retrieved_ids if identifier in relevant]
        precision = len(hit_ids) / k
        recall = len(set(hit_ids)) / len(relevant)
        first_relevant_rank = next(
            (rank for rank, identifier in enumerate(retrieved_ids, start=1) if identifier in relevant),
            None,
        )
        scored.append(
            {
                "query": row["query"],
                "relevant_count": len(relevant),
                "returned_count": len(retrieved_ids),
                "relevant_retrieved": len(set(hit_ids)),
                f"precision_at_{k}": precision,
                f"recall_at_{k}": recall,
                "reciprocal_rank": 1 / first_relevant_rank if first_relevant_rank else 0.0,
                "retrieved_chunk_ids": " | ".join(retrieved_ids),
                "hit_chunk_ids": " | ".join(sorted(set(hit_ids))),
            }
        )

    macro_precision = fmean(row[f"precision_at_{k}"] for row in scored)
    macro_recall = fmean(row[f"recall_at_{k}"] for row in scored)
    total_hits = sum(row["relevant_retrieved"] for row in scored)
    total_relevant = sum(row["relevant_count"] for row in scored)
    summary = {
        "queries": float(len(scored)),
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "micro_precision": total_hits / (k * len(scored)),
        "micro_recall": total_hits / total_relevant,
        "macro_mrr": fmean(row["reciprocal_rank"] for row in scored),
    }
    return scored, summary


def write_results(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate MediAssist FAISS retrieval using labeled relevant chunk IDs."
    )
    parser.add_argument("--dataset", type=Path, help="JSONL file with query and relevant_chunk_ids fields")
    parser.add_argument("--k", type=int, default=4, help="Top-k cutoff (default: 4)")
    parser.add_argument(
        "--export-chunks",
        type=Path,
        help="Export current FAISS chunk IDs and short previews to CSV for human labeling, then exit",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("retrieval_eval_results.csv"),
        help="Per-query results CSV (default: retrieval_eval_results.csv)",
    )
    args = parser.parse_args()

    if args.k < 1:
        parser.error("--k must be at least 1")
    try:
        if args.export_chunks:
            count = export_index_chunks(args.export_chunks)
            print(f"Exported {count} chunks to {args.export_chunks}")
            print("Label relevant chunk IDs for each synthetic/approved test question in a JSONL dataset.")
            return 0
        if not args.dataset:
            parser.error("Provide --dataset or --export-chunks.")
        dataset = load_dataset(args.dataset)
        rows, summary = evaluate(dataset, args.k)
        write_results(args.output_csv, rows)
        print(f"Queries evaluated: {int(summary['queries'])}")
        print(f"Macro Precision@{args.k}: {summary['macro_precision']:.4f} ({summary['macro_precision']:.1%})")
        print(f"Macro Recall@{args.k}:    {summary['macro_recall']:.4f} ({summary['macro_recall']:.1%})")
        print(f"Micro Precision@{args.k}: {summary['micro_precision']:.4f} ({summary['micro_precision']:.1%})")
        print(f"Micro Recall@{args.k}:    {summary['micro_recall']:.4f} ({summary['micro_recall']:.1%})")
        print(f"Mean Reciprocal Rank:     {summary['macro_mrr']:.4f}")
        print(f"Per-query results: {args.output_csv}")
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
