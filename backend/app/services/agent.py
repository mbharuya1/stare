"""Stare v2 — LangGraph router and orchestrator.

States:
    classify              → Claude haiku, returns one of 4 labels
    retrieve_and_rerank   → vector top-20 → cross-encoder top-5
    generate_legal_answer → Claude sonnet, cited answer
    generate_meta_answer  → deterministic, answers questions about the system
    refuse_out_of_scope   → polite canned refusal
    refuse_low_confidence → "not confident enough" refusal
    finalize              → assemble the response object

Routing:
    classify decides legal_question | out_of_scope | meta_question | low_confidence
    After retrieve_and_rerank: if max rerank_score < low_confidence_threshold,
    override to refuse_low_confidence regardless of original classification.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Annotated, Literal, TypedDict

import anthropic
from langgraph.graph import END, StateGraph

from backend.app.config import settings
from backend.app.services.generator import _estimate_cost_usd, generate
from backend.app.services.retriever import retrieve

LOG = logging.getLogger("agent")

Classification = Literal["legal_question", "out_of_scope", "meta_question", "low_confidence"]
VALID_LABELS: set[str] = {"legal_question", "out_of_scope", "meta_question"}

CLASSIFIER_SYSTEM = (
    "You classify user questions about U.S. Supreme Court law. "
    "Respond with EXACTLY ONE of these labels, lowercase, no punctuation, "
    "no explanation:\n"
    "  legal_question   — the user is asking about U.S. Supreme Court doctrine, "
    "cases, constitutional law, or how the Court has ruled.\n"
    "  out_of_scope     — not a legal question (e.g., cooking, code, geography, "
    "general chit-chat, non-U.S. law).\n"
    "  meta_question    — the user is asking about THIS system (how many cases "
    "you have, what years you cover, what your data source is, etc.).\n"
    "Output only the label."
)


def _accumulate_chunks(left: list[dict] | None, right: list[dict] | None) -> list[dict]:
    """LangGraph reducer for list[dict] fields — replace on update."""
    if right is not None:
        return right
    return left or []


def _add_cost(left: float | None, right: float | None) -> float:
    if right is None:
        return left or 0.0
    return (left or 0.0) + right


def _add_int(left: int | None, right: int | None) -> int:
    if right is None:
        return left or 0
    return (left or 0) + right


class AgentState(TypedDict, total=False):
    query: str
    classification: Classification
    chunks: Annotated[list[dict], _accumulate_chunks]
    max_rerank_score: float
    answer: str
    citations: list[dict]
    dropped_citations: list[str]
    model_used: str
    cost_estimate_usd: Annotated[float, _add_cost]
    input_tokens: Annotated[int, _add_int]
    output_tokens: Annotated[int, _add_int]


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


# ─────────────────────── node implementations ───────────────────────

def classify_node(state: AgentState) -> dict:
    """Single haiku call to label the query."""
    client = _get_client()
    resp = client.messages.create(
        model=settings.classifier_model,
        max_tokens=10,
        system=CLASSIFIER_SYSTEM,
        messages=[{"role": "user", "content": state["query"]}],
    )
    raw = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip().lower()
    label: Classification = raw if raw in VALID_LABELS else "out_of_scope"  # type: ignore[assignment]
    cost = _estimate_cost_usd(resp.model, resp.usage.input_tokens, resp.usage.output_tokens)
    LOG.info("classify: raw=%r → label=%s  cost=$%.5f", raw, label, cost)
    return {
        "classification": label,
        "cost_estimate_usd": cost,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "model_used": resp.model,
    }


def retrieve_and_rerank_node(state: AgentState) -> dict:
    chunks = retrieve(state["query"])
    max_score = max((c.get("rerank_score", 0.0) for c in chunks), default=0.0)
    LOG.info("retrieved %d chunks; max rerank_score=%.3f", len(chunks), max_score)
    return {"chunks": chunks, "max_rerank_score": max_score}


def generate_legal_answer_node(state: AgentState) -> dict:
    result = generate(state["query"], state.get("chunks", []))
    return {
        "answer": result["answer"],
        "citations": result["citations"],
        "dropped_citations": result["dropped_citations"],
        "cost_estimate_usd": result["cost_estimate_usd"],
        "input_tokens": result["usage"]["input_tokens"],
        "output_tokens": result["usage"]["output_tokens"],
        "model_used": result["model"] or settings.generator_model,
    }


def generate_meta_answer_node(state: AgentState) -> dict:
    """Answer questions about Stare itself. No LLM call — deterministic."""
    from backend.app.services.retriever import _get_collection  # noqa: PLC0415
    coll = _get_collection()
    answer = (
        "I'm Stare, a research assistant for U.S. Supreme Court law.\n\n"
        f"• Corpus: 9,068 SCOTUS opinions from 1946-11-18 through 2025-06-30.\n"
        f"• Index: {coll.count():,} text chunks in a ChromaDB collection "
        f"({settings.chroma_collection!r}, all-MiniLM-L6-v2 embeddings).\n"
        f"• Sources: Caselaw Access Project (Harvard) for 1946–2014, "
        f"supplemented by Cornell LII for 2015–2025. Metadata from the "
        f"Supreme Court Database (Penn State, release 2025_01).\n"
        f"• Retrieval: top-20 vector recall, reranked with a "
        f"cross-encoder ({settings.reranker_model!r}) to top-{settings.rerank_top_k}.\n"
        f"• Generation: {settings.generator_model}."
    )
    return {"answer": answer, "citations": [], "dropped_citations": []}


def refuse_out_of_scope_node(state: AgentState) -> dict:
    return {
        "answer": (
            "I only answer questions about U.S. Supreme Court law. "
            "Try asking about a constitutional doctrine, a specific case, "
            "or how the Court has ruled on a legal issue."
        ),
        "citations": [],
        "dropped_citations": [],
    }


def refuse_low_confidence_node(state: AgentState) -> dict:
    return {
        "answer": (
            "I don't have enough relevant case law in my corpus to answer "
            "that confidently. Rather than guess, I'd rather decline. "
            "If you can rephrase the question with a specific legal issue "
            "or case name, I may be able to help."
        ),
        "citations": [],
        "dropped_citations": [],
    }


def finalize_node(state: AgentState) -> dict:
    # Pass-through; the StateGraph entry point gathers the final state.
    return {}


# ─────────────────────── routing ───────────────────────

def route_after_classify(state: AgentState) -> str:
    label = state.get("classification")
    if label == "legal_question":
        return "retrieve_and_rerank"
    if label == "meta_question":
        return "generate_meta_answer"
    if label == "low_confidence":
        return "refuse_low_confidence"
    return "refuse_out_of_scope"


def route_after_retrieve(state: AgentState) -> str:
    if state.get("max_rerank_score", 0.0) < settings.low_confidence_threshold:
        return "refuse_low_confidence"
    return "generate_legal_answer"


# ─────────────────────── graph build ───────────────────────

_compiled = None


def _build_graph():
    global _compiled
    if _compiled is not None:
        return _compiled
    g = StateGraph(AgentState)
    g.add_node("classify", classify_node)
    g.add_node("retrieve_and_rerank", retrieve_and_rerank_node)
    g.add_node("generate_legal_answer", generate_legal_answer_node)
    g.add_node("generate_meta_answer", generate_meta_answer_node)
    g.add_node("refuse_out_of_scope", refuse_out_of_scope_node)
    g.add_node("refuse_low_confidence", refuse_low_confidence_node)
    g.add_node("finalize", finalize_node)

    g.set_entry_point("classify")
    g.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "retrieve_and_rerank": "retrieve_and_rerank",
            "generate_meta_answer": "generate_meta_answer",
            "refuse_out_of_scope": "refuse_out_of_scope",
            "refuse_low_confidence": "refuse_low_confidence",
        },
    )
    g.add_conditional_edges(
        "retrieve_and_rerank",
        route_after_retrieve,
        {
            "generate_legal_answer": "generate_legal_answer",
            "refuse_low_confidence": "refuse_low_confidence",
        },
    )
    g.add_edge("generate_legal_answer", "finalize")
    g.add_edge("generate_meta_answer", "finalize")
    g.add_edge("refuse_out_of_scope", "finalize")
    g.add_edge("refuse_low_confidence", "finalize")
    g.add_edge("finalize", END)

    _compiled = g.compile()
    return _compiled


def run_agent(query: str) -> dict:
    """Run the agent end to end. Returns the response shape used by /query."""
    t0 = time.time()
    graph = _build_graph()
    state: AgentState = {"query": query}
    out = graph.invoke(state)
    latency_ms = int((time.time() - t0) * 1000)

    chunks_out = []
    for c in out.get("chunks") or []:
        chunks_out.append({
            "case_id": c.get("case_id", ""),
            "case_name": c.get("case_name", ""),
            "us_cite": c.get("us_cite", ""),
            "decision_date": c.get("decision_date", ""),
            "rerank_score": float(c.get("rerank_score", 0.0)),
            "vector_similarity": float(c.get("vector_similarity", 0.0)),
            "text_excerpt": (c.get("text") or "")[:400],
        })

    return {
        "query": query,
        "classification": out.get("classification", "out_of_scope"),
        "answer": out.get("answer", ""),
        "citations": out.get("citations") or [],
        "dropped_citations": out.get("dropped_citations") or [],
        "retrieval": {
            "chunks": chunks_out,
            "max_rerank_score": float(out.get("max_rerank_score") or 0.0),
        },
        "metadata": {
            "latency_ms": latency_ms,
            "model": out.get("model_used", ""),
            "cost_estimate_usd": float(out.get("cost_estimate_usd") or 0.0),
            "input_tokens": int(out.get("input_tokens") or 0),
            "output_tokens": int(out.get("output_tokens") or 0),
        },
    }


def to_json(query: str) -> str:
    return json.dumps(run_agent(query), indent=2, default=str)
