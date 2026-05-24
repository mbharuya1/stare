"""Shared visual design system for Stare.

Both ``app.py`` and ``pages/1_Analytics.py`` import :func:`get_css` and
:data:`COLUMN_SVG` from here so the brand stays consistent.

The CSS string covers everything: tokens, hero, badges, answer card,
sources, sidebar, footer, plus dashboard-only widgets (KPI cards,
empty state, password gate). Pages that don't use a given selector
simply don't trigger it; harmless dead weight.
"""
from __future__ import annotations

# ---- The shared stylesheet --------------------------------------------------

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&display=swap');

/* ---- Tokens --------------------------------------------------------- */
:root {
    --navy: #1a2540;
    --navy-2: #2a3a5a;
    --bg: #fafaf7;
    --card: #fffefb;
    --ink: #2c2c2c;
    --muted: #6c6c6c;
    --rule: #e8e6e1;
    --rule-soft: #efece6;
    --tan: #8b6f47;
    --burgundy: #722f37;
    --burgundy-tint: #f7eeef;
    --warm-bg: #f4f1e8;
    --warm-bg-2: #faf8f1;

    --font-body: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Helvetica, Arial, sans-serif;
    --font-display: 'Playfair Display', Georgia, 'Times New Roman', serif;
    --font-serif: Georgia, 'Times New Roman', serif;
    --font-mono: 'SF Mono', Monaco, Menlo, Consolas, monospace;
}

/* ---- Top accent stripe (the brand signature) ------------------------ */
.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(
        to right,
        var(--navy) 0%,
        var(--navy) 30%,
        var(--bg) 50%,
        var(--burgundy) 70%,
        var(--burgundy) 100%
    );
    z-index: 9999;
    pointer-events: none;
}

/* ---- Globals -------------------------------------------------------- */
.stApp { background-color: var(--bg); }
html, body, [class*="css"] { font-family: var(--font-body); color: var(--ink); }

/* Hide Streamlit chrome */
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.stDeployButton { display: none !important; }

/* Tighten main container (reading column on the main page).
   Pages that need a wider layout (like Analytics) set layout="wide"
   AND inject a one-line override that raises this max-width. */
.block-container { padding-top: 2.5rem !important; padding-bottom: 2rem !important; max-width: 780px !important; }

/* ---- Hero ----------------------------------------------------------- */
.hero-row {
    display: flex;
    align-items: flex-end;
    gap: 0.95rem;
    margin: 0.4rem 0 0.4rem 0;
}
.hero-column-svg {
    flex: 0 0 auto;
    color: var(--navy);
    margin-bottom: 0.55rem;
}
.hero-title {
    font-family: var(--font-display);
    font-size: 3.5rem;
    font-weight: 600;
    color: var(--navy);
    letter-spacing: -0.025em;
    line-height: 1;
    margin: 0;
}
.hero-tagline {
    font-family: var(--font-serif);
    color: var(--ink);
    font-size: 1.2rem;
    font-weight: 400;
    line-height: 1.45;
    margin: 0.25rem 0 0.55rem 0;
    letter-spacing: -0.005em;
}
.hero-subtitle {
    color: var(--muted);
    font-size: 0.95rem;
    line-height: 1.55;
    margin: 0 0 1.55rem 0;
    font-weight: 400;
    max-width: 60ch;
}
.hero-rule {
    height: 1px;
    background: linear-gradient(to right, var(--tan) 0%, var(--rule) 30%, transparent 80%);
    border: none;
    margin: 0 0 1.9rem 0;
}

