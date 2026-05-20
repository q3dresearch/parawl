"""
Pipeline stage 1: PDF → Markdown extraction.

Primary:  pymupdf4llm — structured Markdown, preserves headings and clause structure (0.1s, 96%)
Fallback: pypdf       — plain text, pure Python, no C deps (3.5s, 96%)

Output: data/derived/<adapter>/extracted/<year>/<bill_id>/text.md
        data/derived/<adapter>/extracted/<year>/<bill_id>/suspect.md  (low-yield only)
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from lib.paths import repo_root

SUSPECT_THRESHOLD = 100


def _extract_pymupdf4llm(pdf_path: Path) -> str:
    import pymupdf4llm
    return pymupdf4llm.to_markdown(str(pdf_path))


def _extract_pypdf(pdf_path: Path) -> str:
    from pypdf import PdfReader
    pages = PdfReader(str(pdf_path)).pages
    return "\n\n".join(p.extract_text() or "" for p in pages)


def extract_pdf(pdf_path: Path) -> tuple[str, str]:
    """Return (text, method). Tries primary then fallback."""
    for fn, name in [(_extract_pymupdf4llm, "pymupdf4llm"), (_extract_pypdf, "pypdf")]:
        try:
            text = fn(pdf_path)
            if len(text.strip()) >= SUSPECT_THRESHOLD:
                return text, name
        except Exception:
            continue
    return "", "failed"


def extract_bill(pdf_path: Path, out_dir: Path, force: bool = False) -> dict:
    """
    Extract one bill PDF to out_dir/text.md.
    Returns dict with keys: status, method, chars, path.
    """
    out_md = out_dir / "text.md"
    suspect_md = out_dir / "suspect.md"

    if not force and out_md.exists():
        return {"status": "skip", "path": str(out_md)}

    if not pdf_path.exists():
        return {"status": "error", "error": f"not found: {pdf_path}"}

    text, method = extract_pdf(pdf_path)
    chars = len(text.strip())
    out_dir.mkdir(parents=True, exist_ok=True)

    if chars < SUSPECT_THRESHOLD:
        suspect_md.write_text(
            f"Low extraction yield ({chars} chars). Likely scanned/image PDF. Method: {method}\n",
            encoding="utf-8",
        )
        return {"status": "suspect", "chars": chars, "method": method, "path": str(suspect_md)}

    out_md.write_text(text, encoding="utf-8")
    return {"status": "ok", "chars": chars, "method": method, "path": str(out_md)}


def run(source: str, force: bool = False, max_n: Optional[int] = None) -> None:
    root = repo_root()
    raw_base = root / "data" / "raw" / source / "pdf"
    derived_base = root / "data" / "derived" / source / "extracted"

    if not raw_base.exists():
        print(f"No PDFs at {raw_base}")
        return

    done = 0
    for year_dir in sorted(raw_base.iterdir()):
        if not year_dir.is_dir():
            continue
        for pdf_path in sorted(year_dir.glob("*.pdf")):
            bill_id = pdf_path.stem
            year = year_dir.name
            result = extract_bill(pdf_path, derived_base / year / bill_id, force=force)
            status = result["status"]
            if status == "ok":
                print(f"OK       {year}/{bill_id}  {result['chars']} chars  [{result['method']}]")
                done += 1
            elif status == "skip":
                print(f"SKIP     {year}/{bill_id}")
            elif status == "suspect":
                print(f"SUSPECT  {year}/{bill_id}  {result['chars']} chars")
            else:
                print(f"ERROR    {year}/{bill_id}  {result.get('error', '')}")
            if max_n and done >= max_n:
                return


def main() -> None:
    p = argparse.ArgumentParser(description="Extract text from downloaded bill PDFs.")
    p.add_argument("--source", default="parliament_my")
    p.add_argument("--force", action="store_true", help="Re-extract even if output exists")
    p.add_argument("--max", type=int, dest="max_n", help="Stop after N extractions")
    args = p.parse_args()
    run(source=args.source, force=args.force, max_n=args.max_n)


if __name__ == "__main__":
    main()
