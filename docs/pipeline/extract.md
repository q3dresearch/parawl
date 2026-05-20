# Pipeline — Extract

**Module:** `src/lib/pipeline/extract.py`  
**Input:** `data/raw/<adapter>/pdf/<year>/<bill_id>.pdf`  
**Output:** `data/derived/<adapter>/extracted/<year>/<bill_id>/text.md`

## What it does

Extracts structured Markdown from downloaded bill PDFs. No LLM is used at this stage — extraction is deterministic.

## Library selection

| Library | Speed | Quality | Role |
|---------|-------|---------|------|
| `pymupdf4llm` | 0.1s | 96% | **Primary** — outputs Markdown with headings and clause structure intact |
| `pypdf` | 3.5s | 96% | **Fallback** — pure Python, no C dependencies, works in restricted environments |

`pymupdf4llm` is the clear choice: same quality as competitors, fastest speed, and Markdown output means the LLM receives structured text (section headings, numbered clauses, sub-clauses indented) rather than a flat string.

If the primary extractor yields < 100 characters, the bill is likely a scanned image PDF. A `suspect.md` marker is written and the LLM stage skips this bill.

## Malaysian bill layout notes

Bills are typically bilingual (Bahasa Malaysia + English). The English text usually appears in the right column or second half of the document. Both languages are preserved in the extracted text — the LLM is instructed to prefer the English sections for analysis but may reference BM for confirmation.

## CLI

```bash
PYTHONPATH=src python -m lib.pipeline.extract --source parliament_my
PYTHONPATH=src python -m lib.pipeline.extract --source parliament_my --force  # re-extract all
```

## Output files

| File | Meaning |
|------|---------|
| `text.txt` | Extracted plain text |
| `suspect.txt` | Present only if extraction yield was suspiciously low |
