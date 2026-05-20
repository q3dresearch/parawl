"""
Parse bill listing HTML from parlimen.gov.my and extract outbound links.

Also: Dewan **billindex** URLs, dhtmlx ``loadResult`` XML → bill rows, merge ranks (arkib / CSV).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlparse

from bs4 import BeautifulSoup

from . import config


def normalize_listing_url_for_dedupe(url: str) -> str:
    """
    Same bills *listing* identity for HTTP dedupe: strip ``lang=``, empty params, sort query.

    ``lang=bm`` / ``lang=en`` / no lang often serve the same bill inventory (different copy).
    """
    frag = url.strip().split("#")[0]
    p = urlparse(frag)
    pairs = [
        (k, v)
        for k, v in parse_qsl(p.query, keep_blank_values=False)
        if k.lower() != "lang"
    ]
    pairs.sort()
    q = urlencode(pairs, doseq=True)
    netloc = (p.netloc or "").lower()
    path = p.path or ""
    scheme = (p.scheme or "https").lower()
    if q:
        return f"{scheme}://{netloc}{path}?{q}"
    return f"{scheme}://{netloc}{path}"


def same_site(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        base_host = urlparse(config.BASE_URL).netloc.lower()
        return host == base_host or host.endswith("parlimen.gov.my")
    except Exception:
        return False


def is_pdf_href(url: str) -> bool:
    try:
        return urlparse(url).path.lower().endswith(".pdf")
    except Exception:
        return False


_DR_LABEL_BILL_YEAR = re.compile(r"D\.R\.\s*(\d+)\s*/\s*(\d{4})", re.IGNORECASE)


def parse_dr_label_bill_year(dr_label: str) -> tuple[int, int] | None:
    """
    ``D.R.17/2024`` → ``(17, 2024)``; ``D.R.01/1990`` → ``(1, 1990)``.

    Used to synthesise billindex paths (legacy ``DR011990E.pdf``, spaced ``DR 17 BI.pdf``).
    """
    m = _DR_LABEL_BILL_YEAR.search((dr_label or "").strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


_DHTMLX_LOAD_RESULT = re.compile(
    r"loadResult\s*\(\s*['\"](/files/billindex/pdf/[^'\"]+)['\"]",
    re.IGNORECASE,
)


def absolute_billindex_pdf_url(site_path: str, base_url: str | None = None) -> str:
    """
    Build an absolute URL for a same-site ``/files/billindex/pdf/…`` path from XML or HTML.

    Paths in ``loadResult`` often contain spaces (e.g. ``DR 17 BI.pdf``); the origin serves
    them with percent-encoding (``DR%2017%20BI.pdf``).
    """
    base = base_url or config.BASE_URL
    raw = (site_path or "").strip()
    if not raw.startswith("/"):
        return ""
    path_enc = quote(unquote(raw), safe="/")
    u = urljoin(base.rstrip("/") + "/", path_enc.lstrip("/"))
    if not same_site(u):
        return ""
    return u


_LEGACY_DR_COMPACT = re.compile(r"(/DR\d{2}\d{4})\.pdf$", re.IGNORECASE)


def legacy_e_suffix_billindex_path(path: str) -> str | None:
    """
    ``…/DR021990.pdf`` → ``…/DR021990E.pdf`` (English scan on older Dewan PDFs).

    Returns ``None`` if the path already ends with ``E.pdf`` or does not match.
    """
    p = (path or "").strip()
    if re.search(r"DR\d{2}\d{4}E\.pdf$", p, re.IGNORECASE):
        return None
    m = _LEGACY_DR_COMPACT.search(p)
    if not m:
        return None
    return p[: m.start(1)] + m.group(1) + "E.pdf"


def xhr_ajax_node_merge_tier(source_tree_node_id: str) -> int:
    """
    Lower is better when merging duplicate bills.

    ``0_2024`` / ``0_1990`` (year bucket XHR) beats ``0_0`` / ``0_1`` beats root ``0``.
    """
    s = (source_tree_node_id or "").strip()
    if s == "0":
        return 2
    parts = s.split("_")
    if len(parts) >= 2 and parts[1].isdigit() and len(parts[1]) == 4:
        y = int(parts[1])
        if 1800 <= y <= 2100:
            return 0
    return 1


_UNICODE_SPACE = re.compile(r"[\u00a0\u1680\u2000-\u200a\u202f\u205f\u3000]+")


def _billindex_path_normalized(url_or_path: str) -> str:
    """Lowercase path with unicode spaces folded to ASCII (site uses NBSP in some filenames)."""
    raw = (url_or_path or "").strip()
    if raw.startswith(("http://", "https://")):
        path = urlparse(raw).path
    else:
        path = raw
    p = unquote(path or "").lower()
    return _UNICODE_SPACE.sub(" ", p)


def billindex_pdf_url_is_bm(url: str) -> bool:
    """True if the path is a Dewan **BM** (Malay) bill PDF filename (``… BM.pdf``)."""
    try:
        path = _billindex_path_normalized(url)
    except Exception:
        return False
    if "/files/billindex/pdf/" not in path:
        return False
    seg = path.rsplit("/", 1)[-1]
    if "dr" not in seg:
        return False
    return bool(re.search(r"(?i)bm\.pdf$", seg))


def billindex_url_for_dhtmlx_path(site_path: str, base_url: str | None = None) -> str:
    """
    Absolute billindex URL from a dhtmlx ``loadResult`` site path.

    **Never returns a BM RUU PDF URL** — we do not carry Malay billindex links forward.
    ``… BM.pdf`` is rewritten to ``… BI.pdf`` on the path string only (no request to the BM URL).
    """
    base = base_url or config.BASE_URL
    raw = (site_path or "").strip()
    if not raw.startswith("/"):
        return ""
    u = absolute_billindex_pdf_url(raw, base)
    if not u:
        return ""
    if not billindex_pdf_url_is_bm(u):
        return u
    path_spaced = _UNICODE_SPACE.sub(" ", unquote(raw))
    bi_rel = re.sub(r"(?i)bm\.pdf$", "BI.pdf", path_spaced)
    if bi_rel == path_spaced:
        return ""
    return absolute_billindex_pdf_url(bi_rel, base) or ""


def _dhtmlx_display_filename(pdf_name: str) -> str:
    """Strip Dewan BM billindex filenames from row display (prefer BI label)."""
    name = (pdf_name or "").strip()
    if not name:
        return ""
    fn = _UNICODE_SPACE.sub(" ", name)
    if re.search(r"(?i)bm\.pdf$", fn):
        return re.sub(r"(?i)bm\.pdf$", "BI.pdf", fn)
    return pdf_name


def bill_record_merge_rank(row: dict[str, str]) -> tuple[int, int, int, int]:
    """
    Lexicographic tuple; lower is better. Prefers year XHR, **BI** over **BM**,
    legacy ``…E.pdf`` over bare ``DRddyyyy.pdf``, then longer URL.
    """
    tier = xhr_ajax_node_merge_tier(row.get("source_tree_node_id") or "")
    url = (row.get("pdf_url") or "").strip()
    path = _billindex_path_normalized(url)

    is_bm = 1 if billindex_pdf_url_is_bm(url) else 0

    legacy_bad = 0
    if re.search(r"/dr\d{2}\d{4}e\.pdf$", path):
        legacy_bad = 0
    elif re.search(r"/dr\d{2}\d{4}\.pdf$", path):
        legacy_bad = 1

    plen = -len(url)
    return (tier, is_bm, legacy_bad, plen)


def alternates_parliament_bill_pdf_url(url: str) -> list[str]:
    """
    Candidate URLs to probe when the embedded link fails.

    **BM** URLs are never emitted — only **BI**, legacy **E**, compact, and BI swaps from BM embeds.
    """
    if not (url or "").strip():
        return []
    p = urlparse((url or "").strip())
    base = f"{p.scheme}://{p.netloc}" if p.netloc else config.BASE_URL
    path = unquote(p.path or "")
    if not path.startswith("/files/billindex/pdf/"):
        u = absolute_billindex_pdf_url(path, base) if path.startswith("/") else url.strip()
        if u and billindex_pdf_url_is_bm(u):
            return []
        return [u] if u else [url.strip()]

    raw_paths: list[str] = []

    def add_raw(pp: str) -> None:
        if pp and pp not in raw_paths:
            raw_paths.append(pp)

    ep = legacy_e_suffix_billindex_path(path)
    if ep:
        add_raw(ep)

    path_spaced = _UNICODE_SPACE.sub(" ", path)
    if billindex_pdf_url_is_bm((url or "").strip()):
        add_raw(re.sub(r"(?i)bm\.pdf$", "BI.pdf", path_spaced))
    else:
        add_raw(path)

    out: list[str] = []
    seen_u: set[str] = set()
    for rp in raw_paths:
        u = absolute_billindex_pdf_url(rp, base)
        if u and not billindex_pdf_url_is_bm(u) and u not in seen_u:
            seen_u.add(u)
            out.append(u)
    if out:
        return out
    # Do not fall back to the embedded BM URL (that broke when NBSP hid BM from regexes).
    return []


def extract_pdf_urls_from_dhtmlx_tree_xml(xml_text: str, base_url: str | None = None) -> list[str]:
    """Bill PDF paths embedded in dhtmlx ``ajx=1`` XML responses (BI/E/compact only — never BM billindex)."""
    base = base_url or config.BASE_URL
    seen: set[str] = set()
    out: list[str] = []
    for m in _DHTMLX_LOAD_RESULT.finditer(xml_text):
        path = m.group(1)
        u = billindex_url_for_dhtmlx_path(path, base)
        if not u:
            continue
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


_DHTMLX_LOAD_RESULT_PAIR = re.compile(
    r"loadResult\s*\(\s*['\"](/files/billindex/pdf/[^'\"]+)['\"]\s*,\s*['\"]([^'\"]*)['\"]",
    re.IGNORECASE,
)
_YEAR_IN_PATH = re.compile(r"/files/billindex/pdf/(\d{4})/", re.IGNORECASE)


def _dhtmlx_userdata_myurl(item: ET.Element) -> str:
    for el in item:
        if el.tag == "userdata" and el.get("name") == "myurl":
            return (el.text or "").strip()
    return ""


def _year_from_dhtmlx_tree_id(tree_id: str | None) -> str:
    if not tree_id:
        return ""
    parts = tree_id.split("_")
    for p in reversed(parts):
        if len(p) == 4 and p.isdigit():
            return p
    return ""


def parse_dhtmlx_bill_records_from_xml(
    xml_text: str,
    *,
    source_tree_node_id: str = "",
    ajax_url: str = "",
    seed_url: str = "",
    base_url: str | None = None,
) -> list[dict[str, str]]:
    """
    One row per ``<item child="1">`` bill group under ``<tree>`` (dhtmlx archive XHR).

    Fields mirror the site's subtree: summary line, DR label, PDF, readings, ministers.
    """
    base = base_url or config.BASE_URL
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError:
        return []
    if root.tag != "tree":
        return []

    tree_year = _year_from_dhtmlx_tree_id(root.get("id"))
    rows: list[dict[str, str]] = []

    for group in root.findall("./item"):
        if group.get("child") != "1":
            continue
        bill_id = (group.get("id") or "").strip()
        summary = (group.get("text") or "").strip()

        dr_label = ""
        pdf_rel = ""
        pdf_name = ""
        first_reading = ""
        second_parts: list[str] = []
        presented_parts: list[str] = []
        passed_parts: list[str] = []

        for child in group.findall("./item"):
            text = (child.get("text") or "").strip()
            myurl = _dhtmlx_userdata_myurl(child)
            m = _DHTMLX_LOAD_RESULT_PAIR.search(myurl) if myurl else None
            if m:
                dr_label = text or dr_label
                pdf_rel = m.group(1).strip()
                pdf_name = (m.group(2) or "").strip()
                continue
            low = text.lower()
            if low.startswith("first reading:"):
                first_reading = text.split(":", 1)[-1].strip()
            elif low.startswith("the second reading:"):
                if text not in second_parts:
                    second_parts.append(text.split(":", 1)[-1].strip())
            elif low.startswith("presented by:"):
                pv = text.split(":", 1)[-1].strip()
                if pv not in presented_parts:
                    presented_parts.append(pv)
            elif low.startswith("passed at:"):
                pv = text.split(":", 1)[-1].strip()
                if pv not in passed_parts:
                    passed_parts.append(pv)

        pdf_url = billindex_url_for_dhtmlx_path(pdf_rel, base)
        pdf_name_out = _dhtmlx_display_filename(pdf_name)

        year = tree_year
        if not year:
            ym = _YEAR_IN_PATH.search(pdf_rel)
            if ym:
                year = ym.group(1)

        rows.append(
            {
                "year": year,
                "bill_item_id": bill_id,
                "summary": summary,
                "dr_label": dr_label,
                "pdf_filename": pdf_name_out,
                "pdf_url": pdf_url,
                "pdf_url_embedded": "",
                "pdf_resolve_status": "",
                "first_reading": first_reading,
                "second_reading": " | ".join(second_parts),
                "presented_by": " | ".join(presented_parts),
                "passed_at": " | ".join(passed_parts),
                "source_tree_node_id": source_tree_node_id,
                "ajax_url": ajax_url,
                "seed_url": seed_url,
            },
        )

    return rows


ARKIB_BILL_CSV_FIELDS: tuple[str, ...] = (
    "year",
    "bill_item_id",
    "summary",
    "dr_label",
    "pdf_filename",
    "pdf_url",
    "pdf_url_embedded",
    "pdf_resolve_status",
    "first_reading",
    "second_reading",
    "presented_by",
    "passed_at",
    "source_tree_node_id",
    "seed_url",
    "ajax_url",
)


# Links on parliament pages often contain these path fragments (tune after inspecting real HTML).
LINK_HREF_SUBSTRINGS: tuple[str, ...] = (
    "bills",
    "bill",
    "billindex",
    "ruu",
    "dewan",
    "attach",
    "pdf",
    ".pdf",
    "akta",
    "webuser",
)


@dataclass(frozen=True)
class ParsedLink:
    """One href resolved to absolute URL with optional anchor text."""

    url: str
    text: str | None


def _interesting_href(href: str) -> bool:
    h = href.lower()
    if h.endswith(".pdf"):
        return True
    return any(s in h for s in LINK_HREF_SUBSTRINGS)


# HTML pages to open when discovering PDFs (one hop from index). Tune as the site changes.
_HTML_FOLLOW_HINTS: tuple[str, ...] = (
    "bill",
    "bills",
    "billindex",
    "ruu",
    "dewan",
    "hansard",
    "attach",
    "arkib",
    "webuser",
)


def is_html_follow_candidate(url: str) -> bool:
    """Same-site page that might link to PDFs (not a PDF URL itself)."""
    if is_pdf_href(url):
        return False
    path = url.split("?", 1)[0].lower()
    if path.endswith((".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2")):
        return False
    u = url.lower()
    return any(h in u for h in _HTML_FOLLOW_HINTS) or path.endswith(".html")


# Sidebar / other sections match ``dewan`` / ``bill`` too easily — use for ``--list-pdfs`` / DR bill harvest.
_DR_FOLLOW_NOISE: tuple[str, ...] = (
    "hansard",
    "ahli-dewan",
    "takwim-dewan",
    "aum-dewan",
    "oral-",
    "written-",
    "committee",
    "kalendar",
    "calendar",
)
_DR_FOLLOW_POSITIVE: tuple[str, ...] = (
    "bills-dewan-rakyat",
    "billindex",
    "/files/billindex",
    "attach",
    "arkib",
    "webuser",
)


def is_dr_bills_follow_candidate(url: str) -> bool:
    """Dewan Rakyat bill PDF discovery: drop DN / hansard / members nav that steals follow budget."""
    if is_pdf_href(url):
        return False
    path = url.split("?", 1)[0].lower()
    if path.endswith((".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2")):
        return False
    u = url.lower()
    if "bills-dewan-negara" in u:
        return False
    if "uweb=dn" in u or "&uweb=dn" in u:
        return False
    if any(n in u for n in _DR_FOLLOW_NOISE):
        return False
    if any(p in u for p in _DR_FOLLOW_POSITIVE):
        return True
    if path.endswith(".html") and "bill" in u and "negara" not in u:
        return True
    return False


def dr_bills_follow_sort_key(url: str) -> tuple[int, str]:
    """Prefer DR bills listing / archive / billindex URLs before other allowed HTML."""
    u = url.lower()
    if "bills-dewan-rakyat" in u:
        pri = 0
    elif "billindex" in u or "/files/billindex" in u:
        pri = 1
    elif "arkib" in u:
        pri = 2
    elif "attach" in u or "webuser" in u:
        pri = 3
    else:
        pri = 5
    return (pri, url)


def extract_pdf_links(html: str, base_url: str) -> list[str]:
    """All same-site ``.pdf`` anchors (broad — for bill pages, acts, attachments)."""
    base = base_url or config.BASE_URL
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    out: list[str] = []
    for tag in soup.find_all("a", href=True):
        raw = tag["href"].strip()
        if not raw or raw.startswith("#"):
            continue
        absolute = urljoin(base, raw)
        if not same_site(absolute):
            continue
        if not is_pdf_href(absolute):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        out.append(absolute)
    return out


# Dewan Rakyat / Negara bill PDFs often appear in page text or JS, not only as <a href>.
_BILLINDEX_PDF_IN_HTML = re.compile(
    r"/files/billindex/pdf/[^\s\"'<>]+\.pdf",
    re.IGNORECASE,
)


def extract_billindex_pdf_urls_from_html(html: str, base_url: str) -> list[str]:
    """Same-site ``/files/billindex/pdf/...pdf`` strings anywhere in HTML (anchors, scripts, data)."""
    base = base_url or config.BASE_URL
    seen: set[str] = set()
    out: list[str] = []
    for m in _BILLINDEX_PDF_IN_HTML.finditer(html):
        path = m.group(0)
        if not path.startswith("/"):
            continue
        absolute = urljoin(base, path)
        if not same_site(absolute):
            continue
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out


def extract_pdf_urls_from_onclick(html: str, base_url: str) -> list[str]:
    """Bill PDF targets referenced only in ``onclick`` / inline handlers (nested table UIs)."""
    base = base_url or config.BASE_URL
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    out: list[str] = []
    for tag in soup.find_all(onclick=True):
        oc = str(tag.get("onclick") or "")
        for m in _BILLINDEX_PDF_IN_HTML.finditer(oc):
            path = m.group(0)
            absolute = urljoin(base, path)
            if same_site(absolute) and absolute not in seen:
                seen.add(absolute)
                out.append(absolute)
        for m in re.finditer(r"['\"]((?:https://[^'\"]+)?/files/billindex/pdf/[^'\"]+\.pdf)['\"]", oc, re.I):
            frag = m.group(1)
            absolute = urljoin(base, frag) if frag.startswith("/") else frag
            if same_site(absolute) and is_pdf_href(absolute) and absolute not in seen:
                seen.add(absolute)
                out.append(absolute)
    return out


def extract_pdf_urls_from_html(html: str, base_url: str) -> list[str]:
    """Union of ``<a href>``, raw HTML billindex strings, and ``onclick`` PDF paths."""
    seen: set[str] = set()
    out: list[str] = []
    for u in extract_pdf_links(html, base_url):
        seen.add(u)
        out.append(u)
    for u in extract_billindex_pdf_urls_from_html(html, base_url):
        if u not in seen:
            seen.add(u)
            out.append(u)
    for u in extract_pdf_urls_from_onclick(html, base_url):
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def extract_pdf_urls_with_xpath(html: str, page_url: str, xpath: str) -> list[str]:
    """
    Evaluate an XPath (lxml) against HTML; extract PDF/billindex URLs from each match.

    Use Chrome “Copy full XPath” as a hint; if the page is malformed, try a shorter path.
    """
    from lxml import html as lhtml
    from lxml.etree import HTMLParser

    parser = HTMLParser(recover=True)
    raw = html.encode("utf-8") if isinstance(html, str) else html
    doc = lhtml.fromstring(raw, parser=parser)
    # Relative ``href`` resolution is handled inside ``extract_pdf_urls_from_html`` via ``page_url``.
    seen: set[str] = set()
    out: list[str] = []
    try:
        nodes = doc.xpath(xpath)
    except Exception:
        return []
    for node in nodes:
        if isinstance(node, str):
            frag = f"<x>{node}</x>"
        else:
            frag = lhtml.tostring(node, encoding="unicode")
        if not frag:
            continue
        for u in extract_pdf_urls_from_html(frag, page_url):
            if u not in seen:
                seen.add(u)
                out.append(u)
    return out


def pdf_filename_from_url(url: str) -> str:
    path = unquote(urlparse(url).path)
    name = path.rstrip("/").split("/")[-1] or "document.pdf"
    if not name.lower().endswith(".pdf"):
        name = f"{name}.pdf"
    return name


def extract_listing_pagination_urls(html: str, page_url: str) -> list[str]:
    """
    Other pages of the *same* listing (same URL path, different query) — e.g. bills table page 2–6.

    Follows same-site ``<a href>`` links whose path matches ``page_url``'s path but full URL differs.
    """
    cur = urlparse(page_url)
    base_path = (cur.path or "/").rstrip("/") or "/"
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    out: list[str] = []
    cur_key = normalize_listing_url_for_dedupe(page_url)
    for tag in soup.find_all("a", href=True):
        raw = tag["href"].strip()
        if not raw or raw.startswith("#"):
            continue
        absolute = urljoin(page_url, raw)
        if not same_site(absolute):
            continue
        p = urlparse(absolute)
        if (p.path or "/").rstrip("/") != base_path.rstrip("/"):
            continue
        nk = normalize_listing_url_for_dedupe(absolute)
        if nk == cur_key:
            continue
        if nk not in seen:
            seen.add(nk)
            out.append(absolute)
    return out


def parse_bill_listing_table_rows(html: str, page_url: str) -> list[dict[str, object]]:
    """
    Best-effort Dewan bills table: Code, Year, Title, Status + any PDF/billindex links in the row.

    DOM varies; returns ``[]`` if no usable table. Used for PDF list context only.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows_out: list[dict[str, object]] = []
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue
            cells = [td.get_text(strip=True) for td in tds]
            if not any(cells):
                continue
            head_guess = " ".join(c.lower() for c in cells[: min(4, len(cells))])
            if "code" in head_guess and "year" in head_guess and (
                "title" in head_guess or "tajuk" in head_guess or "status" in head_guess
            ):
                continue

            if len(cells) >= 4:
                code, year = cells[0], cells[1]
                status = cells[-1]
                title = " ".join(cells[2:-1]) if len(cells) > 4 else cells[2]
            elif len(cells) == 3:
                code, year, title, status = cells[0], None, cells[1], cells[2]
            else:
                continue

            pdf_urls: list[str] = []
            seen_pdf: set[str] = set()
            row_html = str(tr)
            for u in extract_pdf_urls_from_html(row_html, page_url):
                if u not in seen_pdf:
                    seen_pdf.add(u)
                    pdf_urls.append(u)
            for a in tr.find_all("a", href=True):
                href = urljoin(page_url, a["href"].strip())
                if not same_site(href):
                    continue
                if is_pdf_href(href) or "/files/billindex/pdf/" in href.lower():
                    if href not in seen_pdf:
                        seen_pdf.add(href)
                        pdf_urls.append(href)

            rows_out.append(
                {
                    "code": code or None,
                    "year": year or None,
                    "title": title or None,
                    "status": status or None,
                    "pdf_urls": pdf_urls,
                },
            )
    return rows_out


