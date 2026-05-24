"""Stare design system for Streamlit.

Single entry point :func:`inject_css` dumps a full stylesheet on every page:
- Loads Playfair Display + Inter + JetBrains Mono
- Defines CSS variables matching the Next.js landing's design tokens
- Hides every Streamlit default chrome element
- Defines .stare-* utility classes used by app.py
"""
from __future__ import annotations

import streamlit as st


_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

<style>
/* ───────────────────────── design tokens ───────────────────────── */
:root {
    /* Navy scale (base #1a2540) */
    --navy-50:  #f0f3fa;
    --navy-100: #dde4f1;
    --navy-200: #b6c5e2;
    --navy-300: #8aa3cd;
    --navy-400: #5d7fb3;
    --navy-500: #3b5c95;
    --navy-600: #2c4476;
    --navy-700: #233458;
    --navy-800: #1a2540;
    --navy-900: #121a30;
    --navy-950: #0a0e1c;

    /* Cream / paper / mist */
    --cream:    #fafaf7;
    --paper:    #f5f3ee;
    --mist:     #e8e4dc;
    --mist-2:   #d8d3c8;

    /* Burgundy accent */
    --burgundy-100: #f2dadc;
    --burgundy-300: #c08188;
    --burgundy-500: #9e4951;
    --burgundy-700: #722f37;
    --burgundy-900: #471c22;

    --ink:      #0a0e1a;

    /* Type scale */
    --t-xs:   12px;
    --t-sm:   14px;
    --t-base: 16px;
    --t-lg:   18px;
    --t-xl:   20px;
    --t-2xl:  24px;
    --t-3xl:  30px;
    --t-4xl:  36px;
    --t-5xl:  48px;
    --t-6xl:  60px;
    --t-7xl:  72px;

    /* Spacing scale */
    --s-1: 4px;  --s-2: 8px;  --s-3: 12px; --s-4: 16px;
    --s-6: 24px; --s-8: 32px; --s-12: 48px; --s-16: 64px;
    --s-24: 96px; --s-32: 128px;

    /* Radii */
    --r-sm: 4px;  --r-md: 8px; --r-lg: 12px; --r-xl: 16px; --r-2xl: 24px;

    /* Shadows (Linear-style: soft, multi-layer) */
    --shadow-sm: 0 1px 2px rgba(26,37,64,0.04), 0 1px 1px rgba(26,37,64,0.03);
    --shadow-md: 0 4px 8px -2px rgba(26,37,64,0.06), 0 2px 4px -1px rgba(26,37,64,0.04);
    --shadow-lg: 0 12px 24px -6px rgba(26,37,64,0.10), 0 4px 8px -2px rgba(26,37,64,0.05);
    --shadow-xl: 0 24px 48px -12px rgba(26,37,64,0.14), 0 8px 16px -4px rgba(26,37,64,0.06);

    /* Font stacks */
    --font-display: 'Playfair Display', Georgia, serif;
    --font-body:    'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono:    'JetBrains Mono', 'SF Mono', Menlo, monospace;
}

/* ───────────────────────── kill Streamlit chrome ───────────────────────── */
#MainMenu, footer, header[data-testid="stHeader"], div[data-testid="stToolbar"],
div[data-testid="stDecoration"], div[data-testid="stStatusWidget"],
.stDeployButton { display: none !important; }

/* Hide the "Made with Streamlit" footer */
footer:after { content: none !important; }
footer { visibility: hidden !important; }

/* Reset top padding so our sticky nav sits at viewport top */
section[data-testid="stMain"] > div.block-container,
.main .block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 100% !important;
}

/* ───────────────────────── base typography ───────────────────────── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: var(--font-body);
    background: var(--cream);
    color: var(--navy-800);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ───────────────────────── sticky header bar ───────────────────────── */
.stare-header {
    position: sticky;
    top: 0; left: 0; right: 0;
    z-index: 100;
    height: 60px;
    background: var(--navy-800);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 var(--s-8);
    border-bottom: 1px solid var(--navy-900);
    width: 100%;
}
.stare-header .wordmark-group {
    display: flex; align-items: baseline; gap: var(--s-3);
}
.stare-header .wordmark {
    font-family: var(--font-display);
    font-weight: 600;
    font-size: var(--t-2xl);
    letter-spacing: -0.02em;
    color: var(--cream);
}
.stare-header .mode-badge {
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--cream);
    background: rgba(250, 250, 247, 0.10);
    border: 1px solid rgba(250, 250, 247, 0.18);
    padding: 3px 9px;
    border-radius: 9999px;
    line-height: 1;
}
.stare-header .nav-right {
    display: flex; align-items: center; gap: var(--s-6);
}
.stare-header .nav-link {
    font-family: var(--font-body);
    font-size: var(--t-sm);
    color: var(--cream);
    opacity: 0.85;
    text-decoration: none;
    transition: opacity .15s ease;
}
.stare-header .nav-link:hover { opacity: 1; }

