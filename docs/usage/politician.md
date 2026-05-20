# Politician flow

## What you are trying to answer

- Which industries and constituencies are affected — who will call my office about this?
- Who gains power under this bill — the Minister, a regulator, private parties?
- Which existing laws are being weakened or strengthened?
- What is the political narrative, and where are the points of contention?
- Is there a sunset clause, a parliamentary oversight mechanism, or is this power indefinite?

## The problem with reading a raw bill

A bill's impact is almost never contained in the clauses that sound important. The real story is often in the definitions (which expand or contract scope), the ministerial discretion clauses (which allocate power), and the consequential amendments (which change existing Acts through the back door).

## How StateConscious helps

**Affected parties** (`affected_parties[]`) and **industries** (`industries[]`) are the political map. They tell you which sectors will feel the bill before any lobbying call comes in.

**Summary** (`summary`) is a 2–3 sentence plain-English brief — close enough to a speaking note that it can be adapted directly for a constituency communication.

**Key clauses** (`key_clauses[]`) surface clauses that shift power, create new offences, or remove safeguards. Look especially for:

- Clauses that grant the Minister "as the Minister may determine" powers
- Definitions so broad they swallow most of the industry
- Penalty escalation compared to the existing Act

**Tags** (`tags[]`) place the bill in a policy category: `surveillance`, `data-privacy`, `competition`, `housing`, `labour`. Use these to track legislative intent across a Parliament session.

## Example — Online Safety Bill 2024 political reading

```json
{
  "summary": "Creates a new regulator (Online Safety Commission) with powers to compel platforms to remove harmful content, issue standards, and impose heavy fines. Platforms with more than X users bear the greatest compliance burden. Individual users can face criminal liability for certain categories of content.",
  "affected_parties": ["network service provider", "content creator", "individual user", "children"],
  "industries": ["tech", "social-media", "telecom", "media"],
  "tags": ["online-safety", "censorship-risk", "platform-regulation", "ministerial-power"],
  "key_clauses": [
    {
      "section": "5",
      "change": "Establishes Online Safety Commission; members appointed by the Minister",
      "impact": "Executive controls the regulator — no independent appointments mechanism on the face of the bill"
    },
    {
      "section": "83",
      "change": "Minister may by order exempt any person from any provision of this Act",
      "impact": "Blanket exemption power; scope and accountability unclear"
    }
  ]
}
```

The political read: the bill creates a new powerful regulator with executive-controlled appointments and a ministerial blanket exemption — two pressure points for opposition debate regardless of the bill's stated intent.

## Red flags to look for

| Signal | What it may mean |
|--------|-----------------|
| "Minister may determine" appears frequently | Significant secondary legislation expected; Parliament's role is limited after royal assent |
| Definitions reference "as prescribed" | Operational detail pushed into regulations made without parliamentary vote |
| No sunset clause on emergency provisions | Powers that were sold as temporary become permanent |
| Affected parties include "any person" | Very broad scope — almost everyone is a regulated party |
| Acts referenced include constitutional statutes | May trigger constitutional challenge |
