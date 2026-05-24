"""End-to-end smoke test for the retrieve → generate pipeline.

Run from the project root:
    python test_rag.py
"""
from __future__ import annotations

import logging
import sys

from src.generate import generate_answer
from src.retrieve import retrieve

QUESTIONS = [
    "What did the Supreme Court say about warrantless searches and the Fourth Amendment?",
    "How has the Court interpreted the Equal Protection Clause in cases involving race or classification?",
    "What standard does the Court apply when deciding whether speech is protected by the First Amendment?",
]


def run_one(idx: int, total: int, question: str) -> None:
    print()
    print("=" * 90)
    print(f"Q{idx}/{total}: {question}")
    print("=" * 90)

    chunks = retrieve(question, top_k=5)
    print(f"\nRetrieved {len(chunks)} chunks:")
    for c in chunks:
        score = c["similarity_score"]
        case = c["case_name"] or "(unnamed)"
        print(
            f"  [{score:+.3f}] {case[:60]:60}  "
            f"({c['year']}, chunk #{c['chunk_index']})"
        )

    result = generate_answer(question, chunks)
    print("\nAnswer:")
    print(result["answer"])

    cited = result["cited_cases"]
    print(f"\nCited cases ({len(cited)}):")
    for c in cited:
        print(f"  - {c}")


def main() -> int:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s %(name)s — %(message)s",
    )
    for i, q in enumerate(QUESTIONS, start=1):
        try:
            run_one(i, len(QUESTIONS), q)
        except Exception as exc:
            print(f"\n!! Q{i} failed: {exc}", file=sys.stderr)
            return 1
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
