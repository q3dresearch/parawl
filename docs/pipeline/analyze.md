# Pipeline — Analyze

**Module:** `src/lib/pipeline/analyze.py`  
**Input:** `data/derived/<adapter>/extracted/<year>/<bill_id>/text.txt` + bill metadata row  
**Output:** `data/derived/<adapter>/analyzed/<year>/<bill_id>/analysis.json`

## What it does

Calls an LLM once per bill to produce a structured impact analysis grounded in the extracted text. The output is the primary human-readable artifact — it's what gets indexed in the vector store and surfaced to end users.

## Output schema

```json
{
  "bill_id": "D.R.21/2024",
  "title": "Personal Data Protection (Amendment) Bill 2024",
  "purpose": "Strengthens obligations for data processors and introduces data breach notification requirements.",
  "summary": "2–3 sentence plain-English summary of what changed and why it matters.",
  "key_clauses": [
    {"section": "4", "change": "...", "impact": "..."}
  ],
  "affected_parties": ["individuals", "data processors", "SMEs"],
  "industries": ["tech", "finance", "healthcare"],
  "tags": ["data-privacy", "compliance", "amendment"],
  "confidence": 0.9,
  "source_sha256": "<sha256>",
  "analyzed_at": "2024-07-16T10:00:00Z"
}
```

## Prompt discipline

- The LLM is instructed to ground every claim in the extracted text
- If the source doesn't support a claim, the model writes `"unclear"` — not a guess
- Segments (structured sections from `segment.py`) are passed rather than raw full text, to stay within context limits
- One LLM call per bill — no parallel calls in MVP

## CLI

```bash
PYTHONPATH=src python -m lib.pipeline.analyze --source parliament_my --max 10
PYTHONPATH=src python -m lib.pipeline.analyze --source parliament_my --force --max 5
```

## Cost management

- `--max N` caps LLM calls per run
- Token counts are logged if the client exposes them
- Skipped bills (already have `analysis.json`) do not count against `--max`
- Suspect PDFs (marked with `suspect.txt`) are never sent to the LLM

## LLM provider

Configured in `.env` (see `.env.example`). The client wrapper lives at `src/lib/llm/client.py`.
