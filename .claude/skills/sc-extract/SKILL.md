---
skill: sc-extract
phase: 1
version: 0.1
pipeline_stage: extract
prev_skill: sc-download
next_skill: sc-analyze
---

# sc-extract — Bill Text Extractor

Extract plain text from downloaded bill PDFs.

## Task outline

- For each `data/raw/<adapter>/pdf/<year>/<bill_id>.pdf`, check if `data/derived/<adapter>/extracted/<year>/<bill_id>/text.txt` already exists; skip if so
- Extract text from the PDF using `pymupdf4llm` (primary — outputs Markdown, preserves headings and clause structure) or `pypdf` (fallback — pure Python, no C deps)
- Write extracted Markdown to `data/derived/<adapter>/extracted/<year>/<bill_id>/text.md`
- If extraction yields < 100 chars, write a `suspect.txt` marker with a note (likely scanned/image PDF); do not attempt LLM on this bill

## Edge cases to handle

- Scanned / image PDFs (low text yield)
- Password-protected PDFs
- Corrupt or truncated PDFs
- Malay + English bilingual layout (extract both; don't strip either)

## Implementation target

`src/lib/pipeline/extract.py` — callable as `python -m lib.pipeline.extract`

## Key constraint

Extraction is deterministic. Given the same PDF bytes, the output must be the same text. No LLM at this stage.
