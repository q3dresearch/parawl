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
| `my.parliament_my` | parlimen.gov.my — Dewan Rakyat bills | 1990–present |

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
python -m venv .venv && .venv/Scripts/activate  # Windows
pip install -r requirements.txt

# crawl bill index for Malaysia
python -m lib.sources.my.parliament_my.crawl

# extract text from downloaded PDFs
python -m lib.pipeline.extract
```

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
