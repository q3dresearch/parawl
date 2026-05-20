---
skill: sc-analyze
phase: 2
version: 0.1
pipeline_stage: analyze
prev_skill: sc-extract
---

# sc-analyze — Bill Impact Analyzer

Use an LLM to produce a structured impact analysis for each bill.

## Task outline

- For each `data/derived/<adapter>/extracted/<year>/<bill_id>/text.txt` (skip suspects), check if `data/derived/<adapter>/analyzed/<year>/<bill_id>/analysis.json` exists; skip if so
- Pair the extracted text with bill metadata (title, year, minister, reading dates) from the CSV
- Call the LLM with a prompt that asks for: purpose, plain-English summary, key clauses, affected parties, industry tags, confidence
- Write the structured response to `data/derived/parliament_my/analyzed/<sha256>/analysis.json`
- Respect `--max N` to cap LLM calls per run

## Output shape

```json
{
  "bill_id": "D.R.21/2024",
  "title": "...",
  "purpose": "one sentence",
  "summary": "2–3 sentences in plain English",
  "key_clauses": [{"section": "4", "change": "...", "impact": "..."}],
  "affected_parties": ["..."],
  "industries": ["..."],
  "tags": ["..."],
  "confidence": 0.0,
  "source_sha256": "...",
  "analyzed_at": "ISO-8601"
}
```

## Prompt discipline

- Ground every claim in the extracted text; instruct the model to write "unclear" rather than hallucinate
- Send segments (or truncated text if too long) rather than raw full text
- One LLM call per bill; no parallel calls in MVP

## Implementation target

`src/lib/pipeline/analyze.py` — callable as `python -m lib.pipeline.analyze`  
LLM client: `src/lib/llm/client.py`

## Key constraint

Never call the LLM if `analysis.json` already exists for that hash unless `--force` is passed. Token cost is real.