/* ---- Inputs --------------------------------------------------------- */
.stTextArea label, .stTextInput label { font-weight: 500; color: var(--ink); font-size: 0.92rem; letter-spacing: 0.005em; }
.stTextArea textarea, .stTextInput input {
    font-family: var(--font-body) !important;
    font-size: 1rem !important;
    line-height: 1.55 !important;
    padding: 0.85rem 1.05rem !important;
    border-radius: 8px !important;
    border: 1px solid #d8d4c8 !important;
    background: var(--card) !important;
    color: var(--ink) !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--navy) !important;
    box-shadow: 0 0 0 3px rgba(26, 37, 64, 0.10) !important;
    outline: none !important;
}
.input-hint {
    font-size: 0.83rem;
    color: var(--muted);
    margin: 0.35rem 0 1.1rem 0.15rem;
    font-style: italic;
}

/* Primary button override (kills the default red) */
.stButton > button[kind="primary"] {
    background-color: var(--navy) !important;
    color: #fafaf7 !important;
    border: 1px solid var(--navy) !important;
    padding: 0.6rem 1.4rem !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.01em !important;
    border-radius: 6px !important;
    transition: background-color 0.15s, transform 0.05s !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.stButton > button[kind="primary"]:hover {
    background-color: var(--navy-2) !important;
    border-color: var(--navy-2) !important;
    color: #fafaf7 !important;
}
.stButton > button[kind="primary"]:active { transform: translateY(1px); }
.stButton > button[kind="primary"]:focus { box-shadow: 0 0 0 3px rgba(26, 37, 64, 0.18) !important; }

/* Download buttons get the same secondary treatment */
.stDownloadButton > button {
    background: var(--card) !important;
    color: var(--navy) !important;
    border: 1px solid var(--navy) !important;
    padding: 0.5rem 1.05rem !important;
    font-weight: 500 !important;
    font-size: 0.86rem !important;
    letter-spacing: 0.01em !important;
    border-radius: 5px !important;
    transition: all 0.15s ease !important;
    font-family: var(--font-mono) !important;
}
.stDownloadButton > button:hover {
    background: var(--navy) !important;
    color: #fafaf7 !important;
}

/* ---- Refined route badges (citation-marker style) ------------------- */
.badge {
    display: inline-block;
    padding: 0.3rem 0.7rem 0.28rem 0.7rem;
    border-radius: 3px;
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    margin: 0.2rem 0 0.85rem 0;
    border: 1px solid;
    background: var(--card);
}
.badge-legal     { color: var(--burgundy); border-color: var(--burgundy); background: var(--burgundy-tint); }
.badge-meta      { color: var(--navy);     border-color: var(--navy);     background: #eef1f7; }
.badge-lowconf   { color: #6e5a0e;         border-color: #c9b35c;         background: #fbf3d3; }
.badge-oos       { color: #555;            border-color: #c0bcae;         background: #ececeb; }

/* ---- Question echo -------------------------------------------------- */
.question-echo {
    font-family: var(--font-serif);
    font-size: 1.1rem;
    font-style: italic;
    color: #4a4a44;
    line-height: 1.5;
    margin: 1.6rem 0 0.9rem 0;
    padding-left: 0.9rem;
    border-left: 3px solid var(--tan);
}

/* ---- Answer card (reads like a brief, not a chatbot reply) ---------- */
.answer-card {
    background: var(--card);
    border-left: 4px solid var(--navy);
    border-top: 1px solid var(--rule-soft);
    border-right: 1px solid var(--rule-soft);
    border-bottom: 1px solid var(--rule-soft);
    border-radius: 4px;
    padding: 2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    margin: 0.4rem 0 1.25rem 0;
    font-family: var(--font-serif);
    font-size: 16px;
    line-height: 1.72;
    color: var(--ink);
}
.answer-card p { margin: 0 0 0.95rem 0; }
.answer-card p:last-child { margin-bottom: 0; }
.answer-card strong { color: var(--navy); font-weight: 600; }
.answer-card ol, .answer-card ul { margin: 0.4rem 0 0.95rem 1.4rem; padding: 0; }
.answer-card li { margin-bottom: 0.45rem; }
.answer-card code {
    font-family: var(--font-mono);
    background: var(--warm-bg);
    padding: 0.05rem 0.35rem;
    border-radius: 3px;
    font-size: 0.92em;
}

/* ---- Cited cases (academic-paper reference pills) ------------------- */
.section-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--muted);
    font-weight: 600;
    margin: 1.4rem 0 0.6rem 0;
}
.cited-row { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-bottom: 1.25rem; }
.cited-pill {
    display: inline-block;
    padding: 0.28rem 0.65rem;
    background: var(--warm-bg-2);
    border: 1px solid var(--rule);
    border-radius: 3px;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--navy);
    letter-spacing: 0.005em;
}

/* ---- Sources -------------------------------------------------------- */
.source-card {
    background: var(--card);
    border: 1px solid var(--rule-soft);
    border-radius: 6px;
    padding: 1.05rem 1.25rem 1.1rem 1.25rem;
    margin-bottom: 0.85rem;
    box-shadow: 0 1px 1px rgba(0,0,0,0.02);
}
.source-card + .source-divider {
    height: 1px;
    background: var(--rule-soft);
    border: none;
    margin: 0 0.4rem 0.85rem 0.4rem;
}
.source-head {
    display: flex; justify-content: space-between; align-items: baseline;
    flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.35rem;
}
.source-case {
    font-family: var(--font-serif);
    font-weight: 700;
    color: var(--navy);
    font-size: 1rem;
    line-height: 1.3;
}
.source-year {
    font-family: var(--font-serif);
    color: var(--muted);
    font-size: 0.88rem;
    font-weight: 400;
    margin-left: 0.4rem;
}
.source-meta {
    color: var(--muted);
    font-size: 0.76rem;
    margin-bottom: 0.6rem;
    letter-spacing: 0.01em;
    font-family: var(--font-mono);
}
.score-badge {
    display: inline-block;
    padding: 0.18rem 0.55rem;
    border-radius: 3px;
    font-size: 0.74rem;
    font-weight: 500;
    font-family: var(--font-mono);
    letter-spacing: 0.02em;
    color: #fafaf7;
    background: var(--navy);
}
.source-text {
    font-family: var(--font-serif);
    font-size: 14px;
    line-height: 1.7;
    color: #3a3a36;
    background: var(--warm-bg-2);
    border: 1px solid #f0ead8;
    border-radius: 4px;
    padding: 0.85rem 1rem;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-x: auto;
}

/* Streamlit's native expander, made quieter */
[data-testid="stExpander"] { border: none !important; box-shadow: none !important; background: transparent !important; }
[data-testid="stExpander"] details { border: 1px solid var(--rule-soft) !important; background: var(--card) !important; border-radius: 6px !important; }
[data-testid="stExpander"] summary { padding: 0.7rem 1rem !important; font-weight: 500 !important; color: var(--ink) !important; font-size: 0.9rem !important; }
[data-testid="stExpander"] summary:hover { color: var(--navy) !important; }

/* ---- Loading: cycling text + animated underline -------------------- */
.loading-wrap {
    display: inline-block;
    margin: 1rem 0 1.3rem 0;
    padding: 0;
}
.loading-text {
    font-family: var(--font-serif);
    font-style: italic;
    font-size: 1.02rem;
    color: var(--navy);
    letter-spacing: 0.005em;
}
.loading-underline {
    margin-top: 0.45rem;
    height: 2px;
    width: 220px;
    background: var(--rule);
    border-radius: 1px;
    overflow: hidden;
    position: relative;
}
.loading-underline::after {
    content: "";
    position: absolute;
    top: 0; left: 0;
    height: 100%;
    width: 38%;
    background: var(--navy);
    border-radius: 1px;
    animation: slide 1.4s ease-in-out infinite;
}
@keyframes slide {
    0%   { left: -40%; }
    50%  { left: 60%; }
    100% { left: 100%; }
}

/* ---- Sidebar -------------------------------------------------------- */
section[data-testid="stSidebar"] {
    background-color: var(--warm-bg);
    border-right: 1px solid var(--rule);
}
section[data-testid="stSidebar"] .block-container { padding-top: 2rem !important; }

.sidebar-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--muted);
    font-weight: 600;
    margin: 1.4rem 0 0.55rem 0;
}
.sidebar-label:first-of-type { margin-top: 0; }
.sidebar-about {
    font-size: 0.9rem;
    line-height: 1.65;
    color: #3a3a36;
    margin-bottom: 0.4rem;
}
.sidebar-about strong { color: var(--navy); font-weight: 600; }
.sidebar-rule {
    height: 1px;
    background: var(--rule);
    border: none;
    margin: 1.5rem 0 0;
}
section[data-testid="stSidebar"] .stButton > button {
    background: var(--card) !important;
    color: var(--ink) !important;
    border: 1px solid #ddd6c4 !important;
    text-align: left !important;
    font-size: 0.86rem !important;
    line-height: 1.4 !important;
    padding: 0.55rem 0.8rem !important;
    transition: all 0.15s ease !important;
    font-weight: 400 !important;
    white-space: normal !important;
    height: auto !important;
    min-height: 0 !important;
    border-radius: 5px !important;
    margin-bottom: 0.35rem !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #ffffff !important;
    border-color: var(--navy) !important;
    color: var(--navy) !important;
    transform: translateX(1px);
}
section[data-testid="stSidebar"] .stButton > button:focus { box-shadow: 0 0 0 2px rgba(26, 37, 64, 0.15) !important; }

