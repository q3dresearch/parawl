"""Dewan Rakyat archive: walk dhtmlxTree via ``?ajx=1&uid=…&id=…`` XML (no browser).

``uid`` is regenerated every request (cache-busting). ``id`` is the tree node: start at ``0``,
then BFS-expand every ``<item child="1">`` (e.g. ``0_2024``, ``0_1993``) — no manual id list.

All XHRs and Referers use ``lang=en`` on the arkib page URL (``lang=bm`` changes the tree /
``loadResult`` language); seeds may omit ``lang`` — we set English explicitly.

The site can bind PDF access to the same language **session** as the listing (EN tab vs BM tab).
We GET the ``lang=en`` landing page once, reuse that **cookie jar** for all dhtmlx XHRs, and pass
the same cookies into ``--arkib-resolve-pdfs`` probes so behaviour stays consistent (we only use BI/E
billindex URLs, not BM).
"""

from __future__ import annotations

import csv
import os
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Mapping, TextIO
from urllib.parse import parse_qsl, unquote, urlencode, urlparse

import requests
import xml.etree.ElementTree as ET

from lib.sources.my.parliament_my import config, fetch, parse

# Manually verified on parlimen (GET → ``%PDF``). **Do not orphan** — ``synthetic_billindex_pdf_rel_paths``
# and import-time ``_lock_synthesis_to_working_billindex_urls`` must stay aligned with these paths.
BILLINDEX_WORKING_LEGACY_E_PDF = (
    "https://www.parlimen.gov.my/files/billindex/pdf/1990/DR011990E.pdf"
)
BILLINDEX_WORKING_SPACED_BI_PDF = (
    "https://www.parlimen.gov.my/files/billindex/pdf/2024/DR%2017%20BI.pdf"
)

# ``probe_pdf_magic`` only (Range/stream GET). Below ``FETCH_TIMEOUT_S`` so bulk resolve does not
# multiply 45s × many candidates × rows.
ARKIB_PDF_PROBE_TIMEOUT_S = 20


def synthetic_billindex_pdf_rel_paths(bill_no: int, year: int) -> list[str]:
    """
    Relative paths under ``/files/billindex/pdf/`` — same shapes as ``BILLINDEX_WORKING_*`` above.

    **No BM paths** — only legacy **E**, spaced **BI** variants, and compact no-E.
    """
    y = str(year)
    nn = f"{int(bill_no):02d}"
    n_plain = str(int(bill_no))
    return [
        f"/files/billindex/pdf/{y}/DR{nn}{y}E.pdf",
        f"/files/billindex/pdf/{y}/DR {n_plain} BI.pdf",
        f"/files/billindex/pdf/{y}/DR {nn} BI.pdf",
        f"/files/billindex/pdf/{y}/DR{nn}{y}.pdf",
    ]


def _lock_synthesis_to_working_billindex_urls() -> None:
    """Fail fast if synthesis drifts from the known-good parliament URLs (update constants or code together)."""
    leg = unquote(urlparse(BILLINDEX_WORKING_LEGACY_E_PDF).path)
    syn1990 = synthetic_billindex_pdf_rel_paths(1, 1990)
    assert syn1990[0] == leg, (syn1990[0], leg)

    bi = unquote(urlparse(BILLINDEX_WORKING_SPACED_BI_PDF).path)
    syn2024 = synthetic_billindex_pdf_rel_paths(17, 2024)
    assert bi in syn2024, (bi, syn2024)


_lock_synthesis_to_working_billindex_urls()


