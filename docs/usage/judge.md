# Judge flow

## What a judge needs from a bill

Judges do not read bills to know what to do — they read them to understand legislative intent when a statute is ambiguous, contested, or silent. The question is always: *what did Parliament mean?*

Key questions:

- What mischief was this Act designed to remedy? (the Mischief Rule)
- How is a disputed term defined in this legislation — or left undefined?
- Which existing Act does this amend, and what was the old position?
- Was there parliamentary debate that clarifies the scope of a particular clause?

## The problem with reading a raw bill

A bill's long title and preamble carry interpretive weight, but they are easy to miss inside a long document. Definitions sections are scattered. The exact words Parliament chose for an obligation matter — "shall" vs "may", "or" vs "and", "including but not limited to".

## How StateConscious helps

**Purpose** (`purpose`) is a single sentence extracted from the bill's long title and explanatory statement. It captures the stated legislative intent — the closest thing to a Mischief Rule summary without reading Hansard.

**Definitions added** (`definitions_added`) maps every new or substituted definition. When a term is disputed in litigation, checking whether Parliament explicitly defined it is the first step. If it is absent here, it was left to judicial construction.

**Acts referenced** (`acts_referenced[]`) maps the bill's relationship to existing statutes. An amendment bill's key question is always: what was the old provision, and what is the new one? This field tells you which Acts were touched and at which sections.

**Key clauses** (`key_clauses[]`) surfaces clauses with interpretive significance — new offences, extended liability, delegated power to the Minister — rather than purely administrative provisions.

## Example — statutory construction scenario

A judge hearing a case under the Communications and Multimedia Act 1998 needs to construe "online safety harm" in the context of the Online Safety Bill 2024.

```json
{
  "purpose": "To establish a framework for online safety, create duties on network service providers, and regulate harmful online content.",
  "definitions_added": {
    "online safety harm": "content that causes or is likely to cause physical, psychological, financial, or reputational harm to a person",
    "harmful content notice": "a notice submitted by a user or regulator alleging that specific content constitutes online safety harm"
  },
  "acts_referenced": [
    {"act": "Communications and Multimedia Act 1998 [Act 588]", "sections": ["3", "189", "233"]}
  ]
}
```

The definition of "online safety harm" is broad and forward-looking — Parliament chose "likely to cause" rather than "causes". This signals a precautionary legislative intent that affects how the duty to act is construed.

## What StateConscious does not replace

- Hansard (parliamentary debate transcripts) — the most direct evidence of legislative intent, not yet in the pipeline
- Federal Court interpretations of sister legislation
- The existing unamended Act text — StateConscious shows the bill's proposed changes, not the consolidated statute

These are documented as planned sources in the [pipeline roadmap](../pipeline/index.md).