.built-with {
    margin-top: 1.6rem;
    padding-top: 1rem;
    border-top: 1px solid var(--rule);
}
.built-with-tags { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.55rem; }
.built-tag {
    display: inline-block;
    padding: 0.18rem 0.5rem;
    background: var(--card);
    border: 1px solid #ddd6c4;
    border-radius: 3px;
    font-size: 0.7rem;
    color: #5a5a55;
    font-family: var(--font-mono);
    letter-spacing: 0.02em;
}

.usage-stats {
    margin-top: 1.6rem;
    padding-top: 1rem;
    border-top: 1px solid var(--rule);
    font-family: var(--font-mono);
    font-size: 0.76rem;
    color: var(--muted);
    line-height: 1.6;
    letter-spacing: 0.005em;
}
.usage-stats .num { color: var(--navy); font-weight: 600; }
.usage-stats .sep { color: #c8c2b3; margin: 0 0.4rem; }

/* ---- Footer (elegant attribution block) ----------------------------- */
.app-footer {
    margin: 3.8rem 0 0.5rem 0;
    padding-top: 1.2rem;
    border-top: 1px solid var(--rule);
    text-align: center;
    color: var(--muted);
    font-size: 0.83rem;
    letter-spacing: 0.005em;
    line-height: 1.7;
}
.app-footer .brand {
    font-family: var(--font-display);
    color: var(--navy);
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    display: block;
    margin-bottom: 0.45rem;
}
.app-footer .by { display: block; }
.app-footer .links { display: block; margin-top: 0.25rem; font-family: var(--font-mono); font-size: 0.76rem; }
.app-footer a {
    color: var(--muted);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.15s, color 0.15s;
}
.app-footer a:hover { color: var(--navy); border-bottom-color: var(--tan); }
.app-footer .sep { margin: 0 0.55rem; color: #c8c2b3; }

/* =========================================================== */
/* ====  Analytics dashboard widgets (used only on /pages)  ==== */
/* =========================================================== */

/* KPI card: same border-left navy stripe as the answer card */
.kpi-card {
    background: var(--card);
    border: 1px solid var(--rule-soft);
    border-left: 4px solid var(--navy);
    border-radius: 4px;
    padding: 1.1rem 1.25rem 1.2rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    height: 100%;
    min-height: 110px;
}
.kpi-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: var(--muted);
    font-weight: 600;
    margin: 0 0 0.55rem 0;
    font-family: var(--font-body);
}
.kpi-value {
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 600;
    color: var(--navy);
    line-height: 1.05;
    letter-spacing: -0.018em;
}
.kpi-suffix {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--muted);
    margin-top: 0.35rem;
    letter-spacing: 0.01em;
}

