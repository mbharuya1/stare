"""Stare. Streamlit UI for the Lawyer Mode of the AI Law Assistant.

Thin client that hits the FastAPI backend (POST /query) and renders the
classification-aware response. All design lives in styles.py via inject_css().
"""
from __future__ import annotations

import html
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import streamlit as st

from styles import inject_css

DEMO_MODE = os.getenv("STARE_DEMO_MODE", "").lower() in ("1", "true", "yes")
DEMO_RESPONSE_PATH = Path(__file__).parent / "_demo_response.json"

# ───────────────────────── config ─────────────────────────

BACKEND_URL = os.getenv("STARE_BACKEND_URL", "http://localhost:8000")
LANDING_URL = os.getenv("NEXT_PUBLIC_LANDING_URL", "http://localhost:3000")
GITHUB_URL = os.getenv("STARE_GITHUB_URL", "https://github.com/")

SAMPLE_QUESTIONS = [
    "What is the standard for qualified immunity?",
    "When can police search a vehicle without a warrant?",
    "What did Brown v. Board hold?",
]

CITATION_RE = re.compile(r"\[([^\[\]]+?,\s*\d+\s*U\.?\s*S\.?\s*\d+\s*\(\d{4}\))\]")

st.set_page_config(
    page_title="Stare. Lawyer Mode.",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()


# ───────────────────────── helpers ─────────────────────────

def render_header() -> None:
    st.markdown(
        f"""
        <div class="stare-header">
            <div class="wordmark-group">
                <span class="wordmark">Stare</span>
                <span class="mode-badge">Lawyer Mode</span>
            </div>
            <div class="nav-right">
                <a class="nav-link" href="{html.escape(LANDING_URL)}/about" target="_self">About</a>
                <a class="nav-link" href="{html.escape(GITHUB_URL)}" target="_blank" rel="noopener">GitHub</a>
                <a class="nav-link back-link" href="{html.escape(LANDING_URL)}" target="_self">← Back to landing</a>
            </div>
        </div>
        <div class="stare-disclaimer">
            Research and portfolio project. Not legal advice. Not for use in legal practice.
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=15, show_spinner=False)
def backend_health() -> tuple[bool, dict | str]:
    if DEMO_MODE:
        return True, {"status": "ok (demo)", "demo_mode": True}
    try:
        r = httpx.get(f"{BACKEND_URL}/health", timeout=3.0)
        r.raise_for_status()
        return True, r.json()
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def render_backend_error(detail: str) -> None:
    st.markdown(
        f"""
        <div class="stare-error">
            <h2>Backend unreachable</h2>
            <p>I couldn't reach the Stare backend at <code>{html.escape(BACKEND_URL)}</code>.</p>
            <p style="margin-top:16px;"><strong>Diagnosis</strong></p>
            <pre style="background:var(--paper);padding:12px;border-radius:8px;font-family:var(--font-mono);font-size:13px;color:var(--navy-900);overflow-x:auto;">{html.escape(detail)}</pre>
            <p style="margin-top:16px;"><strong>Likely fixes</strong></p>
            <ol style="font-family:var(--font-body);color:var(--navy-800);line-height:1.7;">
                <li>From the repo root: <code>./.venv/bin/uvicorn backend.app.main:app --reload --port 8000</code></li>
                <li>Override the URL with <code>STARE_BACKEND_URL=http://your-host:8000</code></li>
                <li>Check <code>curl {html.escape(BACKEND_URL)}/health</code></li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="stare-hero">
            <h1>Ask a question about US Supreme Court case law.</h1>
            <p class="subtitle">Stare retrieves relevant precedent, generates a grounded answer, and shows you the exact case excerpts behind every citation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sample_chips() -> None:
    st.markdown('<div class="stare-chip-label">Try a sample</div>', unsafe_allow_html=True)
    cols = st.columns(len(SAMPLE_QUESTIONS), gap="small")
    for col, q in zip(cols, SAMPLE_QUESTIONS):
        with col:
            if st.button(q, key=f"chip-{hash(q)}", use_container_width=True):
                st.session_state["pending_query"] = q
                st.rerun()


def render_query_input() -> None:
    """Custom text_area plus primary button. Not st.chat_input (looks Streamlit-y)."""
    with st.form("query-form", clear_on_submit=True, border=False):
        text = st.text_area(
            "Your question",
            key=f"qbox-{st.session_state['form_nonce']}",
            placeholder="e.g., What did Obergefell v. Hodges hold about same-sex marriage?",
            label_visibility="collapsed",
            height=120,
        )
        submitted = st.form_submit_button("Ask Stare →", type="primary")
    if submitted and text.strip():
        st.session_state["queued_query"] = text.strip()
        st.session_state["form_nonce"] += 1
        st.rerun()


def call_backend(query: str) -> dict[str, Any]:
    if DEMO_MODE and DEMO_RESPONSE_PATH.exists():
        # Zero-API-cost path used only for screenshots/development.
        time.sleep(0.4)
        resp = json.loads(DEMO_RESPONSE_PATH.read_text())
        resp["query"] = query
        return resp
    r = httpx.post(
        f"{BACKEND_URL}/query",
        json={"query": query, "mode": "legal_pro"},
        timeout=120.0,
    )
    r.raise_for_status()
    return r.json()


# ───────────────────────── response rendering ─────────────────────────

def _badgeify_citations(answer_md: str) -> str:
    """Wrap inline [Case, Cite (Year)] tokens in <span class="stare-cite">."""
    def repl(m: re.Match) -> str:
        return f'<span class="stare-cite">{html.escape(m.group(1))}</span>'
    return CITATION_RE.sub(repl, answer_md)


def render_question_card(question: str) -> None:
    st.markdown(
        f"""
        <div class="stare-question-card">
            <div class="label">Question</div>
            <div class="question">{html.escape(question)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_legal_answer(resp: dict) -> None:
    answer_html = _badgeify_citations(resp.get("answer", ""))
    # Convert paragraph breaks to <p> tags (markdown's behavior)
    paragraphs = [p.strip() for p in answer_html.split("\n\n") if p.strip()]
    body = "".join(f"<p>{p}</p>" for p in paragraphs)

    st.markdown(
        f"""
        <div class="stare-answer-card">
            <div class="answer-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    citations = resp.get("citations") or []
    if citations:
        st.markdown(
            f'<div class="stare-citations-header">Citations ({len(citations)})</div>',
            unsafe_allow_html=True,
        )
        for c in citations:
            quote = (c.get("quoted_text") or "").strip()
            if len(quote) > 380:
                quote = quote[:380].rstrip() + "…"
            st.markdown(
                f"""
                <div class="stare-citation">
                    <div class="case-name">{html.escape(c.get("case_name", ""))}</div>
                    <div class="case-meta">{html.escape(c.get("us_cite", ""))} · {html.escape(c.get("decision_date", ""))}</div>
                    <p class="quote">{html.escape(quote)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    dropped = resp.get("dropped_citations") or []
    if dropped:
        st.markdown(
            f'<div style="margin-top:var(--s-4);font-family:var(--font-mono);font-size:var(--t-xs);color:var(--burgundy-700);">'
            f'⚠ {len(dropped)} unverifiable citation{"s" if len(dropped) != 1 else ""} '
            f'were dropped: ' + ", ".join(html.escape(c) for c in dropped) + "</div>",
            unsafe_allow_html=True,
        )

    chunks = (resp.get("retrieval") or {}).get("chunks") or []
    if chunks:
        sources_html = '<details class="stare-sources"><summary>View retrieved sources ({} chunks)</summary><div class="source-list">'.format(len(chunks))
        for ch in chunks:
            score = float(ch.get("rerank_score") or 0.0)
            pct = max(0.0, min(1.0, score)) * 100
            excerpt = (ch.get("text_excerpt") or "").strip()
            if len(excerpt) > 320:
                excerpt = excerpt[:320].rstrip() + "…"
            sources_html += f"""
                <div class="stare-source">
                    <div class="case-name">{html.escape(ch.get("case_name",""))}</div>
                    <div class="meta">{html.escape(ch.get("us_cite",""))} · {html.escape(ch.get("decision_date",""))}</div>
                    <div class="stare-scorebar"><div style="width:{pct:.1f}%"></div></div>
                    <div class="stare-scorebar-label">rerank score {score:.3f} · vec sim {float(ch.get('vector_similarity') or 0):.3f}</div>
                    <p class="excerpt">{html.escape(excerpt)}</p>
                </div>
            """
        sources_html += "</div></details>"
        st.markdown(sources_html, unsafe_allow_html=True)

    md = resp.get("metadata") or {}
    st.markdown(
        f"""
        <div class="stare-meta">
            Generated in {md.get("latency_ms", "?")} ms · {html.escape(md.get("model",""))} · ${md.get("cost_estimate_usd", 0.0):.5f} · {md.get("input_tokens", 0):,} in / {md.get("output_tokens", 0):,} out
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_meta_response(resp: dict) -> None:
    body = (resp.get("answer") or "").replace("•", "·")
    st.markdown(
        f"""
        <div class="stare-meta-card">
            <div class="label">About Stare</div>
            <div class="body">{html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    md = resp.get("metadata") or {}
    st.markdown(
        f"""
        <div class="stare-meta">
            Routed in {md.get("latency_ms", "?")} ms · {html.escape(md.get("model",""))} · ${md.get("cost_estimate_usd", 0.0):.5f}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_refusal(resp: dict, *, low_conf: bool) -> None:
    label = "Out of scope" if not low_conf else "Low confidence"
    extra = ""
    if low_conf:
        score = (resp.get("retrieval") or {}).get("max_rerank_score") or 0.0
        extra = (
            f'<div class="hint">Confidence below threshold '
            f'({score:.3f} / 0.300 required). The corpus may not have strong '
            f'coverage of this question.</div>'
        )
    else:
        chips = " · ".join(html.escape(q) for q in SAMPLE_QUESTIONS)
        extra = f'<div class="hint">Try a SCOTUS question. Examples: {chips}</div>'
    st.markdown(
        f"""
        <div class="stare-refusal">
            <div class="label">{label}</div>
            <div class="text">{html.escape(resp.get("answer", ""))}</div>
            {extra}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_response(resp: dict) -> None:
    cls = resp.get("classification", "out_of_scope")
    if cls == "legal_question":
        render_legal_answer(resp)
    elif cls == "meta_question":
        render_meta_response(resp)
    elif cls == "low_confidence":
        render_refusal(resp, low_conf=True)
    else:
        render_refusal(resp, low_conf=False)


def render_loading_skeleton() -> None:
    st.markdown(
        """
        <div class="stare-skeleton-card">
            <div class="stare-skeleton h1"></div>
            <div class="stare-skeleton p"></div>
            <div class="stare-skeleton p"></div>
            <div class="stare-skeleton p short"></div>
        </div>
        <div class="stare-skeleton-card">
            <div class="stare-skeleton p"></div>
            <div class="stare-skeleton p short"></div>
        </div>
        <div class="stare-skeleton-card">
            <div class="stare-skeleton p"></div>
            <div class="stare-skeleton p short"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ───────────────────────── main ─────────────────────────

def main() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("form_nonce", 0)

    # Chip click handler: a sample chip sets pending_query and reruns.
    # Promote it directly to queued_query so the query handler below picks it
    # up on this same run, without needing the user to press "Ask Stare".
    pending = st.session_state.pop("pending_query", None)
    if pending and not st.session_state.get("queued_query"):
        st.session_state["queued_query"] = pending

    render_header()

    healthy, detail = backend_health()
    if not healthy:
        render_backend_error(str(detail))
        return

    st.markdown('<div class="stare-page">', unsafe_allow_html=True)

    # History first (above the input box)
    for turn in st.session_state["history"]:
        st.markdown('<div class="stare-turn">', unsafe_allow_html=True)
        render_question_card(turn["question"])
        render_response(turn["response"])
        st.markdown("</div>", unsafe_allow_html=True)

    # Hero only on first load
    if not st.session_state["history"]:
        render_hero()
        render_sample_chips()

    queued = st.session_state.pop("queued_query", None)
    if queued:
        skeleton_slot = st.empty()
        with skeleton_slot.container():
            st.markdown('<div class="stare-turn">', unsafe_allow_html=True)
            render_question_card(queued)
            render_loading_skeleton()
            st.markdown("</div>", unsafe_allow_html=True)
        try:
            resp = call_backend(queued)
            st.session_state["history"].append({"question": queued, "response": resp, "id": str(uuid.uuid4())})
            skeleton_slot.empty()
            st.rerun()
        except Exception as e:
            skeleton_slot.empty()
            st.markdown(
                f"""
                <div class="stare-error" style="margin-top:24px;">
                    <h2>Query failed</h2>
                    <p>The backend returned an error.</p>
                    <pre style="background:var(--paper);padding:12px;border-radius:8px;font-family:var(--font-mono);font-size:13px;">{html.escape(str(e))}</pre>
                </div>
                """,
                unsafe_allow_html=True,
            )

    render_query_input()
    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
