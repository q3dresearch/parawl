---
title: Configuration
description: Environment variables for parawl, scoped by adapter and pipeline stage.
tags: [config, env, api-keys]
---

# Configuration

parawl reads secrets from a `.env` file in the repo root.
Copy `.env.example` to `.env` and fill in only the variables you need.

```bash
cp .env.example .env
```

Most pipeline stages work without any configuration.
The `crawl` and `extract` stages have no required env vars.

---

## Per-adapter configuration

Each adapter documents its own requirements. Below are the adapters currently implemented.

### `my.parliament_my` (parlimen.gov.my)

| Variable | Stage | Required | Notes |
|----------|-------|----------|-------|
| `PARLIMEN_COOKIE` | download | Yes, for PDFs | Session cookie — see below |

**Why this exists (and when it may go away):**
As of 2026, parlimen.gov.my requires an active browser session cookie to serve PDF files.
Without it, the site returns HTTP 200 with an HTML error page instead of the PDF.
This is a site-specific quirk, not a general pattern.
If the site removes the cookie requirement in a future update, this variable becomes unnecessary.

**How to get the cookie:**

1. Open [parlimen.gov.my](https://www.parlimen.gov.my) in your browser
2. Set the site language to **English** (top-right language selector)
3. Open DevTools → Network → click any request → Request Headers → copy the full `Cookie:` value
4. Add to `.env`: `PARLIMEN_COOKIE=<paste here>`

---

## Pipeline stage configuration

### Analyze stage *(planned)*

The analyze stage calls an LLM and requires an API key.
parawl routes LLM calls through [OpenRouter](https://openrouter.ai) so you can swap models without changing code.

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `OPENROUTER_API_KEY` | Yes | — | Get a key at [openrouter.ai](https://openrouter.ai) |
| `OPENROUTER_MODEL` | No | `anthropic/claude-sonnet-4-6` | Any model available on OpenRouter |

The crawl, download, and extract stages do not call any LLM and do not need this key.

---

## Live integration tests

Live tests hit real government websites and are skipped by default in `pytest`.

| Variable | Adapter | Notes |
|----------|---------|-------|
| `PARLIAMENT_LIVE_CSV_TEST=1` | `parliament_my` | Enables live crawl tests |
| `PARLIAMENT_LIVE_CSV_YEAR` | `parliament_my` | Year to crawl (e.g. `2024`) |
| `PARLIAMENT_LIVE_CSV_MAX_NODES` | `parliament_my` | Max nodes per run to limit time |

Run explicitly with:

```bash
pytest tests/test_parliament_live_year_csv_pdf.py -m live_parliament
```