/* ───────────────────────── disclaimer banner ───────────────────────── */
.stare-disclaimer {
    background: rgba(114, 47, 55, 0.10);
    border-bottom: 1px solid rgba(114, 47, 55, 0.18);
    color: var(--navy-800);
    font-family: var(--font-body);
    font-size: var(--t-sm);
    text-align: center;
    padding: var(--s-3) var(--s-4);
    width: 100%;
}

/* ───────────────────────── page shell ───────────────────────── */
.stare-page {
    max-width: 900px;
    margin: 0 auto;
    padding: var(--s-16) var(--s-6) var(--s-24);
}

/* ───────────────────────── hero (empty state) ───────────────────────── */
.stare-hero h1 {
    font-family: var(--font-display);
    font-weight: 600;
    font-size: var(--t-4xl);
    color: var(--navy-900);
    letter-spacing: -0.025em;
    line-height: 1.15;
    margin: 0 0 var(--s-4);
}
.stare-hero p.subtitle {
    font-family: var(--font-body);
    font-size: var(--t-base);
    color: rgba(26,37,64,0.70);
    margin: 0 0 var(--s-12);
    max-width: 640px;
}

/* ───────────────────────── sample chips ───────────────────────── */
.stare-chips { display: flex; flex-wrap: wrap; gap: var(--s-3); margin: var(--s-6) 0 var(--s-12); }
.stare-chip-label {
    font-family: var(--font-body);
    font-size: var(--t-xs);
    font-weight: 500;
    color: rgba(26,37,64,0.55);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: var(--s-3);
}
div[data-testid="column"] button[kind="secondary"],
div[data-testid="column"] [data-testid="stBaseButton-secondary"] {
    background: var(--paper) !important;
    border: 1px solid var(--mist) !important;
    color: var(--navy-800) !important;
    border-radius: 9999px !important;
    padding: var(--s-2) var(--s-4) !important;
    font-family: var(--font-body) !important;
    font-size: var(--t-sm) !important;
    font-weight: 400 !important;
    height: auto !important;
    line-height: 1.4 !important;
    text-align: left !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all .15s ease !important;
    white-space: normal !important;
    min-height: 40px;
}
div[data-testid="column"] button[kind="secondary"]:hover,
div[data-testid="column"] [data-testid="stBaseButton-secondary"]:hover {
    background: white !important;
    border-color: var(--navy-300) !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-md) !important;
}

/* ───────────────────────── query input ───────────────────────── */
.stArea, .stTextArea {
    margin-top: var(--s-4) !important;
}
.stTextArea textarea {
    font-family: var(--font-body) !important;
    font-size: var(--t-base) !important;
    color: var(--navy-900) !important;
    background: white !important;
    border: 1px solid var(--mist) !important;
    border-radius: var(--r-lg) !important;
    padding: var(--s-4) var(--s-4) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: border-color .15s ease, box-shadow .15s ease !important;
    min-height: 110px !important;
}
.stTextArea textarea:focus {
    border-color: var(--navy-500) !important;
    box-shadow: 0 0 0 4px rgba(26,37,64,0.10) !important;
    outline: none !important;
}
.stTextArea label,
div[data-testid="stWidgetLabel"] label {
    font-family: var(--font-body) !important;
    font-size: var(--t-sm) !important;
    font-weight: 500 !important;
    color: var(--navy-800) !important;
}

/* Primary submit button. Streamlit uses kind="primary" OR
   kind="primaryFormSubmit" (in st.form). Both selectors needed. */
button[kind="primary"],
button[kind="primaryFormSubmit"],
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"] {
    background: var(--navy-800) !important;
    color: var(--cream) !important;
    border: 1px solid var(--navy-900) !important;
    border-radius: var(--r-lg) !important;
    font-family: var(--font-body) !important;
    font-size: var(--t-base) !important;
    font-weight: 500 !important;
    padding: var(--s-3) var(--s-6) !important;
    height: auto !important;
    box-shadow: var(--shadow-md) !important;
    transition: transform .12s ease, box-shadow .15s ease !important;
}
button[kind="primary"]:hover,
button[kind="primaryFormSubmit"]:hover,
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    background: var(--navy-700) !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-lg) !important;
    color: var(--cream) !important;
}
button[kind="primary"]:active,
button[kind="primaryFormSubmit"]:active { transform: scale(0.98); }

