"""
Parliament MY CLI: arkib bill rows / PDF URLs / local HTML parse.

Run: ``PYTHONPATH=src python -m lib.sources.my.parliament_my.crawl`` (see ``--help``).

Index-only fetch + SQLite audit lives outside this module; use ``--list-arkib-bills`` or
``--list-pdfs`` for the Dewan Rakyat PDF path pipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

from lib.parser.seed_txt import parse_seed_urls_file

from lib.sources.my.parliament_my import config, parse
from lib.sources.my.parliament_my.dhtmlx_arkib import (
    dedupe_bill_records,
    drop_bm_billindex_urls,
    list_bill_records_arkib_dhtmlx_sweep,
    list_pdfs_arkib_dhtmlx_sweep,
    resolve_arkib_bill_pdf_urls,
    write_arkib_bills_csv_by_year,
)
from lib.sources.my.parliament_my.pdf_discovery import (
    list_pdfs_from_seed_file,
    list_pdfs_from_urls,
    list_pdfs_literal_pages,
)


def _is_dr_arkib_url(url: str) -> bool:
    u = url.lower()
    return "arkib" in u and "bills-dewan-rakyat" in u


def _dedupe_pdf_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[str] = set()
    out: list[dict[str, object]] = []
    for r in records:
        pu = str(r.get("pdf_url") or "")
        if not pu or pu in seen:
            continue
        seen.add(pu)
        out.append(r)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parliament MY: --list-arkib-bills, --list-pdfs, or --parse-html (PDF path pipeline only).",
    )
    parser.add_argument(
        "--parse-html",
        type=Path,
        metavar="FILE",
        help="Parse a saved HTML file (skip network). Set --source-url for correct link resolution.",
    )
    parser.add_argument(
        "--source-url",
        type=str,
        default=config.BILL_INDEX_URLS[0],
        help="Index URL the HTML was saved from (for relative links).",
    )
    parser.add_argument("--insecure", action="store_true", help="Disable TLS verify (dev only).")
    parser.add_argument("-v", "--verbose", action="store_true", help="Trace to stderr.")
    parser.add_argument(
        "--list-pdfs",
        action="store_true",
        help="Print PDF URLs found in each page HTML only: one GET per URL (default). No link following.",
    )
    parser.add_argument(
        "--list-arkib-bills",
        action="store_true",
        help="DR arkib only: structured bill rows from dhtmlx XML (JSON stdout). Optional --arkib-csv-dir.",
    )
    parser.add_argument(
        "--arkib-csv-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="With --list-arkib-bills: write bills_{year}.csv per year (UTF-8 BOM).",
    )
    parser.add_argument(
        "--arkib-resolve-pdfs",
        action="store_true",
        help="With --list-arkib-bills: GET each pdf_url (BI / legacy E / compact alternates; never BM) until %PDF; sets pdf_resolve_status.",
    )
    parser.add_argument(
        "--arkib-resolve-workers",
        type=int,
        default=None,
        metavar="N",
        help="With --arkib-resolve-pdfs: parallel probe threads (default min(16,max(4,cpu*2))). Use 1 for sequential.",
    )
    parser.add_argument(
        "--max-listing-pages",
        type=int,
        default=40,
        help="With --list-pdfs: max same-path listing pages per seed (pagination).",
    )
    parser.add_argument(
        "--url",
        action="append",
        dest="list_urls",
        metavar="URL",
        help="With --list-pdfs: seed URL (repeatable). If omitted, uses seed_urls.txt.",
    )
    parser.add_argument(
        "--follow-mode",
        choices=("dr_bills", "broad"),
        default="dr_bills",
        help="With --list-pdfs --deep-listing only: which HTML links may be followed.",
    )
    parser.add_argument(
        "--deep-listing",
        action="store_true",
        help="With --list-pdfs: also paginate same-path links and follow HTML (legacy discovery). Default is literal.",
    )
    parser.add_argument(
        "--xpath",
        action="append",
        metavar="EXPR",
        help="With --list-pdfs: optional lxml XPath (repeatable); union with full-page extract per URL.",
    )
    parser.add_argument(
        "--no-redirect",
        action="store_true",
        help="HTTP: do not follow 3xx redirects (with --list-pdfs).",
    )
    parser.add_argument(
        "--no-dhtmlx-arkib-sweep",
        action="store_true",
        help="With --list-pdfs: force literal GET for DR archive URLs (skip ajx=1 XML sweep).",
    )
    parser.add_argument(
        "--arkib-dhtmlx-max-nodes",
        type=int,
        default=2000,
        metavar="N",
        help="Cap BFS node fetches for DR archive dhtmlx sweep (default 2000).",
    )
    args = parser.parse_args()

    if args.insecure:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    if args.list_pdfs and args.list_arkib_bills:
        parser.error("use either --list-pdfs or --list-arkib-bills, not both")
    if args.arkib_csv_dir and not args.list_arkib_bills:
        parser.error("--arkib-csv-dir requires --list-arkib-bills")
    if args.arkib_resolve_pdfs and not args.list_arkib_bills:
        parser.error("--arkib-resolve-pdfs requires --list-arkib-bills")

    if args.list_arkib_bills:
        if args.deep_listing:
            parser.error("--list-arkib-bills does not support --deep-listing")
        verify = not args.insecure
        seed_path = Path(__file__).resolve().parent / "seed_urls.txt"
        urls = (
            args.list_urls
            if args.list_urls
            else [u for u, _ in parse_seed_urls_file(seed_path)]
        )
        if not urls:
            parser.error("--list-arkib-bills: no URLs (pass --url or use seed_urls.txt)")
        bill_rows: list[dict[str, str]] = []
        probe_cookie_jar: dict[str, str] = {}
        for u in urls:
            if _is_dr_arkib_url(u) and not args.no_dhtmlx_arkib_sweep:
                chunk, cj = list_bill_records_arkib_dhtmlx_sweep(
                    u,
                    verify_tls=verify,
                    max_nodes=max(1, args.arkib_dhtmlx_max_nodes),
                    verbose=args.verbose,
                    log=sys.stderr,
                )
                bill_rows.extend(chunk)
                probe_cookie_jar.update(cj)
            elif args.verbose:
                print(
                    f"[list-arkib-bills] skip (not DR arkib or --no-dhtmlx-arkib-sweep): {u[:96]}",
                    file=sys.stderr,
                )
        bill_rows = dedupe_bill_records(bill_rows)
        if args.arkib_resolve_pdfs:
            resolve_arkib_bill_pdf_urls(
                bill_rows,
                verify_tls=verify,
                verbose=args.verbose,
                log=sys.stderr,
                max_workers=args.arkib_resolve_workers,
                probe_cookies=probe_cookie_jar if probe_cookie_jar else None,
            )
        drop_bm_billindex_urls(bill_rows)
        if args.arkib_csv_dir:
            paths = write_arkib_bills_csv_by_year(bill_rows, args.arkib_csv_dir)
            if args.verbose:
                for p in paths:
                    print(f"[list-arkib-bills] wrote {p}", file=sys.stderr)
        print(json.dumps(bill_rows, ensure_ascii=False, indent=2))
        return

    if args.list_pdfs:
        verify = not args.insecure
        if args.deep_listing:
            if args.xpath and args.verbose:
                print(
                    "[list-pdfs] --xpath is ignored when --deep-listing is set",
                    file=sys.stderr,
                )
            if args.list_urls:
                records = list_pdfs_from_urls(
                    args.list_urls,
                    verify_tls=verify,
                    follow_html_per_index=12,
                    follow_mode=args.follow_mode,
                    max_listing_pages=args.max_listing_pages,
                    verbose=args.verbose,
                    log=sys.stderr,
                )
            else:
                records = list_pdfs_from_seed_file(
                    verify_tls=verify,
                    follow_html_per_index=12,
                    follow_mode=args.follow_mode,
                    max_listing_pages=args.max_listing_pages,
                    verbose=args.verbose,
                    log=sys.stderr,
                )
        else:
            seed_path = Path(__file__).resolve().parent / "seed_urls.txt"
            urls = (
                args.list_urls
                if args.list_urls
                else [u for u, _ in parse_seed_urls_file(seed_path)]
            )
            if not urls:
                parser.error("--list-pdfs: no URLs (pass --url or add lines to seed_urls.txt)")
            if args.xpath and args.verbose and any(
                _is_dr_arkib_url(u) and not args.no_dhtmlx_arkib_sweep for u in urls
            ):
                print(
                    "[list-pdfs] --xpath is ignored for URLs that use dhtmlx arkib sweep",
                    file=sys.stderr,
                )
            records = []
            for u in urls:
                if _is_dr_arkib_url(u) and not args.no_dhtmlx_arkib_sweep:
                    rec_chunk, _cookies = list_pdfs_arkib_dhtmlx_sweep(
                        u,
                        verify_tls=verify,
                        max_nodes=max(1, args.arkib_dhtmlx_max_nodes),
                        verbose=args.verbose,
                        log=sys.stderr,
                    )
                    records.extend(rec_chunk)
                else:
                    records.extend(
                        list_pdfs_literal_pages(
                            [u],
                            args.xpath or [],
                            verify_tls=verify,
                            allow_redirects=not args.no_redirect,
                            verbose=args.verbose,
                            log=sys.stderr,
                        ),
                    )
            records = _dedupe_pdf_records(records)
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return

    if args.parse_html:
        text = args.parse_html.read_text(encoding="utf-8", errors="replace")
        summary = parse.parse_fetched_index(text, source_url=args.source_url)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    parser.error(
        "choose a mode: --list-arkib-bills, --list-pdfs, or --parse-html FILE "
        "(index fetch + DB was removed from this entrypoint)",
    )


if __name__ == "__main__":
    main()
