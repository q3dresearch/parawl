# Storage — SQLite Schema

`stateconscious.db` at the repo root (gitignored). Migrations in `sql/migrations/`.

## Existing tables

### `source_library`

Registry of all configured poll URLs — seeded from adapter `seed_urls.txt` via `python scripts/init_db.py`.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `url` | TEXT UNIQUE | Poll URL |
| `label` | TEXT | Human-readable label |
| `adapter_id` | TEXT | e.g. `parliament_my` |
| `resource_kind` | TEXT | `index`, `pdf`, `feed` |
| `active` | INTEGER | 1 = enabled for cron |
| `notes` | TEXT | Crawl notes from `config.py` |

### `crawl_history`

Audit trail for every fetch attempt across all stages.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `url` | TEXT | Fetched URL |
| `adapter_id` | TEXT | Source adapter |
| `sha256` | TEXT | Content hash (null on error) |
| `outcome` | TEXT | `success`, `skip`, `error`, `soft_200`, `timeout` |
| `http_status` | INTEGER | HTTP response code |
| `raw_pdf_relpath` | TEXT | Path to saved PDF (relative to repo root) |
| `error_message` | TEXT | Error detail (null on success) |
| `fetched_at` | TEXT | ISO-8601 timestamp |

## Planned tables (pipeline Phase 2)

### `bill_analysis`

Indexed version of `analysis.json` for structured queries.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `sha256` | TEXT UNIQUE | Links to `crawl_history` and artifact paths |
| `bill_id` | TEXT | e.g. `D.R.21/2024` |
| `country` | TEXT | ISO code |
| `state` | TEXT | `federal`, `selangor`, … |
| `category` | TEXT | `bills`, `acts`, … |
| `year` | INTEGER | |
| `title` | TEXT | |
| `purpose` | TEXT | One-sentence intent |
| `summary` | TEXT | 2–3 sentence plain English |
| `affected_parties` | TEXT | JSON array |
| `industries` | TEXT | JSON array |
| `tags` | TEXT | JSON array |
| `confidence` | REAL | 0.0–1.0 |
| `analyzed_at` | TEXT | ISO-8601 |

### `bill_clause`

Normalized key clauses for per-section queries.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | |
| `bill_sha256` | TEXT | FK → `bill_analysis.sha256` |
| `section` | TEXT | Section/clause reference |
| `change` | TEXT | What changed |
| `impact` | TEXT | Who is affected and how |
