"""Evaluation harness with programmatic metrics, no LLM-as-judge.

Loads eval/test_questions.json, runs each through ``run_agent()`` once, and
records:
    - actual_route vs expected_route (classification accuracy)
    - keyword overlap (fraction of expected keywords appearing in the answer)
    - top-1 similarity (for legal questions that retrieved chunks)
    - per-question cost (from the agent's usage tracker)

Skips RAGAS because running an LLM judge on every metric is too expensive.
The metrics here are crude but honest and testify to real behavior.

Run from the project root:
    python -m src.evaluate
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from src.agent import run_agent

LOG = logging.getLogger("evaluate")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = PROJECT_ROOT / "eval"
TEST_FILE = EVAL_DIR / "test_questions.json"
RESULTS_MD = EVAL_DIR / "results.md"
RESULTS_JSON = EVAL_DIR / "results.json"

# Per-1M-token prices (snapshot 2026).
PRICES = {
    "haiku":  {"input": 1.00, "output": 5.00},   # claude-haiku-4-5
    "sonnet": {"input": 3.00, "output": 15.00},  # claude-sonnet-4-5
}


def _estimate_cost(usage: dict) -> float:
    return (
        usage.get("haiku_input", 0)  / 1_000_000 * PRICES["haiku"]["input"]
        + usage.get("haiku_output", 0)  / 1_000_000 * PRICES["haiku"]["output"]
        + usage.get("sonnet_input", 0) / 1_000_000 * PRICES["sonnet"]["input"]
        + usage.get("sonnet_output", 0) / 1_000_000 * PRICES["sonnet"]["output"]
    )


def _keyword_overlap(answer: str, keywords: list[str]) -> float:
    """Fraction of expected keywords found in the answer (case-insensitive)."""
    if not keywords:
        return 1.0
    a = (answer or "").lower()
    hits = sum(1 for kw in keywords if kw.lower() in a)
    return hits / len(keywords)


def _evaluate_one(test_case: dict) -> dict:
    q = test_case["question"]
    LOG.info("-> %s: %s", test_case["id"], q[:80])
    result = run_agent(q)

    actual_route = result.get("classification") or ""
    expected_route = test_case["expected_route"]
    answer = result.get("answer") or ""
    chunks = result.get("retrieved_chunks") or []
    top_sim = float(chunks[0]["similarity_score"]) if chunks else None
    usage = result.get("usage") or {}

    return {
        "id": test_case["id"],
        "question": q,
        "notes": test_case.get("notes", ""),
        "expected_route": expected_route,
        "actual_route": actual_route,
        "route_match": actual_route == expected_route,
        "expected_keywords": test_case.get("expected_answer_keywords") or [],
        "keyword_overlap": _keyword_overlap(
            answer, test_case.get("expected_answer_keywords") or []
        ),
        "top_similarity": top_sim,
        "answer": answer,
        "cited_cases": result.get("cited_cases") or [],
        "route_taken": result.get("route_taken") or [],
        "usage": usage,
        "cost_usd": _estimate_cost(usage),
    }


def _summarize(records: list[dict]) -> dict:
    n = len(records)
    n_correct = sum(1 for r in records if r["route_match"])
    legal_with_sim = [
        r for r in records
        if r["expected_route"] == "legal_question" and r["top_similarity"] is not None
    ]
    return {
        "n": n,
        "route_correct": n_correct,
        "route_accuracy": (n_correct / n) if n else 0.0,
        "mean_keyword_overlap": (
            sum(r["keyword_overlap"] for r in records) / n if n else 0.0
        ),
        "legal_n": len(legal_with_sim),
        "mean_top_sim_legal": (
            sum(r["top_similarity"] for r in legal_with_sim) / len(legal_with_sim)
            if legal_with_sim else 0.0
        ),
        "total_cost": sum(r["cost_usd"] for r in records),
    }


def _clean_prose(s: str) -> str:
    """Normalize em/en-dashes and ellipsis in display strings.

    Lets us pull notes verbatim from test_questions.json (a data file we
    do not edit) while still producing plain-ASCII headings in results.md.
    """
    return (
        (s or "")
        .replace(" — ", ", ")
        .replace("—", ", ")
        .replace("–", " to ")
        .replace("…", "...")
    )


def _quote_block(text: str) -> str:
    """Markdown blockquote: prefix every line with '> '."""
    if not text.strip():
        return "> _(empty)_"
    return "\n".join(f"> {line}" if line else ">" for line in text.split("\n"))


def _write_results_md(records: list[dict], summary: dict) -> None:
    lines: list[str] = []
    lines.append("# Evaluation results")
    lines.append("")
    lines.append(
        f"_{summary['n']} hand-crafted test questions, each run once through "
        f"`run_agent()`. All metrics are programmatic, no LLM-as-judge._"
    )
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(
        f"| Route classification accuracy | "
        f"**{summary['route_accuracy']:.0%}** "
        f"({summary['route_correct']}/{summary['n']}) |"
    )
    lines.append(
        f"| Mean keyword overlap | **{summary['mean_keyword_overlap']:.2f}** |"
    )
    if summary["legal_n"]:
        lines.append(
            f"| Mean top-1 similarity (legal Qs, n={summary['legal_n']}) | "
            f"**{summary['mean_top_sim_legal']:.3f}** |"
        )
    lines.append(f"| Total estimated cost | **${summary['total_cost']:.4f}** |")
    lines.append("")

    # Per-question table
    lines.append("## Per-question results")
    lines.append("")
    lines.append("| ID | Expected route | Actual route | Match | Top-1 sim | KW overlap | Cost |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in records:
        ok = "yes" if r["route_match"] else "no"
        sim = f"{r['top_similarity']:.3f}" if r["top_similarity"] is not None else "--"
        lines.append(
            f"| `{r['id']}` | `{r['expected_route']}` | `{r['actual_route']}` | "
            f"{ok} | {sim} | {r['keyword_overlap']:.2f} | "
            f"${r['cost_usd']:.4f} |"
        )
    lines.append("")

    # Per-question detail
    lines.append("## Per-question details")
    lines.append("")
    for r in records:
        lines.append(f"### {r['id']}: {_clean_prose(r['notes'])}")
        lines.append("")
        lines.append(f"**Question:** {r['question']}")
        lines.append("")
        lines.append(f"**Route taken:** `{' -> '.join(r['route_taken'])}`")
        lines.append("")
        lines.append(
            "**Expected keywords:** "
            + ", ".join(f"`{k}`" for k in r["expected_keywords"])
            + f". **{r['keyword_overlap']:.0%}** matched"
        )
        lines.append("")
        lines.append("**Answer:**")
        lines.append("")
        lines.append(_quote_block(r["answer"]))
        lines.append("")
        if r["cited_cases"]:
            lines.append(
                "**Cited cases:** "
                + ", ".join(f"`{c}`" for c in r["cited_cases"])
            )
            lines.append("")

    RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    if not TEST_FILE.exists():
        LOG.error("Test file not found: %s", TEST_FILE)
        return 1

    test_cases = json.loads(TEST_FILE.read_text(encoding="utf-8"))
    LOG.info("Loaded %d test questions", len(test_cases))

    records = [_evaluate_one(tc) for tc in test_cases]
    summary = _summarize(records)

    _write_results_md(records, summary)
    RESULTS_JSON.write_text(
        json.dumps(
            {"summary": summary, "records": records},
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    print(
        f"Route accuracy        : "
        f"{summary['route_correct']}/{summary['n']} "
        f"= {summary['route_accuracy']:.0%}"
    )
    print(f"Mean keyword overlap  : {summary['mean_keyword_overlap']:.2f}")
    if summary["legal_n"]:
        print(
            f"Mean top-1 similarity : "
            f"{summary['mean_top_sim_legal']:.3f}  "
            f"(over {summary['legal_n']} legal Qs)"
        )
    print(f"Total estimated cost  : ${summary['total_cost']:.4f}")
    print()
    print(f"  -> {RESULTS_MD.relative_to(PROJECT_ROOT)}")
    print(f"  -> {RESULTS_JSON.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