def _arkib_session_lang_en_warm(
    page_en: str,
    *,
    verify_tls: bool,
    verbose: bool,
    log: TextIO | None,
) -> requests.Session:
    """
    Browser-like cookie jar: GET the human arkib page with ``lang=en`` once, then reuse the same
    session for dhtmlx XHRs.

    The live site can tie PDF access to the same language context as the tab (EN vs BM); stateless
    GETs risk cross-language denials. This adapter uses EN only and BI billindex PDFs.
    """
    sess = requests.Session()
    sess.headers.update(config.DEFAULT_HEADERS)
    try:
        r = sess.get(page_en, verify=verify_tls, timeout=config.FETCH_TIMEOUT_S)
    except requests.RequestException as e:
        if verbose and log:
            print(f"[dhtmlx] EN landing GET failed (continuing with empty cookie jar): {e}", file=log)
        return sess
    if verbose and log and r.status_code != 200:
        print(
            f"[dhtmlx] EN landing GET http={r.status_code} (continuing)",
            file=log,
        )
    return sess


def _resolution_candidate_urls(row: dict[str, str], embedded_url: str) -> list[str]:
    """
    URLs to probe for a working PDF.

    **Order:** dhtmlx XML ``loadResult`` path first (BM→BI / ``E`` swap on that same path), then
    ``dr_label`` synthetics only as fallback when the embed is missing or those fail — avoids
    ~4 useless GETs per row when the tree already gave ``/files/billindex/pdf/…``.
    """
    seen: set[str] = set()
    out: list[str] = []

    def add(u: str) -> None:
        u = (u or "").strip()
        if u and u not in seen:
            seen.add(u)
            out.append(u)

    if (embedded_url or "").strip():
        for u in parse.alternates_parliament_bill_pdf_url(embedded_url):
            add(u)

    parsed = parse.parse_dr_label_bill_year(row.get("dr_label") or "")
    if parsed:
        bill_n, year_n = parsed
        for rel in synthetic_billindex_pdf_rel_paths(bill_n, year_n):
            u = parse.absolute_billindex_pdf_url(rel)
            if u:
                add(u)

    return out


def arkib_page_url_with_lang_en(page_url: str) -> str:
    """
    Dewan arkib listing URL with ``lang=en``.

    dhtmlx ``ajx=1`` responses follow the page's language: ``lang=bm`` yields Malay tree and
    ``loadResult`` targets; ``lang=en`` requests the English/BI-aligned bill inventory. Seeds
    without ``lang`` should default to English for this adapter.
    """
    frag = (page_url or "").strip().split("#")[0]
    p = urlparse(frag)
    pairs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=False) if k.lower() != "lang"]
    pairs.append(("lang", "en"))
    pairs.sort(key=lambda kv: (kv[0].lower(), kv[1]))
    q = urlencode(pairs, doseq=True)
    scheme = (p.scheme or "https").lower()
    netloc = p.netloc or ""
    path = p.path or "/"
    return f"{scheme}://{netloc}{path}" + (f"?{q}" if q else "")


def drop_bm_billindex_urls(rows: list[dict[str, str]]) -> None:
    """Clear ``pdf_url`` / ``pdf_filename`` when they point at a **BM** billindex file (BI-only export)."""
    for row in rows:
        if parse.billindex_pdf_url_is_bm(row.get("pdf_url") or ""):
            row["pdf_url"] = ""
            row["pdf_filename"] = ""


def _ajax_url(arkib_page_url: str, node_id: str) -> str:
    base = arkib_page_url_with_lang_en(arkib_page_url)
    uid = int(time.time() * 1000)
    joiner = "&" if "?" in base else "?"
    return f"{base}{joiner}ajx=1&uid={uid}&id={node_id}"


def _expandable_child_ids(xml_text: str) -> list[str]:
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in root.iter("item"):
        if item.get("child") != "1":
            continue
        iid = item.get("id")
        if not iid or iid in seen:
            continue
        seen.add(iid)
        out.append(iid)
    return out