def extract_index_links(html: str, base_url: str | None = None) -> list[ParsedLink]:
    """
    From a bill *index* page, return a de-duplicated list of candidate bill/document URLs.

    ``base_url`` should be the page URL used to resolve relative links
    (e.g. https://www.parlimen.gov.my/bills-dewan-rakyat.html).
    """
    base = base_url or config.BASE_URL
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    out: list[ParsedLink] = []

    for tag in soup.find_all("a", href=True):
        raw = tag["href"].strip()
        if not raw or raw.startswith("#"):
            continue
        absolute = urljoin(base, raw)
        if not same_site(absolute):
            continue
        if not _interesting_href(absolute):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        text = tag.get_text(strip=True) or None
        out.append(ParsedLink(url=absolute, text=text))

    return out


def extract_dr_bill_ids(html: str) -> list[str]:
    """
    Dewan Rakyat bills are often labeled like ``D.R. 66/2024`` in page text.
    Regex helper for alerting / dedupe when link structure is opaque.
    """
    pattern = re.compile(r"\bD\.?\s*R\.?\s*\d+\s*/\s*\d{4}\b", re.IGNORECASE)
    return list(dict.fromkeys(m.group(0) for m in pattern.finditer(html)))


def parse_fetched_index(
    html: str,
    *,
    source_url: str,
) -> dict[str, object]:
    """Structured summary for logging or downstream semantic layer."""
    links = extract_index_links(html, base_url=source_url)
    bill_ids = extract_dr_bill_ids(html)
    pdf_urls_on_page = extract_pdf_urls_from_html(html, source_url)
    bill_table_rows = parse_bill_listing_table_rows(html, source_url)
    return {
        "source_id": config.SOURCE_ID,
        "index_url": source_url,
        "link_count": len(links),
        "links": [{"url": L.url, "text": L.text} for L in links],
        "pdf_urls_on_page": pdf_urls_on_page,
        "bill_table_rows": bill_table_rows,
        "detected_dr_labels": bill_ids,
    }
