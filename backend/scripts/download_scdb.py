"""Download the Supreme Court Database (SCDB) modern, case-centered, citation file.

SCDB at scdb.la.psu.edu publishes annual releases. The case-centered /
citation file gives one row per case (deduplicated by citation), which is
what we want for joining against CAP. We download the modern (1946-) CSV.

We try the most recent likely releases and fall back to older ones. SCDB
keeps prior releases available at predictable URLs.
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import httpx
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
OUT_CSV = RAW_DIR / "scdb_metadata.csv"

UA = "legal-rag-scotus/0.2 (research; bharuya.mabrok@gmail.com)"

# Try newest first. SCDB names releases YYYY_NN (release N of year YYYY).
# As of 2026-05 the current release is 2025_01.
CANDIDATE_RELEASES = [
    "2025_01", "2024_01", "2023_01", "2022_01",
]
# Modern (1946-) case-centered citation file. Hosted on supremecourtdatabase.org
# (mirrored at scdb.la.psu.edu but the active download URLs are on the .org).
URL_TEMPLATE = "http://supremecourtdatabase.org/_brickFiles/{rel}/SCDB_{rel}_caseCentered_Citation.csv.zip"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client(headers={"User-Agent": UA}, follow_redirects=True, timeout=120) as c:
        last_err: Exception | None = None
        for rel in CANDIDATE_RELEASES:
            url = URL_TEMPLATE.format(rel=rel)
            print(f"Trying {url}")
            try:
                r = c.get(url)
                r.raise_for_status()
                print(f"  OK ({len(r.content)/1_000_000:.1f} MB)")
                with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
                    csv_name = next(n for n in zf.namelist() if n.endswith(".csv"))
                    with zf.open(csv_name) as f:
                        OUT_CSV.write_bytes(f.read())
                print(f"  extracted -> {OUT_CSV}")
                break
            except Exception as e:
                print(f"  fail: {e}")
                last_err = e
                continue
        else:
            raise RuntimeError(f"All SCDB candidate URLs failed; last error: {last_err}")

    # Try multiple encodings — SCDB files are typically Windows-1252.
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(OUT_CSV, encoding=enc, low_memory=False)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise RuntimeError("Could not decode SCDB CSV with any common encoding")

    print(f"\nRow count: {len(df):,}")
    if "dateDecision" in df.columns:
        dd = pd.to_datetime(df["dateDecision"], errors="coerce")
        print(f"Date range: {dd.min().date()}  ..  {dd.max().date()}")
    if "usCite" in df.columns:
        non_null = df["usCite"].notna().sum()
        print(f"Rows with usCite: {non_null:,} / {len(df):,}")
    print(f"Columns: {list(df.columns)}")


if __name__ == "__main__":
    main()
