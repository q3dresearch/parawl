# StateConscious — operations playbook

Operator-facing doc: **how to run and extend the system**. **Who may edit what:** **`PROJECT_USE.md`**. Product scope and gates: **`blueprint/`**. Repo map: **`ARCHITECTURE.md`**.

## Read order (new session)

1. `docs/PROJECT_USE.md` — human vs agent, adhoc flow, cron failure expectations.
2. `docs/ARCHITECTURE.md` — where code and data live.
3. `mds/agents/crawlerAgent.md` — crawl policy (format-agnostic, budgets, DB).
4. Adapter **`seed_urls.txt`** under **`src/lib/sources/<region>/<adapter>/`** — **URL list** (one per line; optional `URL<TAB>label`). **`mds/agents/sitesCrawl.md`**. Reconcile with SQLite **`source_library`** via **`python scripts/init_db.py`**.
5. `blueprint/00-game-rules.md` — if using the neldivad harness.
6. **`adhoc/todo/`** — human async prompts; resolve per **`PROJECT_USE.md`** (then archive under **`adhoc/done/`** yourself).

## Commands (venv active, repo root)

| Goal | Command |
|------|---------|
| Install | `pip install -r requirements.txt` |
| Dev tests | `pip install -r requirements-dev.txt` && `pytest` |
| PYTHONPATH | `export PYTHONPATH="$PWD/src"` (Unix) or `$env:PYTHONPATH="$PWD\src"` (PowerShell) |
| Init DB | `python scripts/init_db.py` |
| Parliament arkib (dhtmlx bill rows → JSON) | `PYTHONPATH=src python -m lib.sources.my.parliament_my.crawl --list-arkib-bills` |
| Parliament arkib + CSV per year | add `--arkib-csv-dir <DIR>`; optional `--arkib-resolve-pdfs` (parallel probes by default; tune with `--arkib-resolve-workers N`, or `1` for sequential) |
| Parliament PDF URLs (per seed) | `PYTHONPATH=src python -m lib.sources.my.parliament_my.crawl --list-pdfs` |
| TLS dev bypass | add `--insecure` to either mode above |
| Inspect DB audit rows | `python scripts/inspect_crawl.py` (or `--json`) |
| View parsed JSON | `python scripts/view_parsed.py data/derived/parliament_my/parsed/<hash>/ --format md` |

## Pipeline commands (venv active, PYTHONPATH=src)

These run **after** the bill index has been crawled and CSVs are in `src/out/bills_csv/`.

| Goal | Command |
|------|---------|
| Download PDFs — dry run | `PYTHONPATH=src python -m lib.pipeline.download --source parliament_my --dry-run` |
| Download PDFs — capped at N | `PYTHONPATH=src python -m lib.pipeline.download --source parliament_my --max 20` |
| Extract text from downloaded PDFs | `PYTHONPATH=src python -m lib.pipeline.extract --source parliament_my` |
| Analyze bills with LLM | `PYTHONPATH=src python -m lib.pipeline.analyze --source parliament_my --max 10` |
| Full pipeline (download → extract → analyze) | `PYTHONPATH=src python -m lib.pipeline.run --source parliament_my --max 20` |

Pipeline outputs (all gitignored under `data/`):

| Stage | Path |
|-------|------|
| Raw PDF | `data/raw/<adapter>/pdf/<year>/<bill_id>.pdf` |
| PDF metadata | `data/raw/<adapter>/pdf/<year>/<bill_id>.meta.json` |
| Extracted text | `data/derived/<adapter>/extracted/<year>/<bill_id>/text.txt` |
| Segments | `data/derived/<adapter>/segments/<year>/<bill_id>/segments.json` |
| Analysis | `data/derived/<adapter>/analyzed/<year>/<bill_id>/analysis.json` |

**Force re-run** of a stage: append `--force` to overwrite existing artifacts.

---

## Crawl trace & audit (why `crawl_history` was empty)

**Parliament adapter CLI** (`lib.sources.my.parliament_my.crawl`) is **PDF-path only**: **`--list-arkib-bills`**, **`--list-pdfs`**, or **`--parse-html`**. It no longer runs a default “index fetch” or writes **`crawl_history`**; use **`scripts/init_db.py`** + other tooling if you need DB-backed polling.

**`crawl_history` / audit:** populated by workflows that call **`insert_crawl_history`** (not the parliament crawl entrypoint above). **`scripts/inspect_crawl.py`** still dumps **`source_library`** + latest history rows (use **`--json`** for scripts).

**End-to-end trace (generic):**

1. **`scripts/init_db.py`** — creates tables; seeds **`source_library`** from adapter **`seed_urls.txt`** (see **`lib.sources.discovery`**).
2. Adapter-specific jobs that persist fetches → **`crawl_history`** (when implemented for that adapter).
3. **`scripts/inspect_crawl.py`** — inspect rows.

**Verbose logging:** **`-v` / `--verbose`** prints DB path, row counts, and each **`crawl_history.id`** after insert (to stderr).

**Soft 200:** parlimen.gov.my may return **HTTP 200** with an HTML error shell (“An error has occurred…”). The parliament adapter sets **`outcome=error`**, **`error_message`** like **`soft_200 (error_page: …)`**, and **does not** write parsed JSON for that fetch. **`http_status`** stays **200** so you can distinguish TLS/403 from app-level failures.

**Quick SQL checks:**

```sql
SELECT COUNT(*) FROM crawl_history;
SELECT id, url, outcome, http_status, raw_html_relpath FROM crawl_history ORDER BY id DESC LIMIT 5;
```

## Artifact layout

- **`data/raw/<adapter>/runs.jsonl`** — append-only fetch log (JSON lines).
- **`data/raw/<adapter>/html/<sha256>/<filename>`** — one directory per **full** content hash.
- **`data/derived/<adapter>/parsed/<sha256>/<stem>.json`** — parse output for that snapshot.
- **`data/raw/<adapter>/pdf/<sha256>/<file>.pdf`** — raw PDF bytes when using **`--discover-pdfs`** (after indices, collects `.pdf` links; **`--follow-html N`** opens up to N HTML pages per index to find embedded PDFs such as acts under `/images/webuser/akta/`).

Cron should treat **hash** as idempotency: same URL + same hash → skip heavy work; new hash → new directory. Cap PDF volume with **`--pdf-max`** per run.

## Crawl budget (future)

`document_frontier` + per-run `N` downloads not implemented yet; `crawlerAgent.md` describes the target shape. Until then, index fetch is bounded by configured URL count.

## Agent / Cursor packaging

Source of truth: **`mds/agents/*.md`** (custom agent briefs). **`mds/skills/`** is for npx-installed skills. **`mds/human/`** is human-written only. Optional: Cursor rules — read `crawlerAgent.md` before editing `lib/sources/`. Avoid duplicating long policy in multiple files.
