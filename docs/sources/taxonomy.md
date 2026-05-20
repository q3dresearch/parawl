---
title: Crawl Strategy
description: How parawl classifies sources by country, state, and document category.
tags: [sources, taxonomy, adapters]
---

# Source Taxonomy

parawl organises all legal sources using a three-level hierarchy. This taxonomy determines how adapters are named and where artifacts are stored on disk.

## Hierarchy

```
country
  └── state / territory / level
        └── category
```

### Country

ISO 3166-1 alpha-2 code, lower-cased.

| Code | Country |
|------|---------|
| `my` | Malaysia |
| `sg` | Singapore |
| `th` | Thailand |
| `id` | Indonesia |

### State / territory / level

For federal systems like Malaysia, this distinguishes national legislation from state enactments.

| Value | Meaning |
|-------|---------|
| `federal` | National / federal level |
| `selangor` | Selangor state |
| `sabah` | Sabah state |
| `sarawak` | Sarawak state |

For centralised systems (Singapore), this is typically `national`.

### Category

The type of legal document.

| Category | Description |
|----------|-------------|
| `bills` | Proposed legislation before Parliament |
| `acts` | Passed and gazetted primary legislation |
| `gazette` | Official Gazette notices |
| `subsidiary_legislation` | Regulations, rules, orders made under an Act |
| `hansard` | Parliamentary debates and Hansard records |

## How this maps to adapters and artifact paths

An adapter ID is a descriptive slug, typically `<category>_<country>`:

```
parliament_my      →  country=my, state=federal, category=bills+hansard
```

Artifact paths follow the same structure:

```
data/raw/my/parliament_my/pdf/<year>/<bill_id>.pdf
data/derived/my/parliament_my/extracted/<year>/<bill_id>.md
```

## Adding a country

Create a folder under `src/lib/sources/<country>/` and add your first adapter inside it.
The `<country>` code must match an ISO 3166-1 alpha-2 code. See [Architecture](../architecture/index.md) for the full adapter structure.
