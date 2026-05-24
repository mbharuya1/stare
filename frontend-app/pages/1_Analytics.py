"""Stare Analytics: password-gated query log dashboard.

Streamlit auto-mounts this file as a sidebar nav entry because of the
``pages/`` directory convention. The filename maps to the displayed name:
``1_Analytics.py`` becomes ``Analytics`` in the sidebar (the leading
``1_`` sorts the page; the rest becomes the label).

This page is read-only. It reads ``data/query_log.jsonl`` written by
``src.logger.log_query`` and never invokes the agent.
"""
from __future__ import annotations

import html
import io
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.logger import LOG_PATH
from src.styles import COLUMN_SVG, get_css

# ----------------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------------

st.set_page_config(
    page_title="Stare Analytics",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject the shared design system, then override the main page's tight
# 780px reading column. The dashboard wants room for charts and tables.
st.markdown(get_css(), unsafe_allow_html=True)
st.markdown(
    "<style>.block-container { max-width: 1200px !important; }</style>",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Password gate
# ----------------------------------------------------------------------------

def _gate() -> None:
    """Block rendering until the admin password is entered correctly."""
    load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
    expected = (os.getenv("STARE_ADMIN_PASSWORD") or "").strip()

    if not expected:
        st.markdown(
            '<div class="password-card">'
            '<div class="lock-title">Admin password not configured</div>'
            '<p class="lock-body">Set <code>STARE_ADMIN_PASSWORD</code> in '
            "<code>.env</code> to enable the analytics dashboard.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.stop()

    if st.session_state.get("analytics_authed"):
        return

    st.markdown(
        '<div class="password-card">'
        '<div class="lock-title">Admin access required</div>'
        '<p class="lock-body">Enter the admin password to view the analytics '
        "dashboard. The password lives in your local <code>.env</code> file.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    pw = st.text_input(
        "Password",
        type="password",
        key="analytics_pw_input",
        placeholder="Enter password",
        label_visibility="collapsed",
    )
    submitted = st.button("Unlock", type="primary")

    if submitted:
        if pw and pw == expected:
            st.session_state.analytics_authed = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


_gate()


# ----------------------------------------------------------------------------
# Log loading + derived columns
# ----------------------------------------------------------------------------

def _load_records() -> list[dict[str, Any]]:
    """Read every JSONL line from the log file. Skip malformed lines silently."""
    if not LOG_PATH.exists():
        return []
    out: list[dict] = []
    with LOG_PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


# Map the raw ``route_taken`` (last graph node) to the four user-facing
# answer-path buckets requested for the route distribution chart.
_ROUTE_BUCKET = {
    "generate":                "legal_question",
    "low_confidence_response": "low_confidence_response",
    "out_of_scope_response":   "out_of_scope",
    "meta_response":           "meta_question",
}


def _bucket(route: str | None) -> str:
    return _ROUTE_BUCKET.get(route or "", route or "unknown")


# ----------------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------------

st.markdown(
    f'<div class="hero-row">'
    f"  {COLUMN_SVG}"
    f'  <h1 class="hero-title">Analytics</h1>'
    f"</div>"
    f'<p class="hero-tagline">Query log monitoring.</p>'
    f'<p class="hero-subtitle">'
    f"Activity, cost, latency, and routing distribution drawn from "
    f"<code>data/query_log.jsonl</code>. Refreshes on every page load."
    f"</p>"
    f'<hr class="hero-rule" />',
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Toolbar: refresh + downloads
# ----------------------------------------------------------------------------

records = _load_records()

tb_left, tb_csv, tb_json, tb_refresh = st.columns([5, 1.3, 1.3, 1.0])

with tb_csv:
    if records:
        df_export = pd.DataFrame(records).copy()
        # Lists must be flattened for CSV. Keep semantics with " | " joiner.
        for col in ("retrieved_cases", "cited_cases"):
            if col in df_export.columns:
                df_export[col] = df_export[col].apply(
                    lambda xs: " | ".join(xs) if isinstance(xs, list) else ""
                )
        csv_buf = io.StringIO()
        df_export.to_csv(csv_buf, index=False)
        st.download_button(
            "⬇  CSV",
            data=csv_buf.getvalue(),
            file_name="stare_query_log.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.download_button(
            "⬇  CSV", data="", file_name="stare_query_log.csv",
            mime="text/csv", use_container_width=True, disabled=True,
        )

with tb_json:
    st.download_button(
        "⬇  JSON",
        data=json.dumps(records, indent=2, ensure_ascii=False),
        file_name="stare_query_log.json",
        mime="application/json",
        use_container_width=True,
        disabled=not records,
    )

with tb_refresh:
    if st.button("↻ Refresh", use_container_width=True):
        st.rerun()


# ----------------------------------------------------------------------------
# Empty state
# ----------------------------------------------------------------------------

if not records:
    st.markdown(
        '<div class="empty-state">'
        '<div class="empty-title">No queries logged yet</div>'
        '<p class="empty-body">'
        "Ask your first question on the main <strong>Stare</strong> page "
        "to start tracking activity. Each query writes one line to "
        "<code>data/query_log.jsonl</code>; this dashboard reads it on "
        "every page load."
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()


# ----------------------------------------------------------------------------
# Build the working DataFrame
# ----------------------------------------------------------------------------

df = pd.DataFrame(records)
df["ts"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
df["date"] = df["ts"].dt.date
df["bucket"] = df["route_taken"].apply(_bucket)
df["latency_s"] = df["latency_ms"].astype(float) / 1000.0
df["top_similarity"] = pd.to_numeric(df.get("top_similarity"), errors="coerce")
df["estimated_cost_usd"] = pd.to_numeric(
    df.get("estimated_cost_usd"), errors="coerce"
).fillna(0.0)


# ----------------------------------------------------------------------------
# KPI row
# ----------------------------------------------------------------------------

total_queries = len(df)
total_cost = float(df["estimated_cost_usd"].sum())
avg_latency_s = float(df["latency_s"].mean()) if total_queries else 0.0
legal_sims = df.loc[df["bucket"] == "legal_question", "top_similarity"].dropna()
avg_sim = float(legal_sims.mean()) if len(legal_sims) else None


def _kpi_html(label: str, value: str, suffix: str = "") -> str:
    suffix_html = f'<div class="kpi-suffix">{html.escape(suffix)}</div>' if suffix else ""
    return (
        f'<div class="kpi-card">'
        f'  <div class="kpi-label">{html.escape(label)}</div>'
        f'  <div class="kpi-value">{html.escape(value)}</div>'
        f"  {suffix_html}"
        f"</div>"
    )


k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(_kpi_html("Total Queries", f"{total_queries:,}"), unsafe_allow_html=True)
with k2:
    st.markdown(_kpi_html("Total Cost", f"${total_cost:.4f}"), unsafe_allow_html=True)
with k3:
    st.markdown(_kpi_html("Avg Latency", f"{avg_latency_s:.1f}s"), unsafe_allow_html=True)
with k4:
    sim_value = f"{avg_sim:.3f}" if avg_sim is not None else "--"
    suffix = f"n = {len(legal_sims)}" if avg_sim is not None else "no legal questions yet"
    st.markdown(_kpi_html("Avg Similarity", sim_value, suffix), unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------------

def _section(title: str) -> None:
    st.markdown(
        f'<div class="dash-section">{html.escape(title)}</div>'
        f'<hr class="dash-section-rule" />',
        unsafe_allow_html=True,
    )


# --- Activity over time ---
_section("Activity over time")
daily = (
    df.dropna(subset=["date"])
      .groupby("date").size()
      .rename("queries")
      .to_frame()
)
if not daily.empty:
    daily.index = pd.to_datetime(daily.index)
    st.line_chart(daily, height=260)
else:
    st.caption("Not enough data for a timeline yet.")

# --- Route distribution ---
_section("Route distribution")
route_counts = (
    df["bucket"].value_counts()
      .rename("queries")
      .to_frame()
)
st.bar_chart(route_counts, height=260, horizontal=True)

# --- Most frequently retrieved cases ---
_section("Most frequently retrieved cases")
all_cases: list[str] = []
for cases in df["retrieved_cases"]:
    if isinstance(cases, list):
        all_cases.extend(c.strip() for c in cases if c and c.strip())
if all_cases:
    top_cases = (
        pd.Series(all_cases)
          .value_counts()
          .head(10)
          .rename("retrievals")
          .to_frame()
    )
    st.bar_chart(top_cases, height=320, horizontal=True)
else:
    st.caption("No cases have been retrieved yet (only meta / out-of-scope queries logged).")


# ----------------------------------------------------------------------------
# Query table
# ----------------------------------------------------------------------------

_section("All queries")

search = st.text_input(
    "Filter questions",
    placeholder="Type to filter by question text (case-insensitive)...",
    label_visibility="collapsed",
    key="analytics_search",
)

view = df.copy()
if search.strip():
    needle = search.strip().lower()
    view = view[view["question"].fillna("").str.lower().str.contains(needle, regex=False)]


def _truncate(s: str, n: int = 80) -> str:
    s = s or ""
    return s if len(s) <= n else s[:n].rstrip() + "..."


table = pd.DataFrame({
    "Timestamp":      view["ts"].dt.strftime("%Y-%m-%d %H:%M"),
    "Question":       view["question"].fillna("").apply(_truncate),
    "Route":          view["bucket"],
    "Top Similarity": view["top_similarity"].apply(
        lambda v: f"{v:.3f}" if pd.notna(v) else "--"
    ),
    "Cost":           view["estimated_cost_usd"].apply(lambda v: f"${v:.4f}"),
    "Latency":        view["latency_s"].apply(lambda v: f"{v:.1f}s"),
})
# Newest first.
table = table.iloc[::-1].reset_index(drop=True)

st.dataframe(table, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------------
# Detail expander
# ----------------------------------------------------------------------------

with st.expander("View full query details"):
    if not records:
        st.caption("No queries to inspect.")
    else:
        # Build label list (newest first), keep raw record alongside.
        labelled: list[tuple[str, dict]] = []
        for rec in records:
            ts_raw = rec.get("timestamp", "")
            try:
                ts_short = pd.to_datetime(ts_raw, utc=True).strftime("%Y-%m-%d %H:%M")
            except Exception:
                ts_short = ts_raw
            q = (rec.get("question") or "")[:60]
            labelled.append((f"{ts_short}  -  {q}", rec))
        labelled.reverse()

        labels = [lbl for lbl, _ in labelled]
        choice = st.selectbox("Select a query", labels, index=0)
        rec = next(r for lbl, r in labelled if lbl == choice)

        st.markdown('<div class="section-label">Question</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="question-echo">{html.escape(rec.get("question") or "")}</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-label">Answer</div>', unsafe_allow_html=True)
        st.markdown(rec.get("answer") or "_(no answer)_")

        retrieved = rec.get("retrieved_cases") or []
        if retrieved:
            st.markdown(
                '<div class="section-label">Retrieved cases</div>',
                unsafe_allow_html=True,
            )
            pills = "".join(
                f'<span class="cited-pill">{html.escape(c)}</span>' for c in retrieved
            )
            st.markdown(f'<div class="cited-row">{pills}</div>', unsafe_allow_html=True)

        cited = rec.get("cited_cases") or []
        if cited:
            st.markdown(
                '<div class="section-label">Cited cases</div>',
                unsafe_allow_html=True,
            )
            pills = "".join(
                f'<span class="cited-pill">{html.escape(c)}</span>' for c in cited
            )
            st.markdown(f'<div class="cited-row">{pills}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label">Raw record</div>', unsafe_allow_html=True)
        st.code(json.dumps(rec, indent=2, ensure_ascii=False), language="json")
