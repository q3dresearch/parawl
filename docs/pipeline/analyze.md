---
title: Analyze (stateconscious)
description: LLM analysis lives in stateconscious, not parawl.
tags: [pipeline, analyze, stateconscious]
---

# Analyze — Handoff to stateconscious

parawl's pipeline ends at **Extract**. The extracted Markdown files are the output this library produces.

LLM-based analysis (translation, impact summarisation, chunking, longitudinal study) is handled by [stateconscious](https://github.com/q3dresearch/stateconscious), which consumes parawl as an upstream dependency.

## What stateconscious does with parawl output

```
parawl output                        stateconscious stages
─────────────────────                ──────────────────────────────────────
data/derived/<adapter>/              → Translate   (OpenRouter / Gemini)
  extracted/<year>/<id>.md           → Analyze     (LLM impact analysis)
                                     → Chunk       (RAG-ready segments)
                                     → Longitudinal (cross-bill study)
                                     → Serve       (search, frontend, API)
```

See the [stateconscious docs](https://github.com/q3dresearch/stateconscious) for the application layer.
