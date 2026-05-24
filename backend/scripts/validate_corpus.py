"""Sanity-check the assembled corpus + index.

Prints: total cases, total chunks, date range, top-10 issue areas,
and two sample retrievals.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from backend.app.services.retriever import retrieve

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = REPO_ROOT / "data" / "processed" / "scotus_cases.jsonl"


def main() -> None:
    print("=" * 70)
    print("CORPUS STATS")
    print("=" * 70)

    cases = []
    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    n_cases = len(cases)
    print(f"Total cases in corpus: {n_cases:,}")

    # Dates come in two shapes: ISO (CAP: "1978-05-31") and US (LII/SCDB: "6/29/2023").
    # Normalize each to ISO before min/max.
    import pandas as pd  # noqa: PLC0415

    def _to_iso(s: str) -> str | None:
        if not s:
            return None
        # ISO first
        try:
            return pd.Timestamp(s).date().isoformat()
        except Exception:
            pass
        # US format M/D/YYYY
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                return pd.to_datetime(s, format=fmt).date().isoformat()
            except Exception:
                continue
        return None

    iso_dates = [_to_iso(c.get("decision_date", "")) for c in cases]
    iso_dates = sorted(d for d in iso_dates if d)
    if iso_dates:
        print(f"Date range: {iso_dates[0]}  ..  {iso_dates[-1]}")

    sources = Counter(c.get("source", "?") for c in cases)
    print(f"By source: {dict(sources)}")

    issue_counter = Counter(c.get("issue_area", "Unspecified") for c in cases)
    print("\nTop 10 issue areas:")
    for label, n in issue_counter.most_common(10):
        print(f"  {n:>5}  {label}")

    print("\n" + "=" * 70)
    print("CHROMA INDEX STATS")
    print("=" * 70)
    # Touch the retriever's underlying collection to get a count
    from backend.app.services.retriever import _get_collection  # noqa: PLC0415
    coll = _get_collection()
    print(f"Collection: {coll.name}")
    print(f"Total chunks: {coll.count():,}")

    print("\n" + "=" * 70)
    print("SAMPLE RETRIEVAL 1: 'Fourth Amendment search and seizure'")
    print("=" * 70)
    for r in retrieve("Fourth Amendment search and seizure", top_k=3):
        snippet = r["text"][:240].replace("\n", " ")
        print(f"\n  case_name : {r['case_name']}")
        print(f"  date      : {r['decision_date']}")
        print(f"  us_cite   : {r['us_cite']}")
        print(f"  issue     : {r['issue_area']}")
        print(f"  score     : {r['similarity_score']:.4f}")
        print(f"  snippet   : {snippet}...")

    print("\n" + "=" * 70)
    print("SAMPLE RETRIEVAL 2: 'affirmative action in higher education'")
    print("=" * 70)
    for r in retrieve("affirmative action in higher education", top_k=3):
        snippet = r["text"][:240].replace("\n", " ")
        print(f"\n  case_name : {r['case_name']}")
        print(f"  date      : {r['decision_date']}")
        print(f"  us_cite   : {r['us_cite']}")
        print(f"  issue     : {r['issue_area']}")
        print(f"  score     : {r['similarity_score']:.4f}")
        print(f"  snippet   : {snippet}...")


if __name__ == "__main__":
    main()
