"""Embed processed SCOTUS opinions and persist to ChromaDB.

Reads:  data/processed/scotus_cases.jsonl
Writes: data/cached/chroma_db/   (PersistentClient, collection 'scotus_v2')

Chunking: ~500-token windows with 50-token overlap, sentence-aware.
Embedding: sentence-transformers/all-MiniLM-L6-v2 (384-d, ~80 MB).
Device: prefers Apple MPS, then CUDA, then CPU.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from backend.app.config import settings

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = REPO_ROOT / "data" / "processed" / "scotus_cases.jsonl"

CHUNK_TOKENS = 500
OVERLAP_TOKENS = 50
BATCH_SIZE = 64

# A token is roughly 0.75 words; we'll use whitespace words as a proxy and
# slice on sentence boundaries.
WORDS_PER_CHUNK = int(CHUNK_TOKENS / 0.75)         # ≈ 666 words
OVERLAP_WORDS = int(OVERLAP_TOKENS / 0.75)         # ≈ 66 words

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _pick_device() -> str:
    import torch
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _chunk(text: str) -> list[str]:
    """Sentence-aware sliding window over ``text``.

    Greedily pack sentences until the running word count would exceed
    WORDS_PER_CHUNK, then emit a chunk and start the next one with the
    trailing OVERLAP_WORDS-worth of sentences for context continuity.
    """
    text = text.strip()
    if not text:
        return []

    sentences = SENT_SPLIT.split(text)
    chunks: list[str] = []
    buf: list[str] = []
    buf_words = 0
    for s in sentences:
        sw = len(s.split())
        if buf_words + sw > WORDS_PER_CHUNK and buf:
            chunks.append(" ".join(buf).strip())
            # carry overlap
            carry: list[str] = []
            carry_words = 0
            for prev in reversed(buf):
                pw = len(prev.split())
                if carry_words + pw > OVERLAP_WORDS:
                    break
                carry.insert(0, prev)
                carry_words += pw
            buf = carry
            buf_words = carry_words
        buf.append(s)
        buf_words += sw
    if buf:
        chunks.append(" ".join(buf).strip())
    return [c for c in chunks if c]


def main() -> None:
    if not CORPUS_PATH.exists():
        print(f"ERROR: {CORPUS_PATH} does not exist. Run build_corpus.py first.",
              file=sys.stderr)
        sys.exit(1)

    persist_dir = settings.chroma_persist_dir
    if persist_dir.exists():
        print(f"Wiping existing ChromaDB at {persist_dir}")
        shutil.rmtree(persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    device = _pick_device()
    print(f"Loading embedding model {settings.embedding_model!r} on device={device}")
    model = SentenceTransformer(settings.embedding_model, device=device)

    print(f"Opening Chroma at {persist_dir} (collection {settings.chroma_collection!r})")
    client = chromadb.PersistentClient(path=str(persist_dir))
    # Collection without an embedding_function — we pass embeddings directly,
    # since we want to control batching/device. Queries via the retriever
    # re-attach the same SentenceTransformer EF so cosine math matches.
    collection = client.get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"Streaming cases from {CORPUS_PATH}")
    # Dedupe by case_id (rare CAP citation collisions produce duplicate caseIds);
    # when we see a dupe, keep the record with the longer opinion text.
    by_id: dict[str, dict] = {}
    raw_count = 0
    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            raw_count += 1
            cid = rec.get("case_id") or ""
            if not cid:
                continue
            cur = by_id.get(cid)
            new_len = len(rec.get("majority_opinion_text") or "")
            if cur is None or new_len > len(cur.get("majority_opinion_text") or ""):
                by_id[cid] = rec
    cases = list(by_id.values())
    print(f"  raw records: {raw_count:,}  unique case_ids: {len(cases):,}  "
          f"(deduped {raw_count - len(cases)})")

    # Pass 1: chunk everything (cheap)
    chunk_records: list[dict] = []
    for case in tqdm(cases, desc="chunking", unit="case"):
        chunks = _chunk(case.get("majority_opinion_text") or "")
        for i, txt in enumerate(chunks):
            chunk_records.append(
                {
                    "id": f"{case['case_id']}::{i}",
                    "text": txt,
                    "metadata": {
                        "case_id": str(case.get("case_id") or ""),
                        "case_name": str(case.get("case_name") or ""),
                        "decision_date": str(case.get("decision_date") or ""),
                        "us_cite": str(case.get("us_cite") or ""),
                        "issue_area": str(case.get("issue_area") or "Unspecified"),
                        "chunk_index": i,
                    },
                }
            )
    print(f"  total chunks: {len(chunk_records):,}")

    # Pass 2: embed in batches and write to Chroma
    print(f"\nEmbedding + indexing (batch={BATCH_SIZE})")
    for start in tqdm(range(0, len(chunk_records), BATCH_SIZE), desc="embed", unit="batch"):
        batch = chunk_records[start : start + BATCH_SIZE]
        texts = [r["text"] for r in batch]
        embeddings = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        collection.add(
            ids=[r["id"] for r in batch],
            documents=texts,
            metadatas=[r["metadata"] for r in batch],
            embeddings=embeddings.tolist(),
        )

    print(f"\nIndex built. Collection count: {collection.count():,}")
    print(f"Persisted at: {persist_dir}")


if __name__ == "__main__":
    main()
