"""
Fetch raw HTML (or PDF) from Parliament of Malaysia URLs and compute content hashes.

Flow (from blueprint): fetch → hash → compare → if changed → store snapshot → parse.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

import requests

from . import config
from .error_pages import soft_error_label


@dataclass
class FetchResult:
    """Minimal ingestion envelope aligned with blueprint snapshot metadata."""

    source: str
    url: str
    fetched_at: str  # ISO8601 Z
    content_hash: str
    raw_bytes: bytes | None
    status: str  # "ok" | "unchanged" (caller sets unchanged when comparing hashes) | "error"
    http_status: int | None = None
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_url(
    url: str,
    *,
    prior_hash: str | None = None,
    headers: dict[str, str] | None = None,
    timeout_s: int | None = None,
    verify: bool | str = True,
    allow_redirects: bool = True,
    session: requests.Session | None = None,
) -> FetchResult:
    """
    GET ``url`` and return bytes + hash. If ``prior_hash`` matches, you may skip parsing.

    Note: parlimen.gov.my often returns 403 for non-browser/datacenter clients.

    Optional ``session`` keeps cookies (e.g. after an EN arkib landing GET so XHR/PDF match browser language context).
    """
    hdrs = {**config.DEFAULT_HEADERS, **(headers or {})}
    timeout = timeout_s if timeout_s is not None else config.FETCH_TIMEOUT_S
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    get = session.get if session is not None else requests.get

    try:
        resp = get(
            url,
            headers=hdrs,
            timeout=timeout,
            verify=verify,
            allow_redirects=allow_redirects,
        )
        final_url = str(getattr(resp, "url", url))
        body = resp.content or b""
        digest = sha256_bytes(body)

        if prior_hash is not None and digest == prior_hash:
            return FetchResult(
                source=config.SOURCE_ID,
                url=url,
                fetched_at=now,
                content_hash=digest,
                raw_bytes=body,
                status="unchanged",
                http_status=resp.status_code,
                meta={"note": "content hash matches prior_hash", "final_url": final_url},
            )

        err = None
        status = "ok"
        meta: dict[str, Any] = {"final_url": final_url}
        if resp.status_code >= 400:
            status = "error"
            err = f"HTTP {resp.status_code}"
        elif resp.status_code == 200:
            # Do not run HTML error-page heuristics on PDF bytes (or obvious PDF URLs).
            path_lower = url.split("?", 1)[0].lower()
            looks_pdf = path_lower.endswith(".pdf") or (len(body) >= 4 and body[:4] == b"%PDF")
            if not looks_pdf:
                text = body.decode("utf-8", errors="replace")
                soft = soft_error_label(text)
                if soft is not None:
                    status = "error"
                    err = f"soft_200 ({soft})"
                    meta["soft_http_error"] = True
                    meta["soft_error_class"] = soft

        return FetchResult(
            source=config.SOURCE_ID,
            url=url,
            fetched_at=now,
            content_hash=digest,
            raw_bytes=body,
            status=status,
            http_status=resp.status_code,
            error=err,
            meta=meta,
        )
    except requests.RequestException as e:
        return FetchResult(
            source=config.SOURCE_ID,
            url=url,
            fetched_at=now,
            content_hash="",
            raw_bytes=None,
            status="error",
            error=str(e),
        )


def probe_pdf_magic(
    url: str,
    *,
    verify: bool = True,
    headers: dict[str, str] | None = None,
    timeout_s: int | None = None,
    cookies: Mapping[str, str] | None = None,
) -> bool:
    """
    True if a short GET returns PDF magic bytes (``%PDF``).

    Tries ``Range: bytes=0-4`` first; some origins mis-handle Range, so we fall back to a tiny
    streamed GET without Range.

    ``cookies`` can carry the jar from an ``lang=en`` arkib landing page so PDF GETs match the same
    language/session as the tree (parlimen may reject cross-language PDF fetches).
    """
    hdrs = {**config.DEFAULT_HEADERS, **(headers or {})}
    timeout = timeout_s if timeout_s is not None else config.FETCH_TIMEOUT_S
    ck = dict(cookies) if cookies else None

    def _check(resp: requests.Response) -> bool:
        try:
            if resp.status_code not in (200, 206):
                return False
            chunk = next(resp.iter_content(8), b"")
            return len(chunk) >= 4 and chunk[:4] == b"%PDF"
        finally:
            resp.close()

    try:
        resp = requests.get(
            url,
            headers={**hdrs, "Range": "bytes=0-7"},
            timeout=timeout,
            verify=verify,
            allow_redirects=True,
            stream=True,
            cookies=ck,
        )
        if _check(resp):
            return True
    except requests.RequestException:
        pass

    try:
        resp = requests.get(
            url,
            headers=hdrs,
            timeout=timeout,
            verify=verify,
            allow_redirects=True,
            stream=True,
            cookies=ck,
        )
        return _check(resp)
    except requests.RequestException:
        return False


def fetch_all_indices(
    *,
    prior_by_url: dict[str, str] | None = None,
    verify: bool | str = True,
) -> list[FetchResult]:
    """Fetch each configured index URL (e.g. for a daily cron)."""
    prior_by_url = prior_by_url or {}
    out: list[FetchResult] = []
    for url in config.BILL_INDEX_URLS:
        prior = prior_by_url.get(url)
        out.append(fetch_url(url, prior_hash=prior, verify=verify))
    return out


def result_to_snapshot_dict(r: FetchResult) -> dict[str, Any]:
    """Shape suitable for JSONL event log or DB row (raw body stored separately on disk)."""
    return {
        "source": r.source,
        "url": r.url,
        "fetched_at": r.fetched_at,
        "content_hash": r.content_hash,
        "status": r.status,
        "http_status": r.http_status,
        "error": r.error,
        "meta": r.meta,
    }
