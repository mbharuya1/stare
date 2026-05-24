"""Stare: Streamlit UI for the agentic Legal RAG over US Supreme Court decisions.

Editorial LegalTech aesthetic: classical column wordmark, navy + cream +
burgundy palette, serif body for the answer card. The shared design system
(CSS + column SVG) lives in :mod:`src.styles`.

Launch with:
    streamlit run app.py
"""
from __future__ import annotations

import concurrent.futures
import html
import time
from pathlib import Path

import streamlit as st
from markdown_it import MarkdownIt

from src.agent import run_agent
from src.logger import humanize_ago, log_query, read_log_stats
from src.styles import COLUMN_SVG, get_css

st.set_page_config(
    page_title="Stare: SCOTUS Q&A",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(get_css(), unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# First-run bootstrap: download the corpus and build the Chroma index.
#
# On Streamlit Cloud the repo is cloned without `chroma_db/` or
# `data/scotus_cases/` (both gitignored), so a cold start has to provision
# both before the agent can answer. The Chroma directory check is itself
# the "run once per cold start" guard: subsequent Streamlit reruns return
# immediately because the directory exists.
# ----------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent
_CHROMA_DIR = _PROJECT_ROOT / "chroma_db"
_DATA_DIR = _PROJECT_ROOT / "data" / "scotus_cases"


def _bootstrap_index() -> None:
    if _CHROMA_DIR.exists() and any(_CHROMA_DIR.iterdir()):
        return  # already built; fast path on every rerun

    st.info(
        "First-time setup: fetching the SCOTUS corpus and building the "
        "case index. This takes about 3 to 5 minutes and only happens "
        "once per deploy."
    )

    # Phase 1: download source corpus from HuggingFace if missing.
    if not _DATA_DIR.exists() or not any(_DATA_DIR.glob("*.txt")):
        try:
            with st.spinner(
                "Downloading SCOTUS corpus from HuggingFace "
                "(coastalcph/lex_glue)..."
            ):
                # Heavy import (HF datasets) deferred until actually needed.
                from data.download_scotus import download
                code = download()
            if code != 0:
                st.error(
                    f"Corpus download exited with code {code}. "
                    "Check the server logs for details."
                )
                st.stop()
        except Exception as exc:
            st.error(
                f"Corpus download failed: **{type(exc).__name__}**: {exc}"
            )
            st.stop()

    # Phase 2: chunk + embed local files into ChromaDB.
    try:
        with st.spinner("Indexing ~100 SCOTUS opinions into ChromaDB..."):
            # Heavy imports (chromadb, sentence-transformers) deferred too.
            from src.ingest import main as run_ingest
            code = run_ingest()
        # Exit 0 = fully clean; exit 2 = some per-case failures but the
        # index is still usable. Either is acceptable for serving.
        if code not in (0, 2):
            st.error(
                f"Ingestion exited with code {code}. Check the server logs "
                "for details."
            )
            st.stop()
    except Exception as exc:
        st.error(
            f"Ingestion failed: **{type(exc).__name__}**: {exc}"
        )
        st.stop()

    st.success("Setup complete. Reloading the app...")
    st.rerun()


_bootstrap_index()


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

EXAMPLES = [
    "What did the court rule on warrantless searches?",
    "How has the Court interpreted the First Amendment?",
    "What's the weather in Boston?",
    "How many cases do you have access to?",
]

LOADING_MESSAGES = [
    "Classifying question...",
    "Searching precedent...",
    "Reviewing cases...",
    "Drafting answer...",
]

_md = MarkdownIt("commonmark", {"breaks": True, "linkify": False})


# ----------------------------------------------------------------------------
# State
# ----------------------------------------------------------------------------

def _init_state() -> None:
    st.session_state.setdefault("user_question", "")
    st.session_state.setdefault("latest_result", None)
    st.session_state.setdefault("latest_question", "")


def _fill_example(text: str) -> None:
    st.session_state.user_question = text


# ----------------------------------------------------------------------------
# Loading: cycling messages while run_agent runs in a worker thread
# ----------------------------------------------------------------------------

def _run_with_progress(question: str) -> tuple[dict, int]:
    """Run the agent in a worker thread; cycle status messages on the main thread.

    Returns (result_state, latency_ms).
    """
    placeholder = st.empty()
    t0 = time.perf_counter()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(run_agent, question)
            i = 0
            while not future.done():
                msg = LOADING_MESSAGES[i % len(LOADING_MESSAGES)]
                placeholder.markdown(
                    f'<div class="loading-wrap">'
                    f'  <div class="loading-text">{html.escape(msg)}</div>'
                    f'  <div class="loading-underline"></div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                time.sleep(0.7)
                i += 1
            result = future.result()
    finally:
        placeholder.empty()
    latency_ms = int((time.perf_counter() - t0) * 1000)
    return result, latency_ms


# ----------------------------------------------------------------------------
# Renderers
# ----------------------------------------------------------------------------

def _render_hero() -> None:
    st.markdown(
        f'<div class="hero-row">'
        f"  {COLUMN_SVG}"
        f'  <h1 class="hero-title">Stare</h1>'
        f"</div>"
        f'<p class="hero-tagline">Question the Court. Get cited answers.</p>'
        f'<p class="hero-subtitle">'
        f"An agentic RAG system over US Supreme Court decisions. Classifies "
        f"your question, retrieves relevant precedent, and generates "
        f"grounded answers with case citations."
        f"</p>"
        f'<hr class="hero-rule" />',
        unsafe_allow_html=True,
    )


def _render_input_hint() -> None:
    st.markdown(
        '<div class="input-hint">'
        "Try asking about Fourth Amendment, First Amendment, or Equal "
        "Protection cases."
        "</div>",
        unsafe_allow_html=True,
    )


def _render_badge(result: dict) -> None:
    route = result.get("route_taken") or []
    if "generate" in route:
        n = len(result.get("retrieved_chunks") or [])
        text = f"Legal Question · {n} sources"
        cls = "badge-legal"
    elif "low_confidence_response" in route:
        score = result.get("confidence_score") or 0.0
        text = f"Low Confidence · top similarity {score:.2f}"
        cls = "badge-lowconf"
    elif "out_of_scope_response" in route:
        text = "Out of Scope"
        cls = "badge-oos"
    elif "meta_response" in route:
        text = "System Info"
        cls = "badge-meta"
    else:
        text = "Route · " + " -> ".join(route)
        cls = "badge-oos"
    st.markdown(
        f'<span class="badge {cls}">{html.escape(text)}</span>',
        unsafe_allow_html=True,
    )


def _render_question_echo(question: str) -> None:
    st.markdown(
        f'<div class="question-echo">{html.escape(question)}</div>',
        unsafe_allow_html=True,
    )


def _render_answer(result: dict) -> None:
    answer_md = result.get("answer") or "_(no answer)_"
    answer_html = _md.render(answer_md)
    st.markdown(
        f'<div class="answer-card">{answer_html}</div>',
        unsafe_allow_html=True,
    )


def _render_cited(result: dict) -> None:
    cited = result.get("cited_cases") or []
    if not cited:
        return
    pills = "".join(
        f'<span class="cited-pill">{html.escape(c)}</span>' for c in cited
    )
    st.markdown(
        '<div class="section-label">Cited Cases</div>'
        f'<div class="cited-row">{pills}</div>',
        unsafe_allow_html=True,
    )


def _render_sources(result: dict) -> None:
    if "generate" not in (result.get("route_taken") or []):
        return
    chunks = result.get("retrieved_chunks") or []
    if not chunks:
        return

    with st.expander(f"Show retrieved sources ({len(chunks)})"):
        last = len(chunks)
        for i, chunk in enumerate(chunks, start=1):
            case = (chunk.get("case_name") or "").strip() or "Unnamed case"
            year = chunk.get("year") or "n.d."
            score = float(chunk.get("similarity_score") or 0.0)
            idx = chunk.get("chunk_index", "?")
            text = chunk.get("text") or ""
            preview = text if len(text) <= 750 else text[:750].rstrip() + "..."

            st.markdown(
                f'<div class="source-card">'
                f'  <div class="source-head">'
                f'    <div>'
                f'      <span class="source-case">{i}. {html.escape(case)}</span>'
                f'      <span class="source-year">· {html.escape(str(year))}</span>'
                f"    </div>"
                f'    <span class="score-badge">{score:+.3f}</span>'
                f"  </div>"
                f'  <div class="source-meta">chunk #{html.escape(str(idx))}</div>'
                f'  <div class="source-text">{html.escape(preview)}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if i < last:
                st.markdown('<hr class="source-divider" />', unsafe_allow_html=True)


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="sidebar-label">About</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-about">'
            "<strong>Stare</strong> answers questions over a corpus of "
            "US Supreme Court decisions using retrieval-augmented generation. "
            "The agent classifies your question, searches a vector store of "
            "~100 SCOTUS opinions, and generates a cited answer with Claude. "
            "It refuses to answer beyond what the retrieved cases support."
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown('<hr class="sidebar-rule" />', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-label">Example questions</div>',
            unsafe_allow_html=True,
        )
        for i, ex in enumerate(EXAMPLES):
            st.button(
                ex,
                on_click=_fill_example,
                args=(ex,),
                key=f"example_{i}",
                use_container_width=True,
            )
        st.markdown(
            '<div class="built-with">'
            '<div class="sidebar-label" style="margin-top: 0;">Built with</div>'
            '<div class="built-with-tags">'
            '<span class="built-tag">python</span>'
            '<span class="built-tag">langchain</span>'
            '<span class="built-tag">langgraph</span>'
            '<span class="built-tag">chromadb</span>'
            '<span class="built-tag">claude</span>'
            "</div></div>",
            unsafe_allow_html=True,
        )

        # Usage stats: read fresh from the log file on every render.
        stats = read_log_stats()
        if stats["count"] == 0:
            usage_html = (
                '<div class="usage-stats">'
                '<div class="sidebar-label" style="margin-top: 0;">Usage</div>'
                "No queries yet."
                "</div>"
            )
        else:
            n = stats["count"]
            label = "question answered" if n == 1 else "questions answered"
            ago = humanize_ago(stats["last_ts"])
            usage_html = (
                '<div class="usage-stats">'
                '<div class="sidebar-label" style="margin-top: 0;">Usage</div>'
                f'<span class="num">{n}</span> {label}'
                '<span class="sep">·</span>'
                f"last query {html.escape(ago)}"
                "</div>"
            )
        st.markdown(usage_html, unsafe_allow_html=True)


def _render_footer() -> None:
    st.markdown(
        '<div class="app-footer">'
        '<span class="brand">Stare</span>'
        '<span class="by">Designed and built by Mabrok Bharuya</span>'
        '<span class="links">'
        '<a href="https://github.com/mbharuya1" target="_blank" rel="noopener">github.com/mbharuya1</a>'
        '<span class="sep">·</span>'
        '<a href="https://www.linkedin.com/in/ai-mabrok-bharuya" target="_blank" rel="noopener">linkedin.com/in/ai-mabrok-bharuya</a>'
        "</span>"
        "</div>",
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> None:
    _init_state()
    _render_sidebar()

    _render_hero()

    st.text_area(
        "Your question",
        key="user_question",
        height=110,
        placeholder="e.g. What did the court rule on warrantless searches?",
        label_visibility="collapsed",
    )
    _render_input_hint()
    ask = st.button("Search cases", type="primary")

    if ask:
        q = (st.session_state.user_question or "").strip()
        if not q:
            st.warning("Please enter a question first.")
        else:
            try:
                result, latency_ms = _run_with_progress(q)
                st.session_state.latest_result = result
                st.session_state.latest_question = q
                log_query(result, latency_ms)
            except Exception as exc:
                st.session_state.latest_result = None
                st.error(
                    f"Something went wrong while answering: "
                    f"**{type(exc).__name__}**: {exc}"
                )

    result = st.session_state.latest_result
    if result is not None:
        _render_question_echo(st.session_state.latest_question)
        _render_badge(result)
        _render_answer(result)
        _render_cited(result)
        _render_sources(result)

    _render_footer()


if __name__ == "__main__":
    main()
