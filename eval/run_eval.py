"""Run the Stare-v2 eval suite end to end.

Iterates eval/test_questions.jsonl, invokes the agent directly (no HTTP server
needed), computes routing/precision/grounding/refusal metrics, writes
eval/results.json + results.md, and logs to MLflow.

Usage:
    python -m eval.run_eval                       # uses settings.use_reranker
    python -m eval.run_eval --no-reranker         # forces USE_RERANKER=false
    python -m eval.run_eval --reranker            # forces USE_RERANKER=true
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import mlflow

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PATH = REPO_ROOT / "eval" / "test_questions.jsonl"
RESULTS_JSON = REPO_ROOT / "eval" / "results.json"
RESULTS_MD = REPO_ROOT / "eval" / "results.md"
MLFLOW_DIR = REPO_ROOT / "eval" / "mlruns"


REFUSAL_CLASSIFICATIONS = {"out_of_scope", "low_confidence"}


def _load_questions() -> list[dict]:
    qs = []
    with TEST_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                qs.append(json.loads(line))
    return qs


def _names_present(retrieved: list[dict], expected: list[str]) -> tuple[bool, list[str]]:
    """Return (any_match, list_of_matched_expected_names)."""
    matched = []
    retrieved_names = [c.get("case_name", "") for c in retrieved]
    for exp in expected:
        exp_l = exp.lower()
        for rn in retrieved_names:
            if exp_l in rn.lower():
                matched.append(exp)
                break
    return (len(matched) > 0, matched)


def _classify_to_behavior(classification: str) -> str:
    if classification == "legal_question":
        return "answer"
    if classification == "meta_question":
        return "meta_response"
    return "refuse"  # out_of_scope or low_confidence


def _eval_one(q: dict, run_agent) -> dict:
    t0 = time.time()
    resp = run_agent(q["question"])
    latency_ms = int((time.time() - t0) * 1000)

    classification = resp.get("classification", "")
    actual_behavior = _classify_to_behavior(classification)
    expected_behavior = q.get("expected_behavior")
    expected_class = q.get("expected_classification", "")

    # Routing: classification matches expected, OR (for refusal cases) actual
    # behavior is refuse and expected behavior is refuse. The low_confidence
    # path is a valid refuse even when expected_classification = out_of_scope.
    routing_match = classification == expected_class or (
        expected_behavior == "refuse" and actual_behavior == "refuse"
    )

    # Precision@5: at least one expected case in the top-5 reranked chunks.
    precision_hit = None
    matched_names: list[str] = []
    if expected_behavior == "answer" and q.get("expected_case_names"):
        chunks = resp.get("retrieval", {}).get("chunks", [])
        precision_hit, matched_names = _names_present(chunks, q["expected_case_names"])

    # Citation grounding: every cited case_id appears in the retrieved chunks.
    citations = resp.get("citations", [])
    retrieved_ids = {c.get("case_id") for c in resp.get("retrieval", {}).get("chunks", [])}
    grounded = all(c.get("case_id") in retrieved_ids for c in citations) if citations else None
    dropped = len(resp.get("dropped_citations") or [])

    return {
        "id": q["id"],
        "question": q["question"],
        "expected_classification": expected_class,
        "expected_behavior": expected_behavior,
        "actual_classification": classification,
        "actual_behavior": actual_behavior,
        "routing_match": routing_match,
        "answer_preview": (resp.get("answer") or "")[:200],
        "precision_at_5": precision_hit,
        "matched_expected_cases": matched_names,
        "n_citations": len(citations),
        "n_dropped_citations": dropped,
        "citations_grounded": grounded,
        "max_rerank_score": resp.get("retrieval", {}).get("max_rerank_score"),
        "latency_ms": latency_ms,
        "cost_usd": resp.get("metadata", {}).get("cost_estimate_usd", 0.0),
        "tokens_in": resp.get("metadata", {}).get("input_tokens", 0),
        "tokens_out": resp.get("metadata", {}).get("output_tokens", 0),
    }


def _summarize(rows: list[dict]) -> dict:
    n = len(rows)
    answer_rows = [r for r in rows if r["expected_behavior"] == "answer"]
    refuse_rows = [r for r in rows if r["expected_behavior"] == "refuse"]
    cited_rows = [r for r in rows if r["citations_grounded"] is not None]

    routing_correct = sum(1 for r in rows if r["routing_match"])
    precision_hits = sum(1 for r in answer_rows if r["precision_at_5"])
    grounded = sum(1 for r in cited_rows if r["citations_grounded"])
    refusals_correct = sum(1 for r in refuse_rows if r["actual_behavior"] == "refuse")

    return {
        "total_questions": n,
        "routing_accuracy": routing_correct / n if n else 0.0,
        "precision_at_5": precision_hits / len(answer_rows) if answer_rows else 0.0,
        "citation_grounding_rate": grounded / len(cited_rows) if cited_rows else 0.0,
        "refusal_accuracy": refusals_correct / len(refuse_rows) if refuse_rows else 0.0,
        "total_cost_usd": sum(r["cost_usd"] for r in rows),
        "total_tokens_in": sum(r["tokens_in"] for r in rows),
        "total_tokens_out": sum(r["tokens_out"] for r in rows),
        "median_latency_ms": sorted(r["latency_ms"] for r in rows)[n // 2] if n else 0,
    }


def _write_markdown(summary: dict, rows: list[dict], reranker_on: bool) -> str:
    lines = [
        "# Stare-v2 Evaluation",
        "",
        f"- Timestamp: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Reranker: **{'ON' if reranker_on else 'OFF'}**",
        f"- Total questions: {summary['total_questions']}",
        "",
        "## Summary metrics",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Routing accuracy | {summary['routing_accuracy']:.1%} |",
        f"| Precision@5 (legal questions) | {summary['precision_at_5']:.1%} |",
        f"| Citation grounding rate | {summary['citation_grounding_rate']:.1%} |",
        f"| Refusal accuracy | {summary['refusal_accuracy']:.1%} |",
        f"| Total cost (USD) | ${summary['total_cost_usd']:.4f} |",
        f"| Total input tokens | {summary['total_tokens_in']:,} |",
        f"| Total output tokens | {summary['total_tokens_out']:,} |",
        f"| Median latency | {summary['median_latency_ms']} ms |",
        "",
        "## Per-question results",
        "",
        "| ID | Routing | Behavior | P@5 | Grounded | Citations | Cost |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        routing = "✓" if r["routing_match"] else "✗"
        p5 = "-" if r["precision_at_5"] is None else ("✓" if r["precision_at_5"] else "✗")
        g = "-" if r["citations_grounded"] is None else ("✓" if r["citations_grounded"] else "✗")
        lines.append(
            f"| {r['id']} | {routing} ({r['actual_classification']}) | "
            f"{r['actual_behavior']} | {p5} | {g} | "
            f"{r['n_citations']} (dropped {r['n_dropped_citations']}) | "
            f"${r['cost_usd']:.5f} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Routing match accepts either an exact classification match "
                 "or — for refusal questions — any classification that produced "
                 "a refusal behavior (out_of_scope **or** low_confidence).")
    lines.append("- Precision@5 reports whether any expected case name appeared "
                 "(case-insensitive substring) in the top-5 reranked chunks.")
    lines.append("- Citation grounding counts an answer as grounded iff every "
                 "verified citation's `case_id` is in the retrieved chunk set.")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group()
    g.add_argument("--reranker", dest="use_rr", action="store_true", default=None)
    g.add_argument("--no-reranker", dest="use_rr", action="store_false", default=None)
    args = p.parse_args()

    if args.use_rr is not None:
        os.environ["USE_RERANKER"] = "true" if args.use_rr else "false"

    # Defer import so the env var lands before settings is built.
    from backend.app.config import settings  # noqa: PLC0415
    from backend.app.services.agent import run_agent  # noqa: PLC0415

    reranker_on = settings.use_reranker
    print(f"== Stare-v2 eval ==  reranker={'ON' if reranker_on else 'OFF'}")
    print(f"   model={settings.generator_model}")
    print(f"   classifier={settings.classifier_model}")

    questions = _load_questions()
    print(f"   questions: {len(questions)}")

    mlflow.set_tracking_uri(f"file://{MLFLOW_DIR}")
    mlflow.set_experiment("stare-eval")

    rows: list[dict] = []
    with mlflow.start_run(run_name=f"eval-{'rr' if reranker_on else 'norr'}-"
                                   f"{datetime.now().strftime('%Y%m%d-%H%M%S')}") as run:
        mlflow.log_param("reranker_on", reranker_on)
        mlflow.log_param("generator_model", settings.generator_model)
        mlflow.log_param("classifier_model", settings.classifier_model)
        mlflow.log_param("low_confidence_threshold", settings.low_confidence_threshold)
        mlflow.log_param("vector_top_k", settings.vector_top_k)
        mlflow.log_param("rerank_top_k", settings.rerank_top_k)

        for i, q in enumerate(questions, 1):
            print(f"  [{i}/{len(questions)}] {q['id']}: {q['question'][:80]}")
            try:
                row = _eval_one(q, run_agent)
            except Exception as e:
                print(f"      ERROR: {e}")
                row = {
                    "id": q["id"], "question": q["question"], "error": str(e),
                    "routing_match": False, "precision_at_5": None,
                    "citations_grounded": None, "expected_behavior": q.get("expected_behavior"),
                    "actual_behavior": "error", "actual_classification": "",
                    "expected_classification": q.get("expected_classification", ""),
                    "answer_preview": "", "n_citations": 0, "n_dropped_citations": 0,
                    "matched_expected_cases": [], "max_rerank_score": 0.0,
                    "latency_ms": 0, "cost_usd": 0.0,
                    "tokens_in": 0, "tokens_out": 0,
                }
            rows.append(row)
            print(f"      → {row['actual_classification']:>16s}  "
                  f"P@5={row['precision_at_5']}  cost=${row['cost_usd']:.5f}")

        summary = _summarize(rows)
        for k, v in summary.items():
            mlflow.log_metric(k, v) if isinstance(v, (int, float)) else mlflow.log_param(k, v)

        RESULTS_JSON.write_text(json.dumps(
            {"reranker_on": reranker_on, "summary": summary, "rows": rows},
            indent=2, default=str,
        ))
        md = _write_markdown(summary, rows, reranker_on)
        RESULTS_MD.write_text(md)
        mlflow.log_artifact(str(RESULTS_JSON))
        mlflow.log_artifact(str(RESULTS_MD))

        print("\n=== SUMMARY ===")
        for k, v in summary.items():
            if isinstance(v, float):
                print(f"  {k:<28s} {v:.4f}")
            else:
                print(f"  {k:<28s} {v}")
        print(f"\nMLflow run: {run.info.run_id}")
        print(f"Wrote: {RESULTS_JSON} and {RESULTS_MD}")


if __name__ == "__main__":
    main()
