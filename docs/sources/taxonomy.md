# Source Taxonomy — Country / State / Category

StateConscious organises all legal sources using a three-level hierarchy. This taxonomy determines how adapters are named, where artifacts are stored, and how query results are scoped.

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
| `gb` | United Kingdom |
| `us` | United States |

### State / territory / level

For federal systems like Malaysia, this distinguishes between national legislation and state enactments.

| Value | Meaning |
|-------|---------|
| `federal` | National / federal level |
| `selangor` | Selangor state |
| `sabah` | Sabah state |
| `sarawak` | Sarawak state |
| *(state name)* | Any other state or territory |

For centralised systems (Singapore, UK), this is typically `national`.

### Category

The type of legal document.

| Category | Description |
|----------|-------------|
| `bills` | Proposed legislation before Parliament |
| `acts` | Passed and gazetted primary legislation |
| `gazette` | Official Gazette (proclamations, subsidiary legislation notices) |
| `subsidiary_legislation` | Regulations, rules, orders made under an Act |
| `hansard` | Parliamentary debates / Hansard records |
| `judgments` | Court judgments (future scope) |

## How this maps to adapters

An adapter ID is typically `<category>_<country>` or a descriptive slug:

```
parliament_my           →  country=my, state=federal, category=bills
gazette_my_federal      →  country=my, state=federal, category=gazette
```

Artifact paths follow the same structure:

```
data/raw/<adapter_id>/pdf/<sha256>/
data/derived/<adapter_id>/extracted/<sha256>/
data/derived/<adapter_id>/analyzed/<sha256>/
```

## Query scope

The taxonomy enables scoped queries:

- All bills affecting `my/federal` in 2024
- All gazette notices under `my/selangor` in the last 90 days
- All employment-related `acts` across `my/federal` and `my/sabah`

These queries work against the `analyzed` artifacts and the SQLite metadata store.
