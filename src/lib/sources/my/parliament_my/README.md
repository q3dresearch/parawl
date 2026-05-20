# Adapter: Parliament of Malaysia (`parliament_my`)

Site-specific fetch/parse lives here. **Global policy:** `mds/agents/crawlerAgent.md`. **Registry (seeds):** this folder’s **`seed_urls.txt`** + **`config.py`** (`CRAWL_NOTES`, `SOURCE_ID`).

## Discovery model (no `sitemap.xml`)

This site does **not** expose a reliable **`/sitemap.xml`** for a generic “Google-style” PDF sweep. Crawl strategy is:

1. **Poll URLs** from `source_library` / `seed_urls.txt` (listing and archive variants).
2. **Parse HTML** (`parse.py`) — link heuristics tuned to `parlimen.gov.my`.
3. **Optional descent** — **`crawl --list-pdfs --deep-listing`** (follow HTML + pagination) to reach `/images/webuser/akta/…` and bill PDFs.

A future **shared** `sitemap` crawler can run **when** `sitemap_url` exists in config; this adapter stays **HTML-first** until then.

## URL hints (operational)

| Hint | Meaning |
|------|---------|
| `?uweb=dr` | Dewan Rakyat–oriented listing; often closer to the real bill table than the bare bills URL. |
| `?uweb=dr&arkib=yes` | Archive-style listing (historical years). |
| `/images/webuser/akta/` | Common path prefix for **Act** PDFs (not exhaustive). |
| `/files/billindex/pdf/…` | Dewan bill PDFs (also matched inside page/JS text, not only `<a href>`). |
| `.pdf` | Treat as document target; verify bytes (`%PDF` magic). |

**List PDF URLs only (no PDF download):** `--list-pdfs` does **one GET per URL** and extracts PDFs **only from that response** (no following links, no pagination). URLs = each `--url` you pass, or every line in **`seed_urls.txt`** if you omit `--url`. Optional `--xpath` (lxml) unions matches with the full-page extract. For the old behaviour (pagination + `--follow-html`), add **`--deep-listing`**. Optional `--no-redirect` on HTTP.

**DR archive without Playwright:** Dewan Rakyat archive pages (`bills-dewan-rakyat` + `arkib=yes`) load the year tree via XHR: same path with **`ajx=1`**, **`uid`** (epoch ms), and **`id`** (tree node). With **`--list-pdfs`** (non–deep-listing), those URLs are swept automatically: BFS on the XML and **`loadResult('/files/billindex/pdf/…')`** paths (see **`dhtmlx_arkib.py`**). Cap fetches with **`--arkib-dhtmlx-max-nodes`**. Use **`--no-dhtmlx-arkib-sweep`** to force a single literal GET. `--xpath` is ignored for sweep URLs (verbose logs a note).

**How those `id=` values work (you don’t enumerate them by hand):**

| Query part | Role |
|------------|------|
| **`uid`** | Opaque per-request timestamp; the crawler generates a fresh value each GET. It does **not** identify a year or bill. |
| **`id`** | dhtmlxTree node id. **`0`** is the root. Children look like **`0_2024`**, **`0_1993`** — year (or branch) segments chosen by the site, not by you. Deeper nodes add more `_…` segments. |
| **Crawl** | Start at **`id=0`**, parse XML, collect PDFs from **`loadResult`**, find every **`<item child="1" id="…">`**, enqueue those ids, repeat (BFS) until the queue is empty or **`--arkib-dhtmlx-max-nodes`** stops the run. If the root response already embeds many bills, you still get them at node **`0`**; expanding **`0_1993`** etc. adds bills that only appear under that year. |

If stderr prints a **max-nodes warning** with nodes still queued, raise **`--arkib-dhtmlx-max-nodes`** (historical archive + many years needs a higher cap than the default).

**Structured bills + CSV:** **`--list-arkib-bills`** runs the same dhtmlx BFS but emits one JSON object per bill group (summary, DR label, readings, ministers, PDF URL). Add **`--arkib-csv-dir path/to/dir`** to write **`bills_2024.csv`**, **`bills_1993.csv`**, … (one file per `year` column; UTF-8 with BOM for Excel). JSON still goes to stdout.

**Embedded `pdf_url` is not always the file you want:** The tree often points at **BM** (`DR … BM.pdf`) while **BI** or legacy **`…E.pdf`** is what you need. Merge rules prefer **year bucket XHR** over **root / `0_0`**, **BI** over **BM**, and legacy **`…E.pdf`** over bare **`DRddyyyy.pdf`** (see **`parse.bill_record_merge_rank`** / **`dedupe_bill_records`**). **`--list-arkib-bills` never keeps BM billindex URLs** in output: after optional **`--arkib-resolve-pdfs`**, **`drop_bm_billindex_urls`** clears any remaining **`… BM.pdf`** rows (use resolve so **BI** / **E** can replace them). Pattern candidates are **BI / E / compact** only (see **`dhtmlx_arkib.py`**).

Add new path fragments to **`parse.py`** (`LINK_HREF_SUBSTRINGS`, `_HTML_FOLLOW_HINTS`) when you confirm them in saved HTML—not only in this README.

## Failure modes

- **403 / TLS** — see `fetch.py` / ops `--insecure` (dev only).
- **HTTP 200 + error HTML** — `error_pages.py` / `soft_200` in `crawl_history`.

## Code map

| Module | Role |
|--------|------|
| `config.py` | `SOURCE_ID`, headers, timeouts; index URLs from local **`seed_urls.txt`**. |
| `fetch.py` | GET + hash; PDF vs HTML soft-error rules. |
| `error_pages.py` | Application-level error page strings. |
| `parse.py` | HTML + billindex: links, PDF extraction, dhtmlx XML → bill rows, merge ranks, CSV fields. |
| `pdf_discovery.py` | `list_pdfs_from_seed_file` / `list_pdfs_from_urls`; HTML fetch only. |
| `dhtmlx_arkib.py` | Archive: sweep `ajx=1` XML for PDFs and/or structured bill rows; per-year CSV helper. |



