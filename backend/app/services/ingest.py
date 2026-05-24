"""Ingest SCOTUS .txt + .json pairs from data/scotus_cases/ into ChromaDB.

Pipeline:
    1. Discover (.txt, .json) pairs under data/scotus_cases/.
    2. Split each opinion with RecursiveCharacterTextSplitter.
    3. Embed each chunk locally with sentence-transformers (all-MiniLM-L6-v2).
    4. Upsert chunks + metadata into a persistent ChromaDB collection.

Run from the project root:
    python -m src.ingest

No LLM API is called in this stage. Embedding is done entirely on-device,
so no ANTHROPIC_API_KEY is required.
"""
from __future__ import annotations

import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Iterator

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

LOG = logging.getLogger("ingest")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "scotus_cases"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

COLLECTION_NAME = "scotus_cases"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384-dim, free, runs on CPU.

# Why chunk_size=800 / chunk_overlap=100?
# An ~800-character window holds roughly one paragraph of legal prose
# (~150 words / ~120 tokens). That is small enough for retrieval to lock
# onto a single holding, argument, or fact, but large enough to keep a
# complete idea intact, which matters in legal text where mid-sentence cuts
# mangle citations and antecedents. A 100-character (~12.5%) overlap
# preserves continuity across boundaries, so a sentence whose subject
# lives in the previous chunk ("This holding...") still has a chance of
# being retrieved with its referent intact. The pair also keeps the
# top-k retrieved context comfortably within the prompt budget when we
# stuff results into Claude later.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def iter_case_pairs(data_dir: Path) -> Iterator[tuple[Path, Path]]:
    for txt_path in sorted(data_dir.glob("*.txt")):
        json_path = txt_path.with_suffix(".json")
        if not json_path.exists():
            LOG.warning("No metadata for %s, skipping", txt_path.name)
            continue
        yield txt_path, json_path


def load_pair(txt_path: Path, json_path: Path) -> tuple[str, dict]:
    text = txt_path.read_text(encoding="utf-8")
    meta = json.loads(json_path.read_text(encoding="utf-8"))
    return text, meta


def build_collection() -> chromadb.api.models.Collection.Collection:
    # If the directory exists but has no sqlite file, it's stale — wipe it
    if CHROMA_DIR.exists() and not (CHROMA_DIR / "chroma.sqlite3").exists():
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if not DATA_DIR.exists() or not any(DATA_DIR.glob("*.txt")):
        LOG.error(
            "No .txt files found in %s. Run data/download_scotus.py first.", DATA_DIR
        )
        return 1

    LOG.info("Loading sentence-transformer model: %s", EMBEDDING_MODEL)
    collection = build_collection()
    LOG.info(
        "ChromaDB collection '%s' ready at %s", COLLECTION_NAME, CHROMA_DIR
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        # Prefer paragraph then sentence breaks so chunks tend not to land
        # mid-citation; fall back to whitespace and finally raw chars.
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    pairs = list(iter_case_pairs(DATA_DIR))
    total_cases = len(pairs)
    LOG.info("Found %d case files to ingest", total_cases)

    cases_done = 0
    cases_failed = 0
    total_chunks = 0

    for idx, (txt_path, json_path) in enumerate(pairs, start=1):
        try:
            text, meta = load_pair(txt_path, json_path)
            if not text.strip():
                LOG.warning("Empty text for %s, skipping", txt_path.name)
                continue

            chunks = splitter.split_text(text)
            if not chunks:
                LOG.warning("No chunks produced for %s, skipping", txt_path.name)
                continue

            base_id = txt_path.stem
            ids = [f"{base_id}__chunk_{i:04d}" for i in range(len(chunks))]
            metadatas = [
                {
                    "case_name": str(meta.get("case_name", "")),
                    "year": int(meta.get("year") or 0),
                    "source_file": txt_path.name,
                    "chunk_index": i,
                }
                for i in range(len(chunks))
            ]
            # upsert (not add) so re-running is idempotent.
            collection.upsert(documents=chunks, metadatas=metadatas, ids=ids)
            total_chunks += len(chunks)
            cases_done += 1
            print(
                f"  Processed {idx}/{total_cases} cases, {total_chunks} chunks indexed"
            )
        except Exception:
            cases_failed += 1
            LOG.exception("Failed to ingest %s, continuing", txt_path.name)

    avg_chunks = (total_chunks / cases_done) if cases_done else 0.0
    print()
    print("=== Ingestion summary ===")
    print(f"  Total cases processed: {cases_done}")
    print(f"  Total cases failed:    {cases_failed}")
    print(f"  Total chunks indexed:  {total_chunks}")
    print(f"  Average chunks/case:   {avg_chunks:.1f}")
    print(f"  ChromaDB path:         {CHROMA_DIR}")
    print(f"  Collection:            {COLLECTION_NAME}")
    return 0 if cases_failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
