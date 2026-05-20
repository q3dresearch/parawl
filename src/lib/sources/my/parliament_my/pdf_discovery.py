"""Discover PDF URLs from parliament index parses (optional HTML follow)."""

from __future__ import annotations

import time
from collections import deque
from pathlib import Path
from typing import Any, TextIO

from lib.parser.seed_txt import parse_seed_urls_file

from lib.sources.my.parliament_my import fetch, parse

# Each entry: ``(logical_seed, listing_page_url, summary_dict)``.
IndexSummaryRow = tuple[str, str, dict[str, Any]]


def collect_pdf_targets(
    index_summaries: list[IndexSummaryRow],
    *,
    follow_html_per_index: int,
    follow_mode: str = "broad",
    verify_tls: bool,
    verbose: bool,
    log: TextIO | None,
) -> list[tuple[str, dict[str, str]]]:
    discovered: dict[str, dict[str, str]] = {}

    def add_pdf(pdf_url: str, logical_seed: str, via_page: str) -> None:
        if pdf_url not in discovered:
            discovered[pdf_url] = {"from_index": logical_seed, "via_page": via_page}

    follow_ok = (
        parse.is_dr_bills_follow_candidate
        if follow_mode == "dr_bills"
        else parse.is_html_follow_candidate
    )

    for logical_seed, page_url, summary in index_summaries:
        for link in summary.get("links", []):
            u = str(link.get("url") or "")
            if parse.is_pdf_href(u):
                add_pdf(u, logical_seed, page_url)

        for u in summary.get("pdf_urls_on_page") or []:
            add_pdf(str(u), logical_seed, page_url)

        if follow_html_per_index <= 0:
            continue

        pool: list[str] = []
        for link in summary.get("links", []):
            u = str(link.get("url") or "")
            if follow_ok(u):
                pool.append(u)
        pool = sorted(set(pool), key=parse.dr_bills_follow_sort_key)
        followed_keys: set[str] = set()
        for html_url in pool[: max(0, follow_html_per_index)]:
            fk = parse.normalize_listing_url_for_dedupe(html_url)
            if fk in followed_keys:
                continue
            followed_keys.add(fk)
            if verbose and log:
                short = html_url if len(html_url) <= 88 else html_url[:85] + "..."
                print(f"[trace] pdf-discovery follow html: {short}", file=log)
            fr = fetch.fetch_url(html_url, verify=verify_tls)
            if fr.status != "ok" or not fr.raw_bytes:
                continue
            html = fr.raw_bytes.decode("utf-8", errors="replace")
            for pdf_url in parse.extract_pdf_urls_from_html(html, html_url):
                add_pdf(pdf_url, logical_seed, html_url)

    return sorted(discovered.items(), key=lambda x: x[0])


def _bill_row_context_by_pdf_url(summaries: list[IndexSummaryRow]) -> dict[str, dict[str, object]]:
    mp: dict[str, dict[str, object]] = {}
    for _seed, _page, summary in summaries:
        for row in summary.get("bill_table_rows") or []:
            if not isinstance(row, dict):
                continue
            ctx = {k: v for k, v in row.items() if k != "pdf_urls"}
            for pu in row.get("pdf_urls") or []:
                ps = str(pu)
                if ps not in mp:
                    mp[ps] = ctx
    return mp


def _index_summaries_for_urls(
    urls: list[str],
    *,
    verify_tls: bool,
    verbose: bool,
    log: TextIO | None,
    max_listing_pages: int,
) -> list[IndexSummaryRow]:
    rows: list[IndexSummaryRow] = []
    cap = max(1, max_listing_pages)

    for seed_url in urls:
        queue: deque[str] = deque([seed_url])
        seen_norm: set[str] = set()

        while queue and len(seen_norm) < cap:
            u = queue.popleft()
            norm_key = parse.normalize_listing_url_for_dedupe(u)
            if norm_key in seen_norm:
                continue
            seen_norm.add(norm_key)

            fr = fetch.fetch_url(u, verify=verify_tls)
            if not fr.raw_bytes or fr.http_status != 200 or fr.status != "ok":
                if verbose and log:
                    print(
                        f"[list-pdfs] skip listing page {u!r}: status={fr.status} "
                        f"http={fr.http_status} err={fr.error}",
                        file=log,
                    )
                continue
            text = fr.raw_bytes.decode("utf-8", errors="replace")
            summary = parse.parse_fetched_index(text, source_url=u)
            rows.append((seed_url, u, summary))

            if len(seen_norm) >= cap:
                break
            for nxt in parse.extract_listing_pagination_urls(text, u):
                nk = parse.normalize_listing_url_for_dedupe(nxt)
                if nk not in seen_norm:
                    queue.append(nxt)

    return rows