def list_pdfs_arkib_dhtmlx_sweep(
    arkib_page_url: str,
    *,
    verify_tls: bool = True,
    max_nodes: int = 2000,
    verbose: bool = False,
    log: TextIO | None = None,
) -> tuple[list[dict[str, object]], dict[str, str]]:
    """
    BFS tree nodes from ``id=0``; each GET returns XML with optional ``loadResult`` PDF paths.

    ``arkib_page_url`` should be the bills archive page, e.g.
    ``https://www.parlimen.gov.my/bills-dewan-rakyat.html?uweb=dr&arkib=yes``.

    Returns ``(records, cookies)`` from an ``lang=en`` landing + shared session so callers can
    reuse the same jar for PDF GETs (parlimen may reject cross-language fetches).
    """
    records: list[dict[str, object]] = []
    pdf_seen: set[str] = set()
    queue: deque[str] = deque(["0"])
    fetched: set[str] = set()
    page_en = arkib_page_url_with_lang_en(arkib_page_url)
    sess = _arkib_session_lang_en_warm(page_en, verify_tls=verify_tls, verbose=verbose, log=log)

    while queue and len(fetched) < max_nodes:
        nid = queue.popleft()
        if nid in fetched:
            continue
        fetched.add(nid)

        url = _ajax_url(page_en, nid)
        fr = fetch.fetch_url(
            url,
            verify=verify_tls,
            headers={"Referer": page_en},
            session=sess,
        )
        if not fr.raw_bytes or fr.status != "ok" or fr.http_status != 200:
            if verbose and log:
                print(f"[dhtmlx] node {nid!r}: {fr.status} {fr.error}", file=log)
            continue
        xml_text = fr.raw_bytes.decode("utf-8", errors="replace")
        pdfs_here = parse.extract_pdf_urls_from_dhtmlx_tree_xml(xml_text)
        for pu in pdfs_here:
            if pu in pdf_seen:
                continue
            pdf_seen.add(pu)
            records.append(
                {
                    "seed_url": page_en,
                    "pdf_url": pu,
                    "via_page": url,
                    "source": "dhtmlx_ajx",
                    "tree_node_id": nid,
                },
            )

        if verbose and log:
            print(
                f"[dhtmlx] node {nid!r}: +{len(pdfs_here)} pdf ref(s) in XML, queue ~{len(queue)}",
                file=log,
            )

        for cid in _expandable_child_ids(xml_text):
            if cid not in fetched:
                queue.append(cid)

    if log:
        print(
            f"[dhtmlx] sweep done: {len(fetched)} node(s) fetched, {len(records)} unique PDF URL(s)",
            file=log,
        )
        if queue and len(fetched) >= max_nodes:
            print(
                f"[dhtmlx] warning: stopped at --arkib-dhtmlx-max-nodes ({max_nodes}); "
                f"~{len(queue)} node id(s) still queued (raise the cap for a full archive pass).",
                file=log,
            )
    return records, sess.cookies.get_dict()


def _bill_identity_key(row: dict[str, str]) -> tuple:
    """Same bill can appear under root ``id=0`` and under ``id=0_1990`` with different PDF paths."""
    y = (row.get("year") or "").strip()
    dr = (row.get("dr_label") or "").strip()
    if y and dr:
        return ("bill", y, dr.lower())
    pdf = (row.get("pdf_url") or "").strip()
    if pdf:
        return ("pdf", pdf)
    return (
        "meta",
        y,
        (row.get("bill_item_id") or "").strip(),
        (row.get("summary") or "")[:240],
    )


def _prefer_bill_row(a: dict[str, str], b: dict[str, str]) -> dict[str, str]:
    ra, rb = parse.bill_record_merge_rank(a), parse.bill_record_merge_rank(b)
    if ra < rb:
        return a
    if rb < ra:
        return b
    return a