/* Section heading above each chart */
.dash-section {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--navy);
    margin: 2rem 0 0.7rem 0;
    letter-spacing: -0.005em;
}
.dash-section-rule {
    height: 1px;
    background: var(--rule);
    border: none;
    margin: 0 0 0.9rem 0;
}

/* Empty state card */
.empty-state {
    background: var(--card);
    border: 1px solid var(--rule-soft);
    border-radius: 6px;
    padding: 3rem 2rem;
    text-align: center;
    margin: 2rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.empty-state .empty-title {
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--navy);
    margin-bottom: 0.6rem;
    letter-spacing: -0.01em;
}
.empty-state .empty-body {
    font-family: var(--font-serif);
    font-size: 1rem;
    color: var(--muted);
    line-height: 1.6;
    max-width: 48ch;
    margin: 0 auto;
}

/* Password gate card */
.password-card {
    background: var(--card);
    border: 1px solid var(--rule-soft);
    border-left: 4px solid var(--burgundy);
    border-radius: 4px;
    padding: 1.6rem 1.8rem;
    margin: 1.2rem 0 1.2rem 0;
    max-width: 520px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.password-card .lock-title {
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--navy);
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.005em;
}
.password-card .lock-body {
    font-family: var(--font-serif);
    color: var(--muted);
    font-size: 0.95rem;
    line-height: 1.55;
    margin: 0;
}

