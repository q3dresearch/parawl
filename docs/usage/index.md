# Who Uses a Parsed Bill — and How

A bill is a dense legal instrument. The same 84 clauses mean different things depending on what question you are trying to answer. StateConscious processes each bill into structured outputs so every reader gets what they actually need — without reading the whole document.

## The core outputs

| Output | What it is | Where it lives |
|--------|-----------|----------------|
| **Bill digest** | 2–3 sentence plain-English summary of intent | `analysis.json → summary` |
| **Obligation index** | Every duty, prohibition, and right in one table | `analysis.json → obligations[]` |
| **Amendment diff** | Old text vs new text, clause by clause | `analysis.json → amendments[]` (planned) |
| **Affected parties** | Who is named, regulated, or empowered | `analysis.json → affected_parties[]` |
| **Acts referenced** | Which existing laws this bill touches | `analysis.json → acts_referenced[]` |

## Reader flows

Each role has a different entry point and a different "done" state.

| Role | Entry point | Done when |
|------|-------------|-----------|
| [Litigator](litigator.md) | Clause text + amendment diff | Knows which sections change existing duties |
| [Consumer](consumer.md) | Plain-language obligations | Knows what they must do / are protected from |
| [Business owner](business.md) | Compliance obligations + timeline | Knows what to change in their operations |
| [Judge](judge.md) | Legislative intent + defined terms | Can place a dispute in statutory context |
| [Politician](politician.md) | Affected parties + industries | Knows who lobbied whom and who gains/loses |
| [Journalist](journalist.md) | Bill digest + key clauses + quotes | Has a publishable summary in minutes |

## What the analysis.json schema provides for each role

```
litigator     →  key_clauses[], acts_referenced[], definitions_added
consumer      →  plain_obligations[], affected_parties[], tags[]
business      →  obligations[], industries[], affected_parties[], confidence
judge         →  purpose, definitions_added, acts_referenced[]
politician    →  affected_parties[], industries[], tags[], summary
journalist    →  summary, purpose, key_clauses[], affected_parties[]
```

These map to fields documented in [Storage → Schema](../storage/schema.md).
