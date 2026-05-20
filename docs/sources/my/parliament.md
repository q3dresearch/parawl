# Malaysia — Parliament (Dewan Rakyat)

**Adapter ID:** `parliament_my`  
**Country:** Malaysia (`my`)  
**State:** Federal  
**Category:** Bills  
**Source URL:** `https://www.parlimen.gov.my/bills-dewan-rakyat.html`

## What it covers

Bills tabled in the Dewan Rakyat (lower house of Parliament) from 1990 to present. Each bill record includes:

| Field | Description |
|-------|-------------|
| `dr_label` | Bill reference number (e.g. `D.R.21/2024`) |
| `summary` | Title and pass status |
| `first_reading` | Date tabled |
| `second_reading` | Date debated |
| `passed_at` | Date passed (if passed) |
| `presented_by` | Minister who tabled the bill |
| `pdf_url` | Direct link to the bill PDF on parlimen.gov.my |

## Crawl strategy

```mermaid
graph TD
  A[seed_urls.txt<br/>live index + archive URL] --> B[fetch.py<br/>GET with session cookie]
  B --> C{Page type?}
  C -->|live index<br/>?uweb=dr| D[parse.py<br/>HTML table parser]
  C -->|archive<br/>?uweb=dr&arkib=yes| E[dhtmlx_arkib.py<br/>AJAX XML tree]
  D --> F[bill rows<br/>dr_label · title · status · dates]
  E --> G[dhtmlx XML<br/>ajx=1 per node]
  G --> H[pdf_discovery.py<br/>resolve PDF URLs]
  F --> I[bills_<year>.csv]
  H --> I
  I --> J[pipeline: download → extract]
```

## Index format

The site uses two different formats depending on which index is being crawled:

**Live index** (`?uweb=dr`) — standard HTML table, parsed by `parse.py`.

**Archive** (`?uweb=dr&arkib=yes`) — uses a **dhtmlx tree** served over AJAX (`ajx=1` query param).
`dhtmlx_arkib.py` fetches the XML tree node-by-node and extracts bill rows, then resolves PDF URLs via `pdf_discovery.py`.

Historical bills (pre-~2010) may have missing or broken PDF URLs; `pdf_resolve_status` records whether the PDF link was confirmed reachable.

## Known quirks

- **TLS issues:** some clients see certificate verification failures; use `--insecure` as a dev bypass, documented in `config.py`.
- **Soft-200 errors:** the site sometimes returns HTTP 200 with an HTML error page ("An error has occurred" or `"File does not exist (3)"`). Detected by `error_pages.py`; logged as `outcome=soft_200`.
- **Session / language cookie required:** direct PDF URLs return `"File does not exist (3)"` unless the site has been visited first in a browser with the language set to English. This sets a session cookie that authorises PDF serving. **Workaround for the download pipeline:** visit `parlimen.gov.my`, set language to EN, copy the session cookies from browser DevTools, store in `.env` as `PARLIMEN_COOKIE`, and pass as `Cookie` header in download requests.
- **Bilingual PDFs:** bills are published in Bahasa Malaysia and English (often both in one PDF).
- **Missing 2003:** no bills in the CSV for 2003; appears to be a gap in the site's own archive.

## Coverage

| Period | Bill count (approx.) |
|--------|----------------------|
| 1990–2009 | ~700 |
| 2010–2019 | ~280 |
| 2020–2024 | ~100 |
| **Total** | **~1,100** |

## CLI

```bash
# List all bills (JSON to stdout)
PYTHONPATH=src python -m lib.sources.my.parliament_my.crawl --list-arkib-bills

# Write per-year CSVs
PYTHONPATH=src python -m lib.sources.my.parliament_my.crawl \
  --list-arkib-bills --arkib-csv-dir src/out/bills_csv

# Resolve PDF URLs (probes each URL in parallel)
PYTHONPATH=src python -m lib.sources.my.parliament_my.crawl \
  --list-arkib-bills --arkib-resolve-pdfs
```

## What's not covered

- **Dewan Negara (Senate):** bills from the upper house are a separate source, not yet added.
- **Private members' bills:** rare; may appear in the index but are often not separately PDFs.
- **Amendments to existing Acts (consolidated text):** this adapter captures the bill as tabled, not the consolidated version of the Act after amendment. The full consolidated Acts are on `agc.gov.my` — a separate future adapter.
