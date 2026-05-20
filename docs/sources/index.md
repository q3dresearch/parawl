# Sources — Overview

A **source** is any public legal publication endpoint that StateConscious can periodically ingest. Each source is wrapped in an **adapter** — a Python module under `src/lib/sources/<region>/<adapter_id>/` — that knows how to fetch, classify, and parse that site's specific format.

## How sources are organised

Sources are classified along three axes:

| Axis | Examples |
|------|---------|
| **Country** | `my` (Malaysia), `sg` (Singapore), `gb` (United Kingdom) |
| **State / territory** | `federal`, `selangor`, `sabah`, `sarawak` |
| **Category** | `bills`, `acts`, `gazette`, `subsidiary_legislation`, `hansard` |

See [Taxonomy](taxonomy.md) for the full classification.

## Adapter structure

Each adapter lives at `src/lib/sources/<country>/<adapter_id>/` and contains:

| File | Role |
|------|------|
| `seed_urls.txt` | One poll URL per line; optional `URL<TAB>label` |
| `config.py` | `SOURCE_ID`, `RESOURCE_KIND`, `CRAWL_NOTES`, headers |
| `fetch.py` | HTTP fetch logic specific to this site |
| `parse.py` | HTML / XML / PDF link extraction |
| `crawl.py` | CLI entrypoint (`python -m lib.sources.<...>.<adapter>.crawl`) |
| `README.md` | Site-specific notes (TLS quirks, known errors, format changes) |

## Active adapters

| Adapter ID | Country | Category | Notes |
|------------|---------|----------|-------|
| `parliament_my` | Malaysia | Bills (Dewan Rakyat) | 1990–present; dhtmlx tree index; PDFs on parlimen.gov.my |

## Adding a new source

1. Create `src/lib/sources/<country>/<adapter_id>/` with the files above.
2. Add at least one URL to `seed_urls.txt`.
3. Run `python scripts/init_db.py` to seed `source_library`.
4. Document site-specific quirks in `README.md`.
5. Add the adapter to this page.
