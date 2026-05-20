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

## Crawl — Malaysia Parliament

```bash
# Crawl bill index → per-year CSVs under src/out/bills_csv/
python -m lib.sources.my.parliament_my.crawl \
  --list-arkib-bills \
  --arkib-csv-dir src/out/bills_csv

# Also resolve PDF URLs (parallel probes)
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
