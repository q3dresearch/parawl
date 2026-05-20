# StateConscious — repository layout

This doc is the **system map** (how code and data relate). Product intent and gates live under `blueprint/`. **Human vs agent roles:** [`PROJECT_USE.md`](PROJECT_USE.md).

**Naming:** The **git repo folder** (`stateconscious/`) is the product name. The **Python package** under `src/` is `lib` (import `lib.*`) so we do not repeat `stateconscious/stateconscious/...` in paths.

## Top-level

| Path | Role |
|------|------|
| `src/lib/` | **Library** — DB, **`parser/`** (shared e.g. `seed_txt`), **`sources/`** (per-site adapters + **`discovery.py`**). |
| `src/lib/sources/<region>/<adapter>/` | **Adapter** — `fetch`/`parse`/`crawl`, **`seed_urls.txt`**, **`config.py`**, optional **`README.md`**. |
| `src/config/` | **Optional** — secrets / env templates (not required for URL lists). |
| `mds/agents/` | Agent briefs: **`crawlerAgent.md`**, **`sitesCrawl.md`**, … |
| `mds/skills/` | Reserved for **npx / packaged skills**. |
| `mds/human/` | **Human-only** — diary; agents do not author here. |
| `adhoc/todo/` | Human-only **async prompts**. **`adhoc/done/`** — archive. **`adhoc/agentHumanChat/`** — agent questions to human; **`resolved/`** for closed lessons. |
| `cron/lib/` | Small helpers (e.g. adhoc archive); see **`mds/agents/cronAgent.md`**. |
| `scripts/` | **General** human tools: **`init_db.py`**, **`inspect_crawl.py`**, **`view_parsed.py`**. Site crawls: **`python -m lib.sources…`**. |
| `sql/migrations/` | Versioned SQLite DDL (`001_init.sql`, …). |
| `tests/` | Pytest + fixtures. |
| `data/raw/` | `runs.jsonl` + `html/<sha256>/…` + `pdf/<sha256>/…`. |
| `data/derived/` | `parsed/<sha256>/…`. |
| `stateconscious.db` | SQLite (gitignored) — `source_library`, `crawl_history`. |

**Legacy:** `data/snapshots/<adapter>/` may still exist locally.

## `paths.py` and `artifacts.py`

- **`lib/paths.py`** — **`repo_root()`** so `data/` and the DB path resolve consistently from any module.
- **`lib/artifacts.py`** — **Content-addressed** paths under `data/raw` / `data/derived` (shared by all adapters).

## Import convention

With `PYTHONPATH=src` (or `pytest.ini` `pythonpath = . src` for `cron.*` tests):

```text
import lib
from lib.sources.my.parliament_my import fetch
from lib.sources.my.parliament_my import parse  # HTML + billindex / dhtmlx PDF helpers
```

## Pipeline

After bill discovery (`src/lib/sources/…`), documents flow through four sequential stages under **`src/lib/pipeline/`**.

| Module | Input | Output | Artifact path |
|--------|-------|--------|---------------|
| `download.py` | Bill row with `pdf_url` (from CSV or DB) | Raw PDF + metadata | `data/raw/<adapter>/pdf/<year>/<bill_id>.pdf` + `.meta.json` |
| `extract.py` | Raw PDF path | Structured Markdown | `data/derived/<adapter>/extracted/<year>/<bill_id>/text.md` |
| `segment.py` | Extracted text | Clauses / section list | `data/derived/<adapter>/segments/<year>/<bill_id>/segments.json` |
| `analyze.py` | Segments + bill metadata | Semantic units + impact narrative | `data/derived/<adapter>/analyzed/<year>/<bill_id>/analysis.json` |

**Idempotency:** each stage checks whether its artifact already exists before running; `--force` overwrites.

**LLM:** configured via `.env` (see `.env.example`); client lives at `src/lib/llm/client.py`.

### analysis.json schema (target)

```json
{
  "bill_id": "D.R.21/2024",
  "title": "Personal Data Protection (Amendment) Bill 2024",
  "purpose": "one-sentence intent",
  "summary": "2–3 sentence plain-English summary",
  "key_clauses": [{"section": "4", "change": "…", "impact": "…"}],
  "affected_parties": ["individuals", "data processors", "SMEs"],
  "industries": ["tech", "finance", "healthcare"],
  "tags": ["data-privacy", "compliance", "amendment"],
  "confidence": 0.9,
  "sha256": "<sha256 stored in .meta.json, not in path>",
  "analyzed_at": "ISO-8601"
}
```

## Patterns

- **Site crawl logic** lives under **`lib/sources/…`**, not **`lib/pipeline/`**.
- **Pipeline logic** lives under **`lib/pipeline/`**; one module per stage.
- **Thin scripts / fat library** — `scripts/*.py` stay small; logic lives under `lib/`.
- **SQL migrations** — schema in `sql/migrations/`; `init_schema()` applies a file.
- **Docs vs blueprint** — `docs/` = how the system runs; `blueprint/` = what we agreed to build.

## Operator playbook

See **`OPERATIONS.md`**.
