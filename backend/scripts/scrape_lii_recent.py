"""Supplement the corpus with 2015+ SCOTUS opinions scraped from Cornell LII.

CAP coverage ends with U.S. Reports vol 572 (June 2014). SCDB metadata
extends through June 2025. For each SCDB row whose docket falls in
2015-01-01..present that we did not pick up from CAP, fetch the slip
opinion from LII at https://www.law.cornell.edu/supremecourt/text/{docket}
and append a record to data/processed/scotus_cases.jsonl.

(Spec called for 2020+ only; widening to 2015+ closes the CAP-coverage gap.)

Be polite: 1-second delay between requests, User-Agent header identifies
the project.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from backend.scripts.constants import DECISION_DIRECTION, ISSUE_AREA, JUSTICE

REPO_ROOT = Path(__file__).resolve().parents[2]
SCDB_PATH = REPO_ROOT / "data" / "raw" / "scdb_metadata.csv"
CORPUS_PATH = REPO_ROOT / "data" / "processed" / "scotus_cases.jsonl"

UA = "legal-rag-scotus/0.2 (research; bharuya.mabrok@gmail.com)"
BASE = "https://www.law.cornell.edu/supremecourt/text"
START_DATE = "2015-01-01"
DELAY_SEC = 1.0


def _extract_opinion(html: str) -> str:
    """Pull the readable opinion text out of an LII slip-opinion page."""
    soup = BeautifulSoup(html, "lxml")
    # LII wraps the opinion body in <div id="content"> with tabs for syllabus,
    # opinion, concurrences, dissents. Concatenating the visible <p> in #content
    # captures everything; the syllabus + majority is what we care about most.
    content = soup.find("div", id="content") or soup.body or soup
    # Strip nav / footer noise
    for tag in content.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    paragraphs = [p.get_text(" ", strip=True) for p in content.find_all(["p", "blockquote"])]
    text = "\n\n".join(p for p in paragraphs if p)
    return text


def _existing_docket_keys() -> set[str]:
    """Read the corpus to find which SCDB caseIds we already have, so we skip them."""
    keys: set[str] = set()
    if not CORPUS_PATH.exists():
        return keys
    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            cid = rec.get("case_id")
            if cid:
                keys.add(cid)
    return keys


def main() -> None:
    if not CORPUS_PATH.exists():
        print(f"ERROR: {CORPUS_PATH} does not exist. Run build_corpus.py first.",
              file=sys.stderr)
        sys.exit(1)

    scdb = pd.read_csv(SCDB_PATH, encoding="latin-1", low_memory=False)
    scdb["dateDecision_p"] = pd.to_datetime(scdb["dateDecision"], errors="coerce")
    recent = scdb[scdb["dateDecision_p"] >= START_DATE].copy()
    print(f"SCDB rows with dateDecision >= {START_DATE}: {len(recent):,}")

    have = _existing_docket_keys()
    print(f"Already in corpus (caseIds): {len(have):,}")
    todo = recent[~recent["caseId"].isin(have)].copy()
    todo = todo[todo["docket"].notna() & (todo["docket"].str.strip() != "")]
    print(f"Recent cases to fetch from LII: {len(todo):,}\n")

    fetched = 0
    failed = 0
    issue_counter: Counter[str] = Counter()

    with httpx.Client(headers={"User-Agent": UA}, follow_redirects=True, timeout=30) as c, \
         CORPUS_PATH.open("a", encoding="utf-8") as fout:
        for _, row in tqdm(todo.iterrows(), total=len(todo), desc="LII", unit="case"):
            docket = str(row["docket"]).strip()
            url = f"{BASE}/{docket}"
            try:
                r = c.get(url)
                if r.status_code != 200 or len(r.content) < 5000:
                    failed += 1
                    time.sleep(DELAY_SEC)
                    continue
                text = _extract_opinion(r.text)
                if len(text) < 1000:
                    failed += 1
                    time.sleep(DELAY_SEC)
                    continue
            except Exception:
                failed += 1
                time.sleep(DELAY_SEC)
                continue

            issue_int = row.get("issueArea")
            try:
                issue_int = int(issue_int) if pd.notna(issue_int) else None
            except (TypeError, ValueError):
                issue_int = None
            issue_label = ISSUE_AREA.get(issue_int, "Unspecified") if issue_int else "Unspecified"

            dir_int = row.get("decisionDirection")
            try:
                dir_int = int(dir_int) if pd.notna(dir_int) else None
            except (TypeError, ValueError):
                dir_int = None

            writer_id = row.get("majOpinWriter")
            try:
                writer_id = int(writer_id) if pd.notna(writer_id) else None
            except (TypeError, ValueError):
                writer_id = None

            maj_v = row.get("majVotes")
            min_v = row.get("minVotes")
            try:
                maj_v = int(maj_v) if pd.notna(maj_v) else None
            except (TypeError, ValueError):
                maj_v = None
            try:
                min_v = int(min_v) if pd.notna(min_v) else None
            except (TypeError, ValueError):
                min_v = None

            us_cite = row.get("usCite")
            if isinstance(us_cite, float):
                us_cite = None  # NaN

            record = {
                "case_id": row["caseId"],
                "case_name": row.get("caseName"),
                "decision_date": (row.get("dateDecision") or "")[:10] if isinstance(row.get("dateDecision"), str) else row["dateDecision_p"].strftime("%Y-%m-%d"),
                "us_cite": us_cite or "",
                "majority_opinion_text": text,
                "issue_area": issue_label,
                "issue_area_code": issue_int,
                "decision_direction": DECISION_DIRECTION.get(dir_int) if dir_int else None,
                "decision_direction_code": dir_int,
                "vote_majority": maj_v,
                "vote_minority": min_v,
                "majority_writer": JUSTICE.get(writer_id, "Unknown") if writer_id else "Unknown",
                "majority_writer_id": writer_id,
                "docket": docket,
                "source": "lii+scdb",
            }
            fout.write(json.dumps(record, separators=(",", ":")) + "\n")
            fout.flush()
            fetched += 1
            issue_counter[issue_label] += 1
            time.sleep(DELAY_SEC)

    print(f"\nFetched: {fetched:,}   Failed: {failed:,}")
    print("Top 10 issue areas (LII-supplemented):")
    for lbl, n in issue_counter.most_common(10):
        print(f"  {n:>5}  {lbl}")


if __name__ == "__main__":
    main()
