---
title: Extract
description: Pipeline stage — convert downloaded PDFs to Markdown using pymupdf4llm.
tags: [pipeline, extract, pdf, markdown]
status: implemented
---

# Pipeline — Extract

!!! success "Implemented"
    `lib.pipeline.extract` is working. Run it after downloading PDFs.

**Module:** `src/lib/pipeline/extract.py`
**Input:** `data/raw/<adapter>/pdf/<year>/<bill_id>.pdf`
**Output:** `data/derived/<adapter>/extracted/<year>/<bill_id>.md`

## What it does

Converts downloaded bill PDFs to Markdown. No LLM involved — extraction is deterministic and fast.

## Library selection

| Library | Speed | Output | Role |
|---------|-------|--------|------|
| `pymupdf4llm` | ~0.1s/page | Markdown | **Primary** — preserves headings and clause structure |
| `pypdf` | ~3.5s/page | Plain text | **Fallback** — pure Python, no C dependency |

`pymupdf4llm` is the clear choice: same quality, fastest speed, and Markdown output means downstream LLM stages receive structured text (headings, numbered clauses, indented sub-clauses) rather than a flat string.

## Suspect PDFs

If extraction yields fewer than 100 characters, the bill is likely a scanned image PDF with no selectable text. A `suspect.md` marker is written alongside the output and the analyze stage will skip it.

## Malaysian bill layout

Bills are typically bilingual (Bahasa Malaysia + English). Both languages are preserved in the extracted Markdown — the English text usually appears in the right column or second half of the document.

## CLI

```bash
PYTHONPATH=src python -m lib.pipeline.extract
PYTHONPATH=src python -m lib.pipeline.extract --force   # re-extract existing
```

## Output files

```
data/derived/my/parliament_my/extracted/2024/
  DR-21-2024.md          # extracted Markdown
  DR-21-2024.suspect.md  # present only if extraction yield < 100 chars
```
