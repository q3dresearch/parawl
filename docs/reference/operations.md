---
title: Operations
description: Common commands for running parawl crawlers and pipeline stages.
tags: [operations, cli, commands]
---

# Operations

Quick reference for running parawl locally.
All commands assume the virtualenv is active and you are in the repo root.

## Setup

=== "Windows"

    ```powershell
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    $env:PYTHONPATH = "$PWD\src"
    ```

=== "macOS / Linux"

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    export PYTHONPATH="$PWD/src"
    ```

---

## Output directories (all gitignored)

```
parawl/
├── src/out/                        ← crawl index CSVs
│   ├── bills_csv/bills_2024.csv    bill metadata + pdf_url per year
│   └── hansard_csv/
│       └── hansard_DR_2024.csv     sitting metadata + pdf_url per house+year
│
└── data/                           ← downloaded and derived artifacts
    ├── raw/parliament_my/pdf/
    │   └── 2024/
    │       ├── DR-6-2024.pdf
    │       └── DR-6-2024.meta.json    sha256, url, downloaded_at
    └── derived/parliament_my/extracted/
        └── 2024/
            └── DR-6-2024.md           extracted Markdown text
```

None of these directories are committed to git — they are runtime outputs produced by the crawl and pipeline stages.

---

## Crawl — Bills (Rang Undang-Undang)

```bash
# Crawl bill index → per-year CSVs under src/out/bills_csv/
python -m lib.sources.my.parliament_my.crawl \
  --list-arkib-bills \
  --arkib-csv-dir src/out/bills_csv

# Also resolve PDF URLs (parallel probes — confirms each link is reachable)
python -m lib.sources.my.parliament_my.crawl \
  --list-arkib-bills \
  --arkib-csv-dir src/out/bills_csv \
  --arkib-resolve-pdfs

# TLS bypass for dev environments with cert issues
python -m lib.sources.my.parliament_my.crawl --list-arkib-bills --insecure

# Print bill JSON to stdout without writing CSVs
python -m lib.sources.my.parliament_my.crawl --list-arkib-bills
```

---

## Crawl — Hansard (Penyata Rasmi)

```bash
# Fast path: Parliament 15 only (2022–present), one CSV per house+year
python -m lib.sources.my.parliament_my.crawl \
  --list-hansard \
  --hansard-parliament 15 \
  --hansard-csv-dir src/out/hansard_csv

# Filter to a single year (also scopes BFS to relevant parliament)
python -m lib.sources.my.parliament_my.crawl \
  --list-hansard \
  --hansard-year 2024 \
  --hansard-csv-dir src/out/hansard_csv

# Full archive sweep — all parliaments 1–15 (slow, ~8000 nodes)
python -m lib.sources.my.parliament_my.crawl \
  --list-hansard \
  --hansard-csv-dir src/out/hansard_csv

# TLS bypass (dev)
python -m lib.sources.my.parliament_my.crawl --list-hansard --insecure
```

---

## Download + Extract sample

A single script crawls, downloads, and extracts a small batch of PDFs into the gitignored `data/` directory:

```bash
python scripts/sample_crawl.py --insecure
```

PDFs land in `data/raw/parliament_my/pdf/<year>/`.  
Extracted Markdown lands in `data/derived/parliament_my/extracted/<year>/`.

---

## Extract — PDF → Markdown

Run after PDFs are downloaded into `data/raw/`.

```bash
python -m lib.pipeline.extract
python -m lib.pipeline.extract --force   # re-extract existing files
```

---

## Tests

```bash
pip install -r requirements-dev.txt
pytest -v

# Single file
pytest tests/test_dhtmlx_dedupe.py -v

# Filter by test name
pytest -v -k "bm"

# Skip live network tests (default behaviour)
pytest -v -m "not live_parliament"
```

---

## Docs (local preview)

```bash
pip install mkdocs-material
mkdocs serve
# open http://127.0.0.1:8000
```
