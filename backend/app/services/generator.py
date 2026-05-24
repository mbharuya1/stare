"""Generate cited legal answers from reranked chunks.

Workflow:
1. Format chunks into a numbered list with case metadata.
2. Call Claude with the legal-answer system prompt.
3. Extract every [Case Name, US Cite (Year)] citation from the response.
4. Verify each cited case appears in the retrieved chunks. Drop the rest.
5. Return {"answer", "citations", "dropped_citations", "model", "usage",
   "cost_estimate_usd"}.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Sequence

import anthropic
from pydantic import BaseModel

from backend.app.config import settings

LOG = logging.getLogger("generator")

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "legal_answer.txt"

# Pricing snapshot (per 1M tokens) — keep in sync if you change models.
PRICES = {
    "claude-sonnet-4-6":          {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5-20251001":  {"input": 1.00, "output": 5.00},
    "claude-opus-4-7":            {"input": 15.00, "output": 75.00},
}

# [Case Name v. Other, 533 U.S. 194 (2001)]  — tolerates "U.S." / "U. S." / "US"
CITATION_RE = re.compile(
    r"\[([^\[\]]+?),\s*(\d+)\s*U\.?\s*S\.?\s*(\d+)\s*\((\d{4})\)\]"
)


class Citation(BaseModel):
    case_id: str
    case_name: str
    us_cite: str
    decision_date: str
    quoted_text: str = ""


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _format_excerpts(chunks: Sequence[dict]) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        year = (c.get("decision_date") or "")[:4]
        lines.append(
            f"[{i}] {c.get('case_name','?')}, {c.get('us_cite','?')} ({year})\n"
            f"    issue area: {c.get('issue_area','Unspecified')}\n"
            f"    excerpt: {c.get('text','').strip()}"
        )
    return "\n\n".join(lines)


def _norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def verify_citations(
    answer: str, chunks: Sequence[dict]
) -> tuple[list[Citation], list[str]]:
    """Pull every [Case, X U.S. Y (Year)] and confirm it's in ``chunks``.

    Matches on US cite first (most reliable), falling back to case-name match.
    Returns (verified, dropped_raw_citations).
    """
    by_cite: dict[str, dict] = {}
    for c in chunks:
        if c.get("us_cite"):
            by_cite[c["us_cite"].replace(" ", "").lower()] = c
    by_name: dict[str, dict] = {_norm_name(c.get("case_name", "")): c for c in chunks}

    verified: list[Citation] = []
    dropped: list[str] = []
    seen: set[str] = set()
    for m in CITATION_RE.finditer(answer):
        case_name, vol, page, year = m.group(1, 2, 3, 4)
        raw = m.group(0)
        cite_key = f"{vol}u.s.{page}"
        chunk = by_cite.get(cite_key) or by_name.get(_norm_name(case_name))
        if chunk is None:
            dropped.append(raw)
            continue
        cid = str(chunk.get("case_id") or raw)
        if cid in seen:
            continue
        seen.add(cid)
        verified.append(
            Citation(
                case_id=cid,
                case_name=chunk.get("case_name", case_name),
                us_cite=chunk.get("us_cite", f"{vol} U.S. {page}"),
                decision_date=chunk.get("decision_date", year),
                quoted_text=(chunk.get("text", "") or "")[:400],
            )
        )
    return verified, dropped


def _estimate_cost_usd(model: str, in_tokens: int, out_tokens: int) -> float:
    p = PRICES.get(model)
    if not p:
        return 0.0
    return in_tokens / 1_000_000 * p["input"] + out_tokens / 1_000_000 * p["output"]


def generate(
    query: str,
    chunks: Sequence[dict],
    model: str | None = None,
    max_tokens: int = 800,
) -> dict:
    """Generate a cited answer using only ``chunks``."""
    if not chunks:
        return {
            "answer": "I couldn't find relevant case law in my corpus to answer that.",
            "citations": [],
            "dropped_citations": [],
            "model": "",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "cost_estimate_usd": 0.0,
        }

    model = model or settings.generator_model
    system = _load_system_prompt()
    user_msg = (
        f"QUESTION:\n{query}\n\n"
        f"EXCERPTS:\n{_format_excerpts(chunks)}\n\n"
        f"Now answer the question using only the excerpts above. "
        f"Cite each claim as [Case Name, US Cite (Year)]."
    )

    client = _get_client()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    answer_text = "".join(
        b.text for b in resp.content if getattr(b, "type", "") == "text"
    )
    verified, dropped = verify_citations(answer_text, chunks)
    if dropped:
        answer_text = answer_text.rstrip() + (
            f"\n\n_Note: {len(dropped)} unverifiable citation"
            f"{'s' if len(dropped) != 1 else ''} were removed from this answer "
            f"because they did not appear in the retrieved excerpts._"
        )

    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }
    cost = _estimate_cost_usd(resp.model, usage["input_tokens"], usage["output_tokens"])
    LOG.info(
        "generated: %d in / %d out (~$%.5f) verified=%d dropped=%d",
        usage["input_tokens"], usage["output_tokens"], cost, len(verified), len(dropped),
    )
    return {
        "answer": answer_text,
        "citations": [c.model_dump() for c in verified],
        "dropped_citations": dropped,
        "model": resp.model,
        "usage": usage,
        "cost_estimate_usd": cost,
    }
