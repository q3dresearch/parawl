# Litigator flow

## What you are trying to answer

- Does this bill change the standard of care my client is held to?
- Which section of which Act is being substituted or repealed?
- If the bill passed today, would my current case argument still hold?
- What is the commencement date — is the new duty already in force?

## The problem with reading a raw bill

Bills are written as surgical edits to existing Acts. Clause 12 might read:

> *In section 7 of the Personal Data Protection Act 2010 [Act 709], for paragraph (a) substitute — …*

Without the current text of Act 709, §7(a), the clause is meaningless. You need both the bill and the existing statute open side by side.

## How StateConscious helps

**Amendment diff** surfaces the before/after for every substituted, deleted, or inserted section. You read one document instead of two.

**Acts referenced** (`acts_referenced[]`) lists every Act the bill touches, with the specific sections cited. You know immediately which existing instruments are in play before opening a single external source.

**Definitions added** (`definitions_added`) flags every new or redefined term. A definition change upstream rewrites every downstream duty — this catches it explicitly.

**Key clauses** (`key_clauses[]`) call out clauses that create, extend, or remove obligations rather than administrative boilerplate (short titles, repeal of spent provisions, etc.).

## Example — Online Safety Bill 2024 (DR-59-2024)

```json
{
  "acts_referenced": ["Communications and Multimedia Act 1998 [Act 588]"],
  "key_clauses": [
    {
      "section": "22",
      "change": "Duty on network service provider to act on harmful content notice within 24 hours",
      "impact": "Potential liability exposure for platforms that fail to remove content after notice"
    },
    {
      "section": "61",
      "change": "New offence: publishing content that causes fear of violence",
      "impact": "Extends criminal exposure to individual users, not just platforms"
    }
  ],
  "definitions_added": {
    "online safety harm": "defined for the first time — scope determines which clauses bite"
  }
}
```

A litigator acting for a platform operator reads `key_clauses[section=22]` and `definitions_added["online safety harm"]` before anything else. The 84-clause bill collapses to two entry points.

## Gaps to know

- StateConscious does not yet fetch the *existing* Act text; the diff is bill-only until we integrate the Acts of Parliament corpus.
- `confidence` score reflects extraction quality — low confidence means clause text may be incomplete.
- Commencement dates are often deferred to ministerial gazette. Flag any clause that says "appointed date" or "as the Minister may determine."
