---
skill: sc-download
phase: 0
version: 0.2
pipeline_stage: download
next_skill: sc-extract
---

# sc-download — Bill PDF Downloader

Download bill PDFs from their `pdf_url` into year/bill_id addressed local storage.

## Task outline

- Read bill rows from `src/out/bills_csv/` (skip rows with empty or failed `pdf_url`)
- Derive `bill_id` from `dr_label` (e.g. `D.R.21/2024` → `DR-21-2024`)
- Check if `data/raw/<adapter>/pdf/<year>/<bill_id>.pdf` already exists; skip if so
- Download PDF bytes; verify magic bytes start with `%PDF`; compute SHA-256
- Write PDF to `data/raw/<adapter>/pdf/<year>/<bill_id>.pdf`
- Write sidecar `<bill_id>.meta.json` with sha256, url, content_length, outcome, downloaded_at
- Log outcome to `crawl_history`
- Respect `--max N` budget and `--dry-run` flag

## Error cases to handle

- TLS failures (retry with insecure, log tls_fallback in meta.json)
- Soft-200 HTML error pages (use `error_pages` module — body starts with "File does not exist" etc.)
- Non-PDF content types (Content-Type not application/pdf)
- Network timeouts
- Missing session cookie (PARLIMEN_COOKIE not set in .env)

## Implementation target

`src/lib/pipeline/download.py` — callable as `python -m lib.pipeline.download`

## Key constraint

`<year>/<bill_id>` is the idempotency key. If the PDF file exists at that path, skip — do not re-download. SHA-256 lives in `.meta.json`, not in the path.
