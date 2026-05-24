"""Join CAP cases with SCDB metadata into the processed corpus.

Reads:
  data/raw/cap_scotus.jsonl     full CAP opinions (1946-2014)
  data/raw/scdb_metadata.csv    SCDB modern, case-centered, citation file

Writes:
  data/processed/scotus_cases.jsonl  one JSON record per joined case

Join key: U.S. Reports citation, e.g. "327 U.S. 1". CAP has a citations list
(an item with type="official" carries the U.S. cite); SCDB has it in usCite.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from backend.scripts.constants import DECISION_DIRECTION, ISSUE_AREA, JUSTICE

REPO_ROOT = Path(__file__).resolve().parents[2]
CAP_PATH = REPO_ROOT / "data" / "raw" / "cap_scotus.jsonl"
SCDB_PATH = REPO_ROOT / "data" / "raw" / "scdb_metadata.csv"
OUT_PATH = REPO_ROOT / "data" / "processed" / "scotus_cases.jsonl"

CITE_RE = re.compile(r"(\d+)\s*U\.\s*S\.\s*(\d+)")


def _normalize_cite(cite: str | None) -> str | None:
    """Normalize 'X U.S. Y' / 'X U. S. Y' / 'X U.S.  Y' to 'X U.S. Y'."""
    if not cite or not isinstance(cite, str):
        return None
    m = CITE_RE.search(cite)
    return f"{m.group(1)} U.S. {m.group(2)}" if m else None


def _cap_us_cite(case: dict) -> str | None:
    for c in case.get("citations", []) or []:
        if c.get("type") == "official":
            n = _normalize_cite(c.get("cite"))
            if n:
                return n
    # fallback: first cite that looks like U.S.
    for c in case.get("citations", []) or []:
        n = _normalize_cite(c.get("cite"))
        if n:
            return n
    return None


def _cap_opinion_text(case: dict) -> str:
    """Pull the majority opinion (or all opinions concatenated) from CAP casebody."""
    body = case.get("casebody") or {}
    # CAP wraps the content in different shapes across releases. Try both.
    if isinstance(body, dict) and "data" in body and isinstance(body["data"], dict):
        body = body["data"]

    opinions = body.get("opinions") if isinstance(body, dict) else None
    if isinstance(opinions, list) and opinions:
        # Prefer the majority opinion if labeled; otherwise concat all.
        majority = [o for o in opinions if (o.get("type") or "").lower() == "majority"]
        chosen = majority if majority else opinions
        return "\n\n".join(o.get("text", "") for o in chosen if o.get("text"))

    # Some volumes use plain text body
    if isinstance(body, dict) and isinstance(body.get("text"), str):
        return body["text"]
    return ""


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # ----- SCDB -----
    print(f"Loading SCDB from {SCDB_PATH}")
    scdb = pd.read_csv(SCDB_PATH, encoding="latin-1", low_memory=False)
    scdb["usCite_norm"] = scdb["usCite"].apply(_normalize_cite)
    scdb_by_cite: dict[str, dict] = {}
    for _, row in scdb.iterrows():
        cite = row.get("usCite_norm")
        if cite and cite not in scdb_by_cite:
            scdb_by_cite[cite] = row.to_dict()
    print(f"  SCDB rows: {len(scdb):,}   indexed by U.S. cite: {len(scdb_by_cite):,}")

    # ----- CAP + JOIN -----
    print(f"\nStreaming CAP from {CAP_PATH}")
    joined = 0
    cap_total = 0
    cap_no_cite = 0
    cap_unmatched = 0
    issue_counter: Counter[str] = Counter()
    matched_scdb_cites: set[str] = set()

    with CAP_PATH.open("r", encoding="utf-8") as fin, \
         OUT_PATH.open("w", encoding="utf-8") as fout:
        bar = tqdm(fin, desc="cases", unit="case")
        for line in bar:
            cap_total += 1
            try:
                case = json.loads(line)
            except json.JSONDecodeError:
                continue
            cite = _cap_us_cite(case)
            if not cite:
                cap_no_cite += 1
                continue
            scdb_row = scdb_by_cite.get(cite)
            if not scdb_row:
                cap_unmatched += 1
                continue

            text = _cap_opinion_text(case)
            if not text or len(text) < 200:
                # Skip orders / minute entries with negligible body
                continue

            issue_int = scdb_row.get("issueArea")
            try:
                issue_int = int(issue_int) if pd.notna(issue_int) else None
            except (TypeError, ValueError):
                issue_int = None
            issue_label = ISSUE_AREA.get(issue_int, "Unspecified") if issue_int else "Unspecified"

            dir_int = scdb_row.get("decisionDirection")
            try:
                dir_int = int(dir_int) if pd.notna(dir_int) else None
            except (TypeError, ValueError):
                dir_int = None

            writer_id = scdb_row.get("majOpinWriter")
            try:
                writer_id = int(writer_id) if pd.notna(writer_id) else None
            except (TypeError, ValueError):
                writer_id = None
            writer_name = JUSTICE.get(writer_id, "Unknown") if writer_id else "Unknown"

            maj_votes = scdb_row.get("majVotes")
            min_votes = scdb_row.get("minVotes")
            try:
                maj_votes = int(maj_votes) if pd.notna(maj_votes) else None
            except (TypeError, ValueError):
                maj_votes = None
            try:
                min_votes = int(min_votes) if pd.notna(min_votes) else None
            except (TypeError, ValueError):
                min_votes = None

            decision_date = (case.get("decision_date") or scdb_row.get("dateDecision") or "")[:10]

            record = {
                "case_id": scdb_row.get("caseId"),
                "case_name": case.get("name_abbreviation") or case.get("name") or scdb_row.get("caseName"),
                "decision_date": decision_date,
                "us_cite": cite,
                "majority_opinion_text": text,
                "issue_area": issue_label,
                "issue_area_code": issue_int,
                "decision_direction": DECISION_DIRECTION.get(dir_int) if dir_int else None,
                "decision_direction_code": dir_int,
                "vote_majority": maj_votes,
                "vote_minority": min_votes,
                "majority_writer": writer_name,
                "majority_writer_id": writer_id,
                "source": "cap+scdb",
            }
            fout.write(json.dumps(record, separators=(",", ":")) + "\n")
            joined += 1
            matched_scdb_cites.add(cite)
            issue_counter[issue_label] += 1
            bar.set_postfix(joined=joined)

    scdb_only = len(scdb_by_cite) - len(matched_scdb_cites)

    print("\n--- Join stats ---")
    print(f"CAP cases read:               {cap_total:,}")
    print(f"  no U.S. cite:               {cap_no_cite:,}")
    print(f"  unmatched in SCDB:          {cap_unmatched:,}")
    print(f"Joined records written:       {joined:,}")
    print(f"SCDB rows with no CAP match:  {scdb_only:,}  "
          f"(these are 2015-2025 cases we'll fill from LII)")
    print(f"\nOutput: {OUT_PATH}  ({OUT_PATH.stat().st_size / 1_000_000:.1f} MB)")

    print("\nTop 10 issue areas:")
    for label, n in issue_counter.most_common(10):
        print(f"  {n:>5}  {label}")


if __name__ == "__main__":
    main()