def dedupe_bill_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    One row per bill (``year`` + ``dr_label``) when both are set.

    Root / shallow nodes often embed **BM** or compact ``DR021990.pdf``; year buckets (``id=0_1990``)
    and **BI** / ``…E.pdf`` variants are preferred when both exist (see ``parse.bill_record_merge_rank``).
    """
    best: dict[tuple, dict[str, str]] = {}
    for row in records:
        key = _bill_identity_key(row)
        if key not in best:
            best[key] = row
        else:
            best[key] = _prefer_bill_row(best[key], row)
    return list(best.values())


def list_bill_records_arkib_dhtmlx_sweep(
    arkib_page_url: str,
    *,
    verify_tls: bool = True,
    max_nodes: int = 2000,
    verbose: bool = False,
    log: TextIO | None = None,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    """
    Same BFS as :func:`list_pdfs_arkib_dhtmlx_sweep`, but each bill group under ``<tree>``
    becomes one dict (title, readings, PDF URL, etc.). After the sweep, rows are merged with
    :func:`dedupe_bill_records` so year-node payloads win over root ``id=0`` for the same DR key.

    Returns ``(rows, cookies)`` for passing to :func:`resolve_arkib_bill_pdf_urls` so PDF probes
    share the same ``lang=en`` cookie context as the tree.
    """
    merged: list[dict[str, str]] = []
    queue: deque[str] = deque(["0"])
    fetched: set[str] = set()
    page_en = arkib_page_url_with_lang_en(arkib_page_url)
    sess = _arkib_session_lang_en_warm(page_en, verify_tls=verify_tls, verbose=verbose, log=log)

    while queue and len(fetched) < max_nodes:
        nid = queue.popleft()
        if nid in fetched:
            continue
        fetched.add(nid)

        url = _ajax_url(page_en, nid)
        fr = fetch.fetch_url(
            url,
            verify=verify_tls,
            headers={"Referer": page_en},
            session=sess,
        )
        if not fr.raw_bytes or fr.status != "ok" or fr.http_status != 200:
            if verbose and log:
                print(f"[dhtmlx-bills] node {nid!r}: {fr.status} {fr.error}", file=log)
            continue
        xml_text = fr.raw_bytes.decode("utf-8", errors="replace")
        rows = parse.parse_dhtmlx_bill_records_from_xml(
            xml_text,
            source_tree_node_id=nid,
            ajax_url=url,
            seed_url=page_en,
        )
        merged.extend(rows)

        if verbose and log:
            print(
                f"[dhtmlx-bills] node {nid!r}: +{len(rows)} bill row(s), queue ~{len(queue)}",
                file=log,
            )

        for cid in _expandable_child_ids(xml_text):
            if cid not in fetched:
                queue.append(cid)

    out = dedupe_bill_records(merged)
    if log:
        print(
            f"[dhtmlx-bills] sweep done: {len(fetched)} node(s), "
            f"{len(out)} bill row(s) after merge (raw {len(merged)})",
            file=log,
        )
        if queue and len(fetched) >= max_nodes:
            print(
                f"[dhtmlx-bills] warning: stopped at max_nodes ({max_nodes}); "
                f"~{len(queue)} id(s) still queued.",
                file=log,
            )
    return out, sess.cookies.get_dict()


def _default_arkib_resolve_workers() -> int:
    return min(16, max(4, (os.cpu_count() or 4) * 2))


def _resolve_arkib_row_pdf_patch(
    row: dict[str, str],
    *,
    verify_tls: bool,
    t_probe: int,
    probe_cookies: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Fields to merge into ``row`` after probing billindex candidates (see :func:`resolve_arkib_bill_pdf_urls`)."""
    from urllib.parse import unquote, urlparse

    orig = (row.get("pdf_url") or "").strip()
    if not orig:
        return {"pdf_resolve_status": "skipped", "pdf_url_embedded": ""}

    patch: dict[str, str] = {"pdf_url_embedded": orig}
    referer = (row.get("seed_url") or "").strip()
    hdrs = {"Referer": referer} if referer else None
    chosen = ""
    ck = dict(probe_cookies) if probe_cookies else None
    for cand in _resolution_candidate_urls(row, orig):
        if parse.billindex_pdf_url_is_bm(cand):
            continue
        if fetch.probe_pdf_magic(
            cand,
            verify=verify_tls,
            headers=hdrs,
            timeout_s=t_probe,
            cookies=ck,
        ):
            chosen = cand
            break

    if chosen:
        if parse.billindex_pdf_url_is_bm(chosen):
            patch.update(
                {
                    "pdf_resolve_status": "failed_bm_rejected",
                    "pdf_url": "",
                    "pdf_filename": "",
                },
            )
        else:
            patch.update(
                {
                    "pdf_url": chosen,
                    "pdf_filename": unquote(urlparse(chosen).path.rsplit("/", 1)[-1]),
                    "pdf_resolve_status": (
                        "ok_embedded" if (orig and chosen == orig) else "ok"
                    ),
                },
            )
        return patch

    patch["pdf_resolve_status"] = "failed"
    if parse.billindex_pdf_url_is_bm(orig):
        patch["pdf_url"] = ""
        patch["pdf_filename"] = ""
    return patch


