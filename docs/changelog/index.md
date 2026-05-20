---
title: Changelog
description: Release history and upcoming changes for parawl.
tags: [releases, changelog]
---

# Changelog

All notable changes to parawl are recorded here.
Dates are in `YYYY-MM-DD` format. Versions follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Planned
- `pipeline/download.py` — PDF downloader with idempotency, TLS fallback, session cookie support
- `pipeline/chunk.py` — split extracted Markdown into LLM-ready JSONL chunks with metadata
- `pipeline/analyze.py` — LLM impact analysis producing structured `analysis.json`
- `src/lib/sources/my/parliament_my/` — Dewan Negara (Senate) bill coverage
- Base class `ParliamentSource` — formal interface for new adapters

---

## [0.1.0] — 2026-05-20

Initial public release. Extracted from the [StateConscious](https://github.com/q3dresearch/stateconscious) monorepo.

### Added
- **`my.parliament_my` adapter** — crawls parlimen.gov.my Dewan Rakyat bills, 1990–present
  - Live index parser (`parse.py`) — HTML table, pagination
  - Archive crawler (`dhtmlx_arkib.py`) — AJAX XML tree walk, per-year CSV output
  - PDF discovery (`pdf_discovery.py`) — resolves and validates PDF URLs
  - Error page detection (`error_pages.py`) — catches soft-200 HTML error responses
  - TLS fallback, session cookie support (`config.py`, `fetch.py`)
- **`pipeline/extract.py`** — PDF → Markdown extraction using `pymupdf4llm` (primary) with `pypdf` fallback
- **`lib/artifacts.py`** — content-addressed paths under `data/raw/` and `data/derived/`
- **`lib/paths.py`** — `repo_root()` for consistent path resolution across modules
- **`lib/sources/discovery.py`** — discovers adapters and seed URLs from `seed_urls.txt` files
- **`lib/parser/seed_txt.py`** — parses `seed_urls.txt` into (url, role) pairs
- **Tests** — parliament HTML parser, dhtmlx XML parser, PDF URL resolution, deduplication, discovery
- **MkDocs Material site** — pipeline, sources, architecture, tests, changelog docs
- **GitHub Actions** — CI (pytest) + docs deploy to GitHub Pages on push to `main`
- **Skills** — `.claude/skills/sc-download`, `sc-extract`, `sc-analyze` for agent-assisted pipeline runs

### Source coverage at release

| Adapter | Source | Bills indexed |
|---------|--------|--------------|
| `my.parliament_my` | parlimen.gov.my — Dewan Rakyat | ~1,100 (1990–2025) |
