---
title: Analyze
description: Pipeline stage — LLM impact analysis of extracted bill text.
tags: [pipeline, analyze, llm]
status: planned
---

# Pipeline — Analyze

!!! warning "Planned"
    `lib.pipeline.analyze` is not yet implemented. This page documents the intended design.

**Module:** `src/lib/pipeline/analyze.py`
**Input:** `data/derived/<adapter>/extracted/<year>/<bill_id>.md`
**Output:** `data/derived/<adapter>/analyzed/<year>/<bill_id>/analysis.json`

## Requirements

An LLM API key is needed for this stage. See [Configuration](../reference/config.md#analyze-stage-planned) for setup.
The crawl, download, and extract stages do not require this.

## What it will do

Call an LLM once per bill to produce a structured impact analysis grounded in the extracted Markdown.
This turns raw legal text into something a non-lawyer can use.

## Output schema

```json
{
  "bill_id": "D.R.21/2024",
  "title": "Personal Data Protection (Amendment) Bill 2024",
  "purpose": "Strengthens obligations for data processors and introduces breach notification requirements.",
  "summary": "2-3 sentence plain-English summary of what changed and why it matters.",
  "key_clauses": [
    {"section": "4", "change": "...", "impact": "..."}
  ],
  "affected_parties": ["individuals", "data processors", "SMEs"],
  "industries": ["tech", "finance", "healthcare"],
  "tags": ["data-privacy", "compliance", "amendment"],
  "confidence": 0.9,
  "analyzed_at": "2026-05-20T00:00:00Z"
}
```

## Design principles

- Every claim is grounded in the extracted text — if the source doesn't support it, write `"unclear"`
- Suspect PDFs (`.suspect.md` marker) are never sent to the LLM
- One LLM call per bill; no parallel calls in MVP
- `--max N` caps how many bills are analyzed per run

## Planned CLI

```bash
PYTHONPATH=src python -m lib.pipeline.analyze --max 10
PYTHONPATH=src python -m lib.pipeline.analyze --force --max 5  # re-analyze existing
```