def resolve_arkib_bill_pdf_urls(
    rows: list[dict[str, str]],
    *,
    verify_tls: bool = True,
    verbose: bool = False,
    log: TextIO | None = None,
    probe_timeout_s: int | None = None,
    max_workers: int | None = None,
    probe_cookies: Mapping[str, str] | None = None,
) -> None:
    """
    Mutates rows: probes pattern URLs and alternates (**BI** / legacy **E** / compact — never **BM**).

    Sets ``pdf_url_embedded`` to the pre-probe URL, updates ``pdf_url`` / ``pdf_filename`` when a
    candidate returns PDF magic bytes, and sets ``pdf_resolve_status`` to ``ok`` / ``failed`` / ``skipped``.

    Uses a thread pool (default ~``cpu*2``, capped at 16) so bulk CSV export probes many rows at once.

    ``probe_cookies``: jar from :func:`list_bill_records_arkib_dhtmlx_sweep` (``lang=en`` landing + tree)
    so PDF GETs match the same language/session as in the browser.
    """
    t_probe = ARKIB_PDF_PROBE_TIMEOUT_S if probe_timeout_s is None else probe_timeout_s
    workers = _default_arkib_resolve_workers() if max_workers is None else max(1, max_workers)
    p_cookies = dict(probe_cookies) if probe_cookies else None

    if workers == 1 or len(rows) <= 1:
        for row in rows:
            patch = _resolve_arkib_row_pdf_patch(
                row,
                verify_tls=verify_tls,
                t_probe=t_probe,
                probe_cookies=p_cookies,
            )
            if (
                verbose
                and log
                and patch.get("pdf_resolve_status") == "failed"
                and (row.get("pdf_url") or "").strip()
            ):
                o = (row.get("pdf_url") or "").strip()
                print(f"[resolve-pdf] no working candidate for {o[:120]}", file=log)
            row.update(patch)
        return

    def _work(r: dict[str, str]) -> tuple[dict[str, str], str]:
        p = _resolve_arkib_row_pdf_patch(
            r,
            verify_tls=verify_tls,
            t_probe=t_probe,
            probe_cookies=p_cookies,
        )
        orig_u = (r.get("pdf_url") or "").strip()
        return p, orig_u

    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(_work, rows))

    for row, (patch, orig_u) in zip(rows, results):
        if (
            verbose
            and log
            and patch.get("pdf_resolve_status") == "failed"
            and orig_u
        ):
            print(f"[resolve-pdf] no working candidate for {orig_u[:120]}", file=log)
        row.update(patch)


def write_arkib_bills_csv_by_year(
    records: list[dict[str, str]],
    out_dir: Path,
    *,
    filename_template: str = "bills_{year}.csv",
) -> list[Path]:
    """
    Write one UTF-8 CSV per distinct ``year`` field (``bills_2024.csv``, …).
    Rows with empty year go to ``bills_unknown.csv``.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in records:
        y = (row.get("year") or "").strip() or "unknown"
        by_year[y].append(row)

    written: list[Path] = []
    fields = parse.ARKIB_BILL_CSV_FIELDS
    for year, rows in sorted(by_year.items(), key=lambda kv: kv[0]):
        path = out_dir / filename_template.format(year=year)
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        written.append(path)
    return written
