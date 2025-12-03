import csv
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from vanna.integrations.chromadb import ChromaAgentMemory
import json
from datetime import datetime


def _read_rows(csv_file: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with csv_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = (row.get("question") or "").strip()
            s = (row.get("sql") or "").strip()
            if q and s:
                rows.append({"question": q, "sql": s})
    return rows


def _stable_id(question: str, sql: str) -> str:
    m = hashlib.sha1()
    m.update(f"seed-qna::{question}:::{sql}".encode("utf-8"))
    return m.hexdigest()


def seed_qna(csv_path: Path, persist_directory: str, collection_name: str) -> Tuple[int, int]:
    """Seed Q&A into Chroma as tool-usage memories compatible with Vanna training.

    Stores entries with:
      - document: question
      - metadata: matches save_tool_usage fields (question, tool_name, args_json, timestamp, success, metadata_json)
    Returns (upserted_count, total_rows).
    """
    memory = ChromaAgentMemory(
        persist_directory=persist_directory, collection_name=collection_name
    )
    collection = memory._get_collection()  # type: ignore[attr-defined]

    rows = _read_rows(csv_path)
    if not rows:
        return (0, 0)

    docs: List[str] = []
    ids: List[str] = []
    metadatas: List[Dict[str, str]] = []
    now = datetime.now().isoformat()
    for r in rows:
        question = r["question"]
        sql = r["sql"]
        docs.append(question)
        ids.append(_stable_id(question, sql))
        meta = {
            "question": question,
            "tool_name": "run_sql",
            "args_json": json.dumps({"sql": sql}),
            "timestamp": now,
            "success": True,
            "metadata_json": json.dumps({"seed_source": "seed_qna.csv"}),
        }
        metadatas.append(meta)

    collection.upsert(documents=docs, metadatas=metadatas, ids=ids)
    return (len(ids), len(rows))


def seed_on_start() -> None:
    """Convenience wrapper to seed using defaults on process start."""
    load_dotenv()
    persist_directory = os.getenv("VANNA_CHROMA_DIR", "./chroma_db")
    collection_name = os.getenv("VANNA_CHROMA_COLLECTION", "vanna_memory")
    csv_path = Path(__file__).parent / "business" / "seed_qna.csv"
    if not csv_path.exists():
        return
    try:
        upserted, total = seed_qna(csv_path, persist_directory, collection_name)
        print(f"[seed] Seeded {upserted}/{total} entries into '{collection_name}' at '{persist_directory}'.")
    except Exception as exc:
        print(f"[seed] Skipped seeding due to error: {exc}")


if __name__ == "__main__":
    seed_on_start()