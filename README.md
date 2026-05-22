# parawl

Southeast Asia parliamentary document crawler and parser library.

Crawl, download, extract, and chunk bill and Hansard documents from public government sources.
No hosted service required — run it locally, own your data.

## What this is

`parawl` is a **source plugin library**. Each country/chamber is a self-contained adapter.
The core pipeline stages (download → extract → chunk) are shared across all adapters.

This is the data producer layer. It has no opinion on where your data goes after extraction —
pipe it to SQLite, a vector store, a search index, or a folder on your machine.

## Current sources

| Adapter | Source | Coverage |
|---|---|---|
| `my.parliament_my` | parlimen.gov.my — Bills (Dewan Rakyat) | 1990–present |
| `my.parliament_my` | parlimen.gov.my — Hansard / Penyata Rasmi | 1959–present |

## Pipeline stages

```
crawl     →  discover bill/hansard URLs from the source site
download  →  fetch PDFs into data/raw/<adapter>/<year>/<bill_id>.pdf
extract   →  PDF → Markdown via pymupdf4llm (pypdf fallback)
chunk     →  (planned) split markdown into LLM-ready chunks with metadata
```

Each stage is callable independently:

```bash
python -m lib.pipeline.extract --adapter my.parliament_my --year 2024
```

## Quickstart

```bash
git clone https://github.com/q3dresearch/parawl
cd parawl
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export PYTHONPATH=src
```

> **Note:** Use `python -m pip` rather than bare `pip` to ensure packages install into the active venv,
> not a system or Conda environment that may be on your PATH.

Then crawl and extract:

```powershell
# crawl bill index for Malaysia
python -m lib.sources.my.parliament_my.crawl --list-arkib-bills --arkib-csv-dir src/out/bills_csv

# crawl Hansard — Parliament 15 (2022–present)
python -m lib.sources.my.parliament_my.crawl --list-hansard --hansard-parliament 15 --hansard-csv-dir src/out/hansard_csv

# download + extract a sample batch of 3 hansard + 3 bill PDFs
python scripts/sample_crawl.py

# TLS bypass if your machine has certificate issues
python scripts/sample_crawl.py --insecure
```

## Browse the docs locally

```powershell
python -m mkdocs serve
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

> Use `python -m mkdocs` rather than bare `mkdocs` for the same reason as `python -m pip` above.

The hosted docs are at **https://q3dresearch.github.io/parawl/**

## Output format

Each extracted bill produces:

```
data/raw/my/parliament_my/pdf/2024/DR-6-2024.pdf
data/raw/my/parliament_my/pdf/2024/DR-6-2024.meta.json
data/derived/my/parliament_my/extracted/2024/DR-6-2024.md
```

## Adding a new source

Subclass `ParliamentSource` and implement the required methods.
See `src/lib/sources/my/parliament_my/` as the reference adapter.

## Part of the StateConscious project

`parawl` is the open data layer of [StateConscious](https://github.com/q3dresearch/stateconscious) —
a longitudinal study on Southeast Asian law and legislative transparency.

The application layer (search, RAG, analytics, frontend) lives in stateconscious.
`parawl` is the part anyone can run locally.

## License

MIT
