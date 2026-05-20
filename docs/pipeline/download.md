---
title: Download
description: Pipeline stage — fetch bill PDFs from resolved URLs into local storage.
tags: [pipeline, download, pdf]
status: planned
---

# Pipeline — Download

!!! warning "Planned"
    `lib.pipeline.download` is not yet implemented. This page documents the intended design.

**Module:** `src/lib/pipeline/download.py`
**Input:** `src/out/bills_csv/bills_<year>.csv` — rows with a non-empty `pdf_url`
**Output:** `data/raw/<adapter>/pdf/<year>/<bill_id>.pdf` + `<bill_id>.meta.json`

## What it will do

Fetch the PDF for each bill and write it to addressed local storage. If the PDF already exists at that path, the bill is skipped.

## Idempotency

The bill's natural key `<year>/<bill_id>` (e.g. `2024/DR-21-2024`) determines the artifact path. If `.pdf` already exists, skip. SHA-256 is computed on download and stored in `.meta.json` — useful for change detection later, not for path addressing.

## Output per bill

```
data/raw/my/parliament_my/pdf/2024/
  DR-21-2024.pdf
  DR-21-2024.meta.json
```

`.meta.json` schema:

```json
{
  "bill_id": "DR-21-2024",
  "url": "https://...",
  "sha256": "abc123...",
  "content_length": 204800,
  "outcome": "success",
  "tls_fallback": false,
  "downloaded_at": "2026-05-20T00:00:00Z"
}
```

## Known edge cases to handle

| Case | Handling |
|------|----------|
| TLS failure | Retry with `verify=False`; set `tls_fallback: true` in `.meta.json` |
| Soft-200 HTML error page | Detect via `error_pages.py`; write `outcome: soft_200` |
| Non-PDF content type | Skip; write `outcome: wrong_content_type` |
| Session cookie required | Read `PARLIMEN_COOKIE` from `.env`; pass as `Cookie` header |
| Network timeout | Write `outcome: timeout` |

## Planned CLI

```bash
PYTHONPATH=src python -m lib.pipeline.download --source parliament_my --max 20
PYTHONPATH=src python -m lib.pipeline.download --source parliament_my --dry-run
PYTHONPATH=src python -m lib.pipeline.download --source parliament_my --year 2024
```
