# Pipeline — Overview

parawl handles ingestion: discover → download → extract. Each stage is idempotent — it checks whether its output artifact already exists before doing work, making re-runs safe.

Downstream processing (translation, analysis, chunking, longitudinal study) lives in [stateconscious](https://github.com/q3dresearch/stateconscious), which consumes parawl's extracted Markdown as its input.

## Stages

```mermaid
graph LR
  A[bills / hansard CSV<br/>pdf_url] --> B[Download<br/>raw PDF bytes]
  B --> C[Extract<br/>Markdown text]
  C --> D[stateconscious<br/>translate · analyze · serve]
  style D stroke-dasharray: 5 5
```

| Stage | Input | Output | Module |
|-------|-------|--------|--------|
| [Download](download.md) | `pdf_url` from crawl CSV | `data/raw/<adapter>/pdf/<year>/<id>.pdf` + `.meta.json` | `lib.pipeline.download` |
| [Extract](extract.md) | Raw PDF path | `data/derived/<adapter>/extracted/<year>/<id>.md` | `lib.pipeline.extract` |

## Idempotency

The document's natural key (`<year>/<id>`) determines the artifact path. Each stage checks whether its output file exists before running — if it does, the document is skipped. SHA-256 is stored in `.meta.json` alongside the PDF for change-detection.

Pass `--force` to any stage to overwrite existing artifacts.

## Running the pipeline

```bash
# Download PDFs
python -m lib.pipeline.download --source parliament_my --max 50

# Extract text from downloaded PDFs
python -m lib.pipeline.extract

# Or run both in one script (sample: 3 hansard + 3 bills)
python scripts/sample_crawl.py
```

## Failure handling

Each stage catches per-item failures and continues. Suspect PDFs (< 100 chars extracted — likely a scanned image) are written to a `.suspect.md` file and flagged for human review rather than silently dropped.