/* Streamlit dataframe: soften the default chrome */
[data-testid="stDataFrame"] {
    border-radius: 6px;
    border: 1px solid var(--rule-soft);
    overflow: hidden;
}
</style>
"""

# ---- Brand wordmark icon ----------------------------------------------------

# Simple, restrained Doric column SVG. Single navy stroke, no fill.
# 36×56 viewport → roughly cap-height of the 3.5rem hero wordmark.
COLUMN_SVG = """\
<svg class="hero-column-svg" width="34" height="54" viewBox="0 0 34 54" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <!-- abacus (top slab) -->
  <rect x="2" y="3"  width="30" height="3" stroke="currentColor" stroke-width="1.4" />
  <!-- echinus -->
  <path d="M5 6 L29 6 L27.5 9.5 L6.5 9.5 Z" stroke="currentColor" stroke-width="1.2" />
  <!-- shaft -->
  <line x1="8"  y1="9.5" x2="8"  y2="46" stroke="currentColor" stroke-width="1" />
  <line x1="12" y1="9.5" x2="12" y2="46" stroke="currentColor" stroke-width="1" />
  <line x1="17" y1="9.5" x2="17" y2="46" stroke="currentColor" stroke-width="1" />
  <line x1="22" y1="9.5" x2="22" y2="46" stroke="currentColor" stroke-width="1" />
  <line x1="26" y1="9.5" x2="26" y2="46" stroke="currentColor" stroke-width="1" />
  <!-- shaft outline -->
  <line x1="6.5" y1="9.5" x2="6.5" y2="46" stroke="currentColor" stroke-width="1.2" />
  <line x1="27.5" y1="9.5" x2="27.5" y2="46" stroke="currentColor" stroke-width="1.2" />
  <!-- base -->
  <rect x="4" y="46" width="26" height="3" stroke="currentColor" stroke-width="1.2" />
  <rect x="2" y="49" width="30" height="3" stroke="currentColor" stroke-width="1.4" />
</svg>
"""


def get_css() -> str:
    """Return the full Stare design-system CSS, wrapped in ``<style>`` tags.

    Inject with ``st.markdown(get_css(), unsafe_allow_html=True)`` once near
    the top of every page.
    """
    return _CSS
