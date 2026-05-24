"""Smoke test for the LangGraph agent.

Three questions, one per route. Prints route_taken, answer, and an
estimated cost for each question + a total at the end.

Pricing snapshot (per 1M tokens):
    claude-haiku-4-5  : $1.00 input / $5.00 output
    claude-sonnet-4-5 : $3.00 input / $15.00 output
"""
from __future__ import annotations

import logging
import sys

from src.agent import run_agent

PRICES = {
    "haiku":  {"input": 1.00, "output": 5.00},
    "sonnet": {"input": 3.00, "output": 15.00},
}

QUESTIONS = [
    ("legal",        "What did the court rule on warrantless searches?"),
    ("out_of_scope", "What's the weather in Boston?"),
    ("meta",         "How many cases do you have access to?"),
]


def estimate_cost(usage: dict) -> float:
    h_in  = usage.get("haiku_input", 0)
    h_out = usage.get("haiku_output", 0)
    s_in  = usage.get("sonnet_input", 0)
    s_out = usage.get("sonnet_output", 0)
    return (
        h_in  / 1_000_000 * PRICES["haiku"]["input"]
        + h_out / 1_000_000 * PRICES["haiku"]["output"]
        + s_in  / 1_000_000 * PRICES["sonnet"]["input"]
        + s_out / 1_000_000 * PRICES["sonnet"]["output"]
    )


def main() -> int:
    logging.basicConfig(
        level=logging.WARNING, format="%(levelname)s %(name)s — %(message)s"
    )

    total = {"haiku_input": 0, "haiku_output": 0, "sonnet_input": 0, "sonnet_output": 0}

    for label, question in QUESTIONS:
        print()
        print("=" * 90)
        print(f"[expected route: {label}] {question}")
        print("=" * 90)

        result = run_agent(question)

        route = " → ".join(result["route_taken"])
        print(f"Route taken      : {route}")
        print(f"Classification   : {result['classification']}")
        if result["confidence_score"]:
            print(f"Top-1 similarity : {result['confidence_score']:.3f}")
        print(f"\nAnswer:\n{result['answer']}")

        if result["cited_cases"]:
            print(f"\nCited cases ({len(result['cited_cases'])}):")
            for c in result["cited_cases"]:
                print(f"  - {c}")

        usage = result.get("usage") or {}
        cost = estimate_cost(usage)
        print(f"\nTokens: {usage}")
        print(f"Cost  : ${cost:.4f}")

        for k in total:
            total[k] += usage.get(k, 0)

    print()
    print("=" * 90)
    print("TOTAL across 3 questions")
    print("=" * 90)
    print(f"Tokens: {total}")
    print(f"Estimated cost: ${estimate_cost(total):.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
