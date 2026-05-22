"""
Crawl 3 Hansard + 3 Bill PDFs, download them, and extract text.

All output goes to gitignored directories:
  data/raw/parliament_my/pdf/<year>/<filename>.pdf
  data/raw/parliament_my/pdf/<year>/<filename>.meta.json
  data/derived/parliament_my/extracted/<year>/<stem>.md

Run from repo root:
  PYTHONPATH=src python scripts/sample_crawl.py [--insecure]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path

# --- bootstrap PYTHONPATH so this script is runnable from the repo root ---
_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

import requests
from lib.paths import repo_root
from lib.pipeline.extract import extract_pdf
from lib.sources.my.parliament_my.crawl import _is_dr_arkib_url, _is_hansard_arkib_url
from lib.sources.my.parliament_my.dhtmlx_arkib import (
    list_bill_records_arkib_dhtmlx_sweep,
    list_hansard_records_arkib_dhtmlx_sweep,
)
from lib.sources.my.parliament_my import config


ADAPTER_ID = "parliament_my"
N_EACH = 3  # how many PDFs to sample per type


def _raw_dir(year: str) -> Path:
    d = repo_root() / "data" / "raw" / ADAPTER_ID / "pdf" / year
    d.mkdir(parents=True, exist_ok=True)
    return d


def _derived_dir(year: str) -> Path:
    d = repo_root() / "data" / "derived" / ADAPTER_ID / "extracted" / year
    d.mkdir(parents=True, exist_ok=True)
    return d


def _download(url: str, dest: Path, *, verify: bool, cookies: dict | None = None) -> dict:
    """Download url -> dest. Returns meta dict."""
    try:
        resp = requests.get(
            url,
            verify=verify,
            timeout=config.FETCH_TIMEOUT_S,
            headers=config.DEFAULT_HEADERS,
            cookies=cookies or {},
            stream=True,
        )
        resp.raise_for_status()
        raw = resp.content
        sha = hashlib.sha256(raw).hexdigest()
        dest.write_bytes(raw)
        meta = {"url": url, "sha256": sha, "bytes": len(raw), "status": "ok"}
        dest.with_suffix(".meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return meta
    except Exception as e:
        return {"url": url, "status": "error", "error": str(e)}


def run(verify: bool) -> None:
    hansard_seed = "https://www.parlimen.gov.my/hansard-dewan-negara.html?uweb=dn&lang=bm&arkib=yes"
    bills_seed = "https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&arkib=yes"

    # ------------------------------------------------------------------ bills
    print("\n=== Crawling bills (Parliament 15 / DR arkib) ===")
    bill_rows, bill_cookies = list_bill_records_arkib_dhtmlx_sweep(
        bills_seed,
        verify_tls=verify,
        max_nodes=200,
        verbose=True,
        log=sys.stderr,
    )
    # Pick rows that have a pdf_url, prefer 2024 if available
    bill_sample = [r for r in bill_rows if r.get("pdf_url")]
    bill_sample.sort(key=lambda r: r.get("year", ""), reverse=True)
    bill_sample = bill_sample[:N_EACH]
    print(f"  Selected {len(bill_sample)} bill(s) for download")

    # ---------------------------------------------------------------- hansard
    print("\n=== Crawling Hansard (DN arkib, Parliament 15) ===")
    hansard_rows = list_hansard_records_arkib_dhtmlx_sweep(
        hansard_seed,
        verify_tls=verify,
        parliament_filter=[15],
        max_nodes=500,
        verbose=True,
        log=sys.stderr,
    )
    hansard_sample = [r for r in hansard_rows if r.get("pdf_url")]
    hansard_sample.sort(key=lambda r: r.get("sitting_date", ""), reverse=True)
    hansard_sample = hansard_sample[:N_EACH]
    print(f"  Selected {len(hansard_sample)} hansard sitting(s) for download")

    # ---------------------------------------------------------------- download
    print("\n=== Downloading PDFs ===")
    downloaded: list[tuple[Path, str]] = []  # (pdf_path, year)

    def dl(url: str, year: str, filename: str, cookies: dict | None = None) -> None:
        dest = _raw_dir(year) / filename
        if dest.exists():
            print(f"  [skip] {filename} already exists")
            downloaded.append((dest, year))
            return
        meta = _download(url, dest, verify=verify, cookies=cookies)
        status = meta.get("status", "?")
        size = meta.get("bytes", 0)
        print(f"  [{status}] {filename}  ({size:,} bytes)  ->  {dest.relative_to(repo_root())}")
        if status == "ok":
            downloaded.append((dest, year))

    for r in bill_sample:
        url = r.get("pdf_url", "")
        year = r.get("year", "unknown")
        fn = url.rsplit("/", 1)[-1] or "bill.pdf"
        dl(url, year, fn, cookies=bill_cookies)

    for r in hansard_sample:
        url = r.get("pdf_url", "")
        date = (r.get("sitting_date") or "unknown")[:4]  # year from ISO date
        fn = r.get("pdf_filename", url.rsplit("/", 1)[-1] or "hansard.pdf")
        dl(url, date, fn)

    # ----------------------------------------------------------------- extract
    print("\n=== Extracting text from PDFs ===")
    for pdf_path, year in downloaded:
        stem = pdf_path.stem
        out_dir = _derived_dir(year)
        out_md = out_dir / f"{stem}.md"
        if out_md.exists():
            print(f"  [skip] {stem}.md already exists")
            continue
        text, method = extract_pdf(pdf_path)
        chars = len(text.strip())
        if chars >= 100:
            out_md.write_text(text, encoding="utf-8")
            print(f"  [ok/{method}] {stem}.md  ({chars:,} chars)  ->  {out_md.relative_to(repo_root())}")
            # Print first 300 chars as preview
            preview = text.strip()[:300].replace("\n", " ")
            print(f"    preview: {preview!r}")
        else:
            suspect = out_dir / f"{stem}.suspect.md"
            suspect.write_text(text, encoding="utf-8")
            print(f"  [suspect/{method}] {stem} — only {chars} chars, written to {suspect.name}")

    print("\nDone.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Sample crawl: 3 hansard + 3 bill PDFs -> extract text.")
    ap.add_argument("--insecure", action="store_true", help="Disable TLS verification (dev only).")
    args = ap.parse_args()
    if args.insecure:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    run(verify=not args.insecure)
