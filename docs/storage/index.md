# Storage — Overview

StateConscious uses two complementary stores:

| Store | Purpose | Technology |
|-------|---------|-----------|
| **Metadata DB** | Structured fields — bill ID, title, dates, minister, tags, affected parties | SQLite (`stateconscious.db`) |
| **Vector store** | Semantic search — "show me bills about employee rights" | SQLite + `sqlite-vec` extension (or Chroma for larger scale) |

## Why two stores

SQLite handles structured queries well:
> "All bills passed in 2024 tagged `data-privacy`"

Vector search handles semantic queries:
> "Bills that could affect my logistics business"

The `analysis.json` produced by the pipeline feeds both: structured fields go into the metadata DB, embeddings of the `summary` + `key_clauses` text go into the vector store.

## Data flow

```
analysis.json
    ├──→  metadata DB  (bill_id, title, tags, parties, dates, industries)
    └──→  vector store  (embed: summary + key_clauses → float[] vector)
```

## Query patterns supported

| Query type | Store | Example |
|------------|-------|---------|
| Filter by tag | Metadata DB | `tags LIKE '%data-privacy%'` |
| Filter by year + country | Metadata DB | `year=2024 AND country='my'` |
| Filter by affected party | Metadata DB | `affected_parties CONTAINS 'SME'` |
| Semantic similarity | Vector store | "bills about employee termination" |
| Combined | Both (join) | Semantic search within a country/year scope |

See [Schema](schema.md) and [Vector Store](vector.md) for implementation detail.