def list_pdfs_from_urls(
    urls: list[str],
    *,
    verify_tls: bool = True,
    follow_html_per_index: int = 200,
    follow_mode: str = "dr_bills",
    max_listing_pages: int = 40,
    verbose: bool = False,
    log: TextIO | None = None,
) -> list[dict[str, object]]:
    """
    HTML-only discovery: fetch each seed URL, walk same-path pagination links,
    optionally follow same-site HTML links, collect PDF URLs (anchors + billindex paths).
    Does not download ``.pdf`` bodies.
    """
    t0 = time.perf_counter()
    index_summaries = _index_summaries_for_urls(
        urls,
        verify_tls=verify_tls,
        verbose=verbose,
        log=log,
        max_listing_pages=max_listing_pages,
    )
    bill_ctx = _bill_row_context_by_pdf_url(index_summaries)
    records: list[dict[str, object]] = []
    for pdf_url, meta in collect_pdf_targets(
        index_summaries,
        follow_html_per_index=follow_html_per_index,
        follow_mode=follow_mode,
        verify_tls=verify_tls,
        verbose=verbose,
        log=log,
    ):
        rec: dict[str, object] = {
            "seed_url": meta["from_index"],
            "pdf_url": pdf_url,
            "via_page": meta["via_page"],
        }
        row = bill_ctx.get(pdf_url)
        if row:
            rec["bill"] = row
        records.append(rec)

    elapsed = time.perf_counter() - t0
    if log is not None:
        print(
            f"[list-pdfs] {len(records)} PDF(s) in {elapsed:.1f}s "
            f"({len(index_summaries)} listing page fetch(es), "
            f"max_listing_pages={max_listing_pages})",
            file=log,
        )
    return records


def list_pdfs_literal_pages(
    urls: list[str],
    xpaths: list[str],
    *,
    verify_tls: bool = True,
    allow_redirects: bool = True,
    verbose: bool = False,
    log: TextIO | None = None,
) -> list[dict[str, object]]:
    """
    One GET per ``urls`` entry only: no pagination, no link following.

    If ``xpaths`` is non-empty, evaluate each XPath on the response and union PDFs
    found under matching nodes; otherwise parse the full document.
    """
    t0 = time.perf_counter()
    records: list[dict[str, object]] = []
    for page_url in urls:
        fr = fetch.fetch_url(
            page_url,
            verify=verify_tls,
            allow_redirects=allow_redirects,
        )
        base = str((fr.meta or {}).get("final_url") or page_url)
        if verbose and log:
            print(f"[literal] GET {page_url} -> {fr.http_status} final_url={base}", file=log)
        if not fr.raw_bytes or fr.status != "ok" or fr.http_status != 200:
            if log:
                print(
                    f"[literal] skip {page_url!r}: status={fr.status} err={fr.error}",
                    file=log,
                )
            continue
        text = fr.raw_bytes.decode("utf-8", errors="replace")
        pdfs: list[str] = []
        if xpaths:
            for xp in xpaths:
                pdfs.extend(parse.extract_pdf_urls_with_xpath(text, base, xp))
        else:
            pdfs = parse.extract_pdf_urls_from_html(text, base)
        seen_u: set[str] = set()
        for u in pdfs:
            if u in seen_u:
                continue
            seen_u.add(u)
            records.append(
                {
                    "seed_url": page_url,
                    "pdf_url": u,
                    "via_page": base,
                    "literal": True,
                    "xpaths": list(xpaths) if xpaths else None,
                },
            )
    elapsed = time.perf_counter() - t0
    if log is not None:
        print(
            f"[literal] {len(records)} PDF row(s) in {elapsed:.1f}s "
            f"({len(urls)} URL(s), xpaths={len(xpaths)})",
            file=log,
        )
    return records


def list_pdfs_from_seed_file(
    seed_file: Path | None = None,
    *,
    verify_tls: bool = True,
    follow_html_per_index: int = 200,
    follow_mode: str = "dr_bills",
    max_listing_pages: int = 40,
    verbose: bool = False,
    log: TextIO | None = None,
) -> list[dict[str, object]]:
    """Same as :func:`list_pdfs_from_urls` but URLs come from ``seed_urls.txt`` next to this adapter."""
    path = seed_file or (Path(__file__).resolve().parent / "seed_urls.txt")
    urls = [u for u, _ in parse_seed_urls_file(path)]
    return list_pdfs_from_urls(
        urls,
        verify_tls=verify_tls,
        follow_html_per_index=follow_html_per_index,
        follow_mode=follow_mode,
        max_listing_pages=max_listing_pages,
        verbose=verbose,
        log=log,
    )
