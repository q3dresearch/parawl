"""
On-disk artifact layout (immutable raw vs derived).

**Why here:** adapter-agnostic path helpers used by every crawl implementation under
``lib/sources/``. Keeps ``data/raw`` / ``data/derived`` layout in one place.

Layout (stable contract):
  data/raw/<adapter_id>/runs.jsonl
  data/raw/<adapter_id>/html/<content_sha256>/<filename>   — immutable HTML (or text) bytes
  data/raw/<adapter_id>/pdf/<content_sha256>/<filename> — immutable PDF bytes
  data/derived/<adapter_id>/parsed/<content_sha256>/<filename>.json

``content_sha256`` is the full hex digest (64 chars for SHA-256), not a “latest” symlink.

Legacy ``data/snapshots/<adapter>/`` may still exist from early runs; new writes use the paths above.
"""

from __future__ import annotations

from pathlib import Path

from lib.paths import repo_root


def raw_adapter_dir(adapter_id: str) -> Path:
    return repo_root() / "data" / "raw" / adapter_id


def raw_html_dir(adapter_id: str) -> Path:
    return raw_adapter_dir(adapter_id) / "html"


def raw_html_snapshot_path(adapter_id: str, content_hash: str, filename: str) -> Path:
    """One fetched document: directory per full hash so renames/versioning stay unambiguous."""
    return raw_html_dir(adapter_id) / content_hash / filename


def raw_pdf_dir(adapter_id: str) -> Path:
    return raw_adapter_dir(adapter_id) / "pdf"


def raw_pdf_snapshot_path(adapter_id: str, content_hash: str, filename: str) -> Path:
    return raw_pdf_dir(adapter_id) / content_hash / filename


def runs_jsonl_path(adapter_id: str) -> Path:
    return raw_adapter_dir(adapter_id) / "runs.jsonl"


def derived_parsed_dir(adapter_id: str) -> Path:
    return repo_root() / "data" / "derived" / adapter_id / "parsed"


def derived_parsed_snapshot_path(adapter_id: str, content_hash: str, stem: str) -> Path:
    """Parsed sidecar for one raw snapshot (stem usually equals URL basename without query)."""
    safe = stem if stem.endswith(".json") else f"{stem}.json"
    return derived_parsed_dir(adapter_id) / content_hash / safe
