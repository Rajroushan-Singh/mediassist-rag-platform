#!/usr/bin/env python3
"""Join missed retrieval cases to labeled and retrieved chunk previews.

Run from backend/:
python scripts/analyze_retrieval_failures.py \
  --results evaluation/results.csv \
  --dataset evaluation/questions.jsonl \
  --chunks evaluation/chunks.csv \
  --output evaluation/failures_review.csv
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
            if not isinstance(row, dict) or not isinstance(row.get("query"), str):
                raise ValueError(f"Line {line_number} must have a string query.")
            ids = row.get("relevant_chunk_ids")
            if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
                raise ValueError(f"Line {line_number} must have relevant_chunk_ids as a string list.")
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("evaluation/results.csv"))
    parser.add_argument("--dataset", type=Path, default=Path("evaluation/questions.jsonl"))
    parser.add_argument("--chunks", type=Path, default=Path("evaluation/chunks.csv"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/failures_review.csv"))
    args = parser.parse_args()

    results = read_csv(args.results)
    dataset = read_jsonl(args.dataset)
    chunks = read_csv(args.chunks)
    preview_by_id = {row.get("chunk_id", ""): row.get("preview", "") for row in chunks}
    labels_by_query = {row["query"].strip(): row["relevant_chunk_ids"] for row in dataset}

    failures = []
    for result in results:
        query = result.get("query", "").strip()
        relevant = labels_by_query.get(query)
        if relevant is None:
            raise ValueError(f"Query in results CSV is missing from dataset JSONL: {query!r}")
        retrieved = [part.strip() for part in result.get("retrieved_chunk_ids", "").split(" | ") if part.strip()]
        hits = set(relevant).intersection(retrieved)
        if hits:
            continue
        failures.append(
            {
                "query": query,
                "target_chunk_ids": " | ".join(relevant),
                "target_previews": " || ".join(preview_by_id.get(identifier, "[preview not found]") for identifier in relevant),
                "retrieved_chunk_ids_ranked": " | ".join(retrieved),
                "retrieved_previews_ranked": " || ".join(
                    f"rank {rank}: {preview_by_id.get(identifier, '[preview not found]')}"
                    for rank, identifier in enumerate(retrieved, 1)
                ),
                "manual_miss_cause": "",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "query",
        "target_chunk_ids",
        "target_previews",
        "retrieved_chunk_ids_ranked",
        "retrieved_previews_ranked",
        "manual_miss_cause",
    ]
    with args.output.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(failures)

    print(f"Failed queries: {len(failures)} of {len(results)}")
    print(f"Review file: {args.output}")
    print("Fill manual_miss_cause in a spreadsheet (e.g. label issue, weak query match, chunk boundary, missing corpus coverage, or ranking/near-duplicate issue).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
