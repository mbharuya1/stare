"""Append-only JSONL query logger for Stare.

One line per agent invocation, written to ``data/query_log.jsonl``.
Self-contained: no imports from src.agent / src.evaluate, so it can be
called from anywhere (including the Streamlit app) without circulars.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = PROJECT_ROOT / "data" / "query_log.jsonl"

# Per-1M-token prices (snapshot 2026). Duplicated from src/evaluate.py so
# this module stays standalone. Keep the two in sync if pricing changes.
PRICES = {
    "haiku":  {"input": 1.00, "output": 5.00},   # claude-haiku-4-5
    "sonnet": {"input": 3.00, "output": 15.00},  # claude-sonnet-4-5
}


def _estimate_cost(usage: dict) -> float:
    return (
        usage.get("haiku_input", 0)   / 1_000_000 * PRICES["haiku"]["input"]
        + usage.get("haiku_output", 0)  / 1_000_000 * PRICES["haiku"]["output"]
        + usage.get("sonnet_input", 0)  / 1_000_000 * PRICES["sonnet"]["input"]
        + usage.get("sonnet_output", 0) / 1_000_000 * PRICES["sonnet"]["output"]
    )


def _utc_now_iso() -> str:
    # Trailing 'Z' for UTC; strip microseconds for readability.
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def log_query(state: dict, latency_ms: int) -> None:
    """Append one structured line describing this agent invocation.

    Never raises into the caller. Logging failure must not break the UI.
    """
    try:
        chunks = state.get("retrieved_chunks") or []
        retrieved_cases = [
            (c.get("case_name") or "").strip() for c in chunks if c.get("case_name")
        ]
        top_sim = float(chunks[0]["similarity_score"]) if chunks else None
        usage = state.get("usage") or {}
        route = state.get("route_taken") or []

        record = {
            "timestamp":          _utc_now_iso(),
            "question":           state.get("question") or "",
            "route_taken":        route[-1] if route else "",
            "classification":     state.get("classification") or "",
            "top_similarity":     top_sim,
            "retrieved_cases":    retrieved_cases,
            "answer":             state.get("answer") or "",
            "cited_cases":        state.get("cited_cases") or [],
            "estimated_cost_usd": round(_estimate_cost(usage), 6),
            "latency_ms":         int(latency_ms),
        }

        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        # Logging is best-effort. Swallow to keep the user-facing flow alive.
        pass


def read_log_stats() -> dict:
    """Return ``{"count": int, "last_ts": str | None}`` for the sidebar.

    Reads the whole file (small: one JSONL line per query). Returns
    zeros if the file is missing or unreadable.
    """
    try:
        if not LOG_PATH.exists():
            return {"count": 0, "last_ts": None}
        count = 0
        last_ts: str | None = None
        with LOG_PATH.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                count += 1
                try:
                    rec = json.loads(line)
                    ts = rec.get("timestamp")
                    if ts:
                        last_ts = ts
                except json.JSONDecodeError:
                    continue
        return {"count": count, "last_ts": last_ts}
    except Exception:
        return {"count": 0, "last_ts": None}


def humanize_ago(iso_ts: str | None) -> str:
    """Render an ISO timestamp as a short relative phrase (e.g. ``3 min ago``)."""
    if not iso_ts:
        return "--"
    try:
        ts = iso_ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        delta = datetime.now(timezone.utc) - dt
        secs = int(delta.total_seconds())
        if secs < 5:
            return "just now"
        if secs < 60:
            return f"{secs}s ago"
        if secs < 3600:
            return f"{secs // 60} min ago"
        if secs < 86400:
            return f"{secs // 3600} hr ago"
        return f"{secs // 86400}d ago"
    except Exception:
        return "--"