/* ───────────────────────── Q&A turn card stack ───────────────────────── */
.stare-turn { margin: var(--s-12) 0; }
.stare-question-card {
    background: var(--paper);
    border-left: 3px solid var(--navy-800);
    border-radius: var(--r-md);
    padding: var(--s-4) var(--s-6);
    margin-bottom: var(--s-6);
}
.stare-question-card .label {
    font-family: var(--font-mono);
    font-size: var(--t-xs);
    color: rgba(26,37,64,0.55);
    text-transform: uppercase;
    letter-spacing: 0.10em;
    margin-bottom: var(--s-2);
}
.stare-question-card .question {
    font-family: var(--font-body);
    font-size: var(--t-lg);
    color: var(--navy-900);
    font-weight: 500;
    line-height: 1.45;
}

.stare-answer-card {
    background: white;
    border: 1px solid var(--mist);
    border-radius: var(--r-xl);
    padding: var(--s-8);
    box-shadow: var(--shadow-sm);
}
.stare-answer-card .answer-body {
    font-family: var(--font-body);
    font-size: var(--t-base);
    color: var(--navy-900);
    line-height: 1.7;
}
.stare-answer-card .answer-body p { margin: 0 0 var(--s-4); }
.stare-answer-card .answer-body p:last-child { margin-bottom: 0; }

/* Inline citation badges, applied after-the-fact by app.py */
.stare-cite {
    display: inline-flex;
    align-items: center;
    background: var(--navy-50);
    color: var(--navy-700);
    border: 1px solid var(--navy-100);
    border-radius: var(--r-sm);
    padding: 1px 6px;
    margin: 0 1px;
    font-family: var(--font-mono);
    font-size: 0.82em;
    font-weight: 500;
    white-space: nowrap;
    text-decoration: none;
}

/* Citations list */
.stare-citations-header {
    font-family: var(--font-display);
    font-size: var(--t-2xl);
    font-weight: 600;
    color: var(--navy-900);
    margin: var(--s-8) 0 var(--s-4);
    letter-spacing: -0.015em;
}
.stare-citation {
    background: white;
    border: 1px solid var(--mist);
    border-left: 3px solid var(--navy-800);
    border-radius: var(--r-md);
    padding: var(--s-4) var(--s-6);
    margin-bottom: var(--s-3);
}
.stare-citation .case-name {
    font-family: var(--font-display);
    font-size: var(--t-lg);
    font-weight: 600;
    color: var(--navy-900);
    margin-bottom: 2px;
    letter-spacing: -0.01em;
}
.stare-citation .case-meta {
    font-family: var(--font-mono);
    font-size: var(--t-sm);
    color: rgba(26,37,64,0.60);
    margin-bottom: var(--s-3);
}
.stare-citation .quote {
    font-family: var(--font-body);
    font-style: italic;
    font-size: 15px;
    color: var(--navy-800);
    line-height: 1.55;
    padding-left: var(--s-3);
    border-left: 2px solid var(--mist);
    margin: 0;
}

/* ───────────────────────── retrieved-sources expander ───────────────────────── */
details.stare-sources {
    margin-top: var(--s-6);
    border: 1px solid var(--mist);
    border-radius: var(--r-md);
    background: var(--paper);
    padding: 0;
    overflow: hidden;
}
details.stare-sources > summary {
    list-style: none;
    cursor: pointer;
    padding: var(--s-3) var(--s-6);
    font-family: var(--font-body);
    font-size: var(--t-sm);
    font-weight: 500;
    color: var(--navy-800);
    user-select: none;
}
details.stare-sources > summary::-webkit-details-marker { display: none; }
details.stare-sources > summary:after {
    content: "▾";
    float: right;
    color: rgba(26,37,64,0.40);
    transition: transform .15s ease;
}
details.stare-sources[open] > summary:after { transform: rotate(180deg); }
details.stare-sources .source-list { padding: var(--s-4) var(--s-6) var(--s-6); }
.stare-source {
    padding: var(--s-3) 0;
    border-bottom: 1px solid var(--mist);
}
.stare-source:last-child { border-bottom: none; }
.stare-source .case-name {
    font-family: var(--font-display);
    font-size: var(--t-base);
    font-weight: 600;
    color: var(--navy-900);
}
.stare-source .meta {
    font-family: var(--font-mono);
    font-size: var(--t-xs);
    color: rgba(26,37,64,0.55);
    margin-bottom: var(--s-2);
}
.stare-source .excerpt {
    font-family: var(--font-body);
    font-size: var(--t-sm);
    color: var(--navy-800);
    line-height: 1.55;
    margin: var(--s-2) 0 0;
}

