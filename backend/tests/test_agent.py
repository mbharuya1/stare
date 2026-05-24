"""Agent unit tests. All Anthropic and ChromaDB calls are mocked — no API spend."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from backend.app.services import agent as agent_mod
from backend.app.services.generator import verify_citations


# ─────────────────────── helpers ───────────────────────

def _mock_anthropic_response(text: str, in_tok: int = 50, out_tok: int = 5, model: str = "claude-haiku-4-5-20251001"):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=in_tok, output_tokens=out_tok),
        model=model,
    )


SAMPLE_CHUNKS = [
    {
        "case_id": "2000-075",
        "case_name": "Saucier v. Katz",
        "us_cite": "533 U.S. 194",
        "decision_date": "2001-06-18",
        "issue_area": "Civil Rights",
        "rerank_score": 0.92,
        "vector_similarity": 0.75,
        "text": "Qualified immunity is an entitlement not to stand trial...",
        "chunk_index": 0,
    },
    {
        "case_id": "1973-053",
        "case_name": "Miller v. California",
        "us_cite": "413 U.S. 15",
        "decision_date": "1973-06-21",
        "issue_area": "First Amendment",
        "rerank_score": 0.88,
        "vector_similarity": 0.72,
        "text": "Obscenity standards: the basic guidelines for the trier of fact...",
        "chunk_index": 0,
    },
]


# ─────────────────────── classifier ───────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("legal_question",  "legal_question"),
    ("LEGAL_QUESTION",  "legal_question"),   # case normalized
    ("out_of_scope",    "out_of_scope"),
    ("meta_question",   "meta_question"),
    ("garbage answer",  "out_of_scope"),     # invalid → safe default
    ("",                "out_of_scope"),     # empty → safe default
])
def test_classifier_returns_valid_label(raw, expected):
    fake_client = SimpleNamespace(
        messages=SimpleNamespace(
            create=lambda **kw: _mock_anthropic_response(raw, in_tok=42, out_tok=3)
        )
    )
    with patch.object(agent_mod, "_get_client", return_value=fake_client):
        result = agent_mod.classify_node({"query": "anything"})
    assert result["classification"] == expected
    assert result["input_tokens"] == 42
    assert result["output_tokens"] == 3
    assert result["cost_estimate_usd"] > 0


# ─────────────────────── citation verifier ───────────────────────

def test_verify_citations_keeps_real_and_drops_fake():
    answer = (
        "The standard comes from [Saucier v. Katz, 533 U.S. 194 (2001)] "
        "and the obscenity test is [Miller v. California, 413 U.S. 15 (1973)]. "
        "Some unrelated point cites [Smith v. Bogus, 999 U.S. 1 (1999)]."
    )
    verified, dropped = verify_citations(answer, SAMPLE_CHUNKS)
    cited_names = {c.case_name for c in verified}
    assert "Saucier v. Katz" in cited_names
    assert "Miller v. California" in cited_names
    assert len(verified) == 2
    assert len(dropped) == 1
    assert "Smith v. Bogus" in dropped[0]


def test_verify_citations_handles_spacing_variants():
    answer = "See [Saucier v. Katz, 533 U. S. 194 (2001)] and [Miller v. California, 413 US 15 (1973)]."
    verified, dropped = verify_citations(answer, SAMPLE_CHUNKS)
    assert len(verified) == 2
    assert dropped == []


def test_verify_citations_dedupes_repeated_citations():
    answer = (
        "[Saucier v. Katz, 533 U.S. 194 (2001)] established the test. "
        "Again, [Saucier v. Katz, 533 U.S. 194 (2001)] held that..."
    )
    verified, _ = verify_citations(answer, SAMPLE_CHUNKS)
    assert len(verified) == 1


def test_verify_citations_with_empty_input():
    verified, dropped = verify_citations("", SAMPLE_CHUNKS)
    assert verified == [] and dropped == []
    verified, dropped = verify_citations("[Smith v. Bogus, 999 U.S. 1 (1999)]", [])
    assert verified == [] and len(dropped) == 1


# ─────────────────────── refusal threshold ───────────────────────

def test_route_after_retrieve_below_threshold_refuses():
    # threshold default is 0.3
    state = {"max_rerank_score": 0.29}
    assert agent_mod.route_after_retrieve(state) == "refuse_low_confidence"


def test_route_after_retrieve_at_threshold_proceeds():
    state = {"max_rerank_score": 0.3}
    assert agent_mod.route_after_retrieve(state) == "generate_legal_answer"


def test_route_after_retrieve_high_score_proceeds():
    state = {"max_rerank_score": 0.97}
    assert agent_mod.route_after_retrieve(state) == "generate_legal_answer"


def test_route_after_retrieve_missing_score_refuses():
    # safe default — missing score is treated as 0.0
    assert agent_mod.route_after_retrieve({}) == "refuse_low_confidence"


# ─────────────────────── classify routing ───────────────────────

@pytest.mark.parametrize("label,expected", [
    ("legal_question", "retrieve_and_rerank"),
    ("meta_question",  "generate_meta_answer"),
    ("low_confidence", "refuse_low_confidence"),
    ("out_of_scope",   "refuse_out_of_scope"),
])
def test_route_after_classify(label, expected):
    assert agent_mod.route_after_classify({"classification": label}) == expected
