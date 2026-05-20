# Pipeline — Download

**Module:** `src/lib/pipeline/download.py`  
**Input:** `src/out/bills_csv/bills_<year>.csv` — rows with a non-empty `pdf_url`  
**Output:** `data/raw/<adapter>/pdf/<year>/<bill_id>.pdf` + `<bill_id>.meta.json`

## What it does

Fetches the PDF for each bill and writes it to content-addressed local storage. If the PDF is already on disk (same URL already has a `crawl_history` row with `outcome=success`), the bill is skipped.

## Change detection strategy

**Decision: trust the source.** Download each bill PDF once. Re-crawl the index periodically to detect new bills and status changes. Do not attempt to detect silent PDF content edits.

**Rationale:** Parliament bill PDFs are official tabled documents — silent content edits are rare and low-stakes. The added complexity of change detection (HEAD checks, periodic re-downloads) is not justified for MVP.

**Known blind spot:** if the government silently replaces a PDF at the same URL (e.g. a typo correction), the pipeline will not detect it. The stored PDF may differ from the current live version.

**Cron modes this implies:**

| Mode | Frequency | What it does |
|------|-----------|--------------|
| `index` | Weekly | Re-crawl the bill index; find new bill rows; queue new downloads |
| `fetch` | Per index run | Download PDFs for bills not yet in storage |

**Future option (not implemented):** HTTP HEAD checks — send `HEAD` to each known PDF URL and compare `Content-Length` / `ETag` headers against what is stored in `.meta.json`. Cheap proxy for change detection. Caveat: government servers may not update these headers reliably when a file is silently replaced, so HEAD checks are a heuristic, not a guarantee. Document as a v2 improvement if silent edits become a practical problem.

## Idempotency key

The bill's natural key: `<year>/<bill_id>` (e.g. `2024/DR-21-2024`). If the `.pdf` file already exists at that path, the bill is skipped. SHA-256 is computed on download and stored in the `.meta.json` sidecar — used for future change detection, not for path addressing.

## CLI

```bash
PYTHONPATH=src python -m lib.pipeline.download --source parliament_my --max 20
PYTHONPATH=src python -m lib.pipeline.download --source parliament_my --dry-run
PYTHONPATH=src python -m lib.pipeline.download --source parliament_my --year 2024
```

## Error logging

Every fetch attempt — success or failure — produces a `crawl_history` row. Key fields:

| Field | Meaning |
|-------|---------|
| `url` | `pdf_url` from the CSV |
| `outcome` | `success` / `skip` / `error` / `soft_200` / `timeout` |
| `http_status` | HTTP response code |
| `sha256` | Hash of bytes (only on success; also written to `.meta.json`) |
| `raw_pdf_relpath` | Relative path: `data/raw/<adapter>/pdf/<year>/<bill_id>.pdf` |
| `content_length` | Response `Content-Length` header (baseline for future HEAD checks) |
| `tls_fallback` | `true` if TLS verification was skipped |