/* Score bar */
.stare-scorebar {
    background: var(--mist);
    border-radius: 999px;
    height: 4px;
    width: 100%;
    overflow: hidden;
    margin: var(--s-2) 0 var(--s-3);
    position: relative;
}
.stare-scorebar > div {
    background: var(--navy-800);
    height: 100%;
    border-radius: 999px;
    transition: width .3s ease;
}
.stare-scorebar-label {
    font-family: var(--font-mono);
    font-size: var(--t-xs);
    color: rgba(26,37,64,0.55);
}

/* ───────────────────────── metadata footer ───────────────────────── */
.stare-meta {
    font-family: var(--font-mono);
    font-size: var(--t-xs);
    color: rgba(26,37,64,0.50);
    margin-top: var(--s-6);
    padding-top: var(--s-3);
    border-top: 1px solid var(--mist);
}

/* ───────────────────────── refusal cards ───────────────────────── */
.stare-refusal {
    background: var(--paper);
    border: 1px solid var(--mist);
    border-radius: var(--r-xl);
    padding: var(--s-8);
    text-align: left;
}
.stare-refusal .label {
    font-family: var(--font-mono);
    font-size: var(--t-xs);
    color: var(--burgundy-700);
    text-transform: uppercase;
    letter-spacing: 0.10em;
    margin-bottom: var(--s-3);
}
.stare-refusal .text {
    font-family: var(--font-body);
    font-size: var(--t-lg);
    color: var(--navy-900);
    line-height: 1.55;
}
.stare-refusal .hint {
    font-family: var(--font-body);
    font-size: var(--t-sm);
    color: rgba(26,37,64,0.65);
    margin-top: var(--s-4);
}

/* ───────────────────────── meta-answer card ───────────────────────── */
.stare-meta-card {
    background: white;
    border: 1px solid var(--mist);
    border-radius: var(--r-xl);
    padding: var(--s-6) var(--s-8);
    box-shadow: var(--shadow-sm);
}
.stare-meta-card .label {
    font-family: var(--font-mono);
    font-size: var(--t-xs);
    color: rgba(26,37,64,0.55);
    text-transform: uppercase;
    letter-spacing: 0.10em;
    margin-bottom: var(--s-3);
}
.stare-meta-card .body {
    font-family: var(--font-body);
    font-size: var(--t-base);
    color: var(--navy-900);
    line-height: 1.7;
    white-space: pre-line;
}

/* ───────────────────────── loading skeleton ───────────────────────── */
@keyframes pulse-bg {
    0%, 100% { background-color: var(--mist); }
    50%      { background-color: var(--paper); }
}
.stare-skeleton {
    background: var(--mist);
    border-radius: var(--r-md);
    margin-bottom: var(--s-3);
    animation: pulse-bg 1.4s ease-in-out infinite;
}
.stare-skeleton.h1 { height: 28px; width: 60%; }
.stare-skeleton.p  { height: 14px; width: 100%; margin-bottom: var(--s-2); }
.stare-skeleton.p.short { width: 70%; }
.stare-skeleton-card {
    background: white;
    border: 1px solid var(--mist);
    border-radius: var(--r-xl);
    padding: var(--s-6);
    margin-bottom: var(--s-3);
}

/* ───────────────────────── backend-error full-page ───────────────────────── */
.stare-error {
    max-width: 720px;
    margin: var(--s-16) auto;
    padding: var(--s-8);
    background: white;
    border: 1px solid var(--burgundy-100);
    border-left: 4px solid var(--burgundy-700);
    border-radius: var(--r-xl);
    box-shadow: var(--shadow-md);
}
.stare-error h2 {
    font-family: var(--font-display);
    font-size: var(--t-3xl);
    color: var(--burgundy-700);
    margin: 0 0 var(--s-4);
}
.stare-error p { font-family: var(--font-body); color: var(--navy-800); line-height: 1.6; }
.stare-error code {
    font-family: var(--font-mono);
    font-size: var(--t-sm);
    background: var(--paper);
    padding: 2px 6px;
    border-radius: var(--r-sm);
    color: var(--navy-900);
}

/* Streamlit "running" spinner, restyle */
div[data-testid="stSpinner"] { display: none; }

/* ───────────────────────── mobile ───────────────────────── */
@media (max-width: 640px) {
    .stare-page { padding: var(--s-12) var(--s-4) var(--s-16); }
    .stare-hero h1 { font-size: var(--t-3xl); }
    .stare-header { padding: 0 var(--s-4); }
    .stare-header .nav-link:not(.back-link) { display: none; }
}
</style>
"""


def inject_css() -> None:
    """Inject Stare's design system into the current Streamlit page."""
    st.markdown(_CSS, unsafe_allow_html=True)
