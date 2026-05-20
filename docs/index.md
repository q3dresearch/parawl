# StateConscious

**A diff engine for public policy.**

StateConscious tracks how laws change over time, extracts structured meaning from bill text, and maintains a queryable record of who is affected and how.

## The problem

Laws change quietly. PDFs are silently updated. Gazette notices are published without fanfare. The people most affected — employees, SME owners, property buyers — find out months or years later, usually through a penalty or a lawyer's letter.

The elite class has in-house counsel and retainers who monitor this. Everyone else doesn't.

## What StateConscious does

1. **Ingests** public legal sources on a schedule (parliament bills, gazette, subsidiary legislation)
2. **Detects changes** — new content, revised PDFs, new readings — using content-addressed snapshots
3. **Extracts meaning** — purpose, key clauses, affected parties, industry tags — via LLM analysis
4. **Stores durably** — structured metadata in SQLite, full text in a vector store for semantic queries
5. **Exposes** — a queryable record: "what changed in employment law in 2024?" or "which bills affect data processors?"

## What it is not

- Not a legal advice service
- Not a full legislative database (no court rulings, no full consolidated Acts in scope for MVP)
- Not a real-time alerting system

## Design principles

- **Snapshot, don't overwrite.** Every ingestion is immutable; hash-addressed storage means you can always replay history.
- **Extraction is a pipeline, not a chat.** LLM calls produce structured artifacts on disk; not ephemeral context.
- **One source first.** MVP proves the pipeline on Malaysian Parliament bills (Dewan Rakyat) before expanding.
- **Separation of concerns.** Crawling, extraction, and querying are distinct stages with their own modules.

## Current status

| Component | Status |
|-----------|--------|
| Bill index crawler (MY Parliament) | ✅ working — 1,000+ bills, 1990–present |
| PDF download | 🔧 in design |
| Text extraction | 🔧 in design |
| LLM analysis | 🔧 in design |
| SQLite metadata store | ✅ schema exists |
| Vector store | 📋 planned |
