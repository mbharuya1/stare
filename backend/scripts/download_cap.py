"""Download Caselaw Access Project SCOTUS data from static.case.law.

The user-spec referenced the HuggingFace `free-law/Caselaw_Access_Project`
dataset, but that mirror is gated. Harvard publishes the same data publicly
as per-volume bulk archives at https://static.case.law/. We pull modern U.S.
Reports volumes (327+ = 1946+) as .zip archives and stream each case JSON
into ``data/raw/cap_scotus.jsonl`` (one line per case).

Filtering happens at the join step (build_corpus.py) where we keep only
cases that match an SCDB row; SCDB tracks orally argued signed opinions and
gives us the ~9k modern signed opinions the user is targeting.

Network: ~250 small zip files (~750 MB total). Resumable.
"""
from __future__ import annotations

import io
import json
import sys
import time
import zipfile
from pathlib import Path

import httpx
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
OUT_PATH = RAW_DIR / "cap_scotus.jsonl"
ZIP_CACHE = RAW_DIR / "cap_zips"

START_VOLUME = 327          # 1946-02 (vol 327 starts with In re Yamashita)
END_VOLUME = 572            # 2014-06 (last U.S. Reports volume on static.case.law)
MIN_DATE = "1946-01-01"

UA = "legal-rag-scotus/0.2 (research; bharuya.mabrok@gmail.com)"
BASE = "https://static.case.law/us"


def _fetch_volume_zip(client: httpx.Client, vol: int, dest: Path) -> Path | None:
    """Download {vol}.zip with retry. Returns local path or None on 404."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    url = f"{BASE}/{vol}.zip"
    for attempt in range(3):
        try:
            r = client.get(url, timeout=120)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            dest.write_bytes(r.content)
            return dest
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if attempt == 2:
                print(f"\n  WARN vol {vol}: {e}", file=sys.stderr)
                return None
            time.sleep(2 ** attempt)
    return None


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ZIP_CACHE.mkdir(parents=True, exist_ok=True)

    print(f"Downloading CAP U.S. Reports volumes {START_VOLUME}..{END_VOLUME}")
    print(f"Writing to {OUT_PATH}")

    cases_written = 0
    volumes_done = 0
    skipped_pre_1946 = 0

    with httpx.Client(headers={"User-Agent": UA}, follow_redirects=True) as client, \
         OUT_PATH.open("w", encoding="utf-8") as out_fp:
        bar = tqdm(range(START_VOLUME, END_VOLUME + 1), desc="volumes", unit="vol")
        for vol in bar:
            zip_path = _fetch_volume_zip(client, vol, ZIP_CACHE / f"{vol}.zip")
            if zip_path is None:
                continue
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    # Per-case JSONs live under json/ inside each volume zip.
                    case_names = [n for n in zf.namelist()
                                  if n.startswith("json/") and n.endswith(".json")]
                    for name in case_names:
                        with zf.open(name) as f:
                            try:
                                case = json.load(f)
                            except json.JSONDecodeError:
                                continue
                        dd = (case.get("decision_date") or "")[:10]
                        if dd and dd < MIN_DATE:
                            skipped_pre_1946 += 1
                            continue
                        out_fp.write(json.dumps(case, separators=(",", ":")) + "\n")
                        cases_written += 1
                volumes_done += 1
            except zipfile.BadZipFile:
                print(f"\n  WARN vol {vol}: bad zip, deleting cache", file=sys.stderr)
                zip_path.unlink(missing_ok=True)
                continue
            bar.set_postfix(cases=cases_written, vols=volumes_done)

    print(f"\nDone. Volumes processed: {volumes_done}")
    print(f"Cases written: {cases_written}")
    print(f"Skipped (pre-1946): {skipped_pre_1946}")
    print(f"Output: {OUT_PATH}  ({OUT_PATH.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    main()
