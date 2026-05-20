# Business owner flow

## What you are trying to answer

- Does this bill create a new compliance obligation for my business?
- When do I need to comply, and what is the penalty for non-compliance?
- Which part of my operations is affected — product, HR, data handling, marketing?
- Do I need external legal review or can I self-serve?

## The problem with reading a raw bill

A 84-clause bill contains obligations, definitions, offences, regulations, transitional provisions, and consequential amendments. Most of it is irrelevant to any specific business. The cost is finding the 5 clauses that matter in a 40-page document — and being confident you have not missed one.

## How StateConscious helps

**Obligations index** (`obligations[]`) extracts every duty, prohibition, and deadline from the bill into a single flat list, tagged by the party obligated. Filter by your entity type and you have your compliance checklist.

**Industries** (`industries[]`) tags the bill by sector: `tech`, `finance`, `healthcare`, `telecom`, `manufacturing`. If your industry is not in the list, the bill likely does not touch your sector directly.

**Affected parties** (`affected_parties[]`) names the regulated categories explicitly: `network service provider`, `data processor`, `employer`, `licensed financial institution`. Compare against your business registration or license type.

**Confidence** score (`confidence`) tells you how reliably the extraction parsed the bill. Low confidence = send to a lawyer before acting.

## Example — compliance checklist for a social media platform

Bill: Online Safety Bill 2024 (DR-59-2024). Entity type: `network service provider`.

```json
{
  "obligations": [
    {
      "party": "network service provider",
      "duty": "Establish a mechanism for users to submit harmful content notices",
      "deadline": "within 6 months of commencement",
      "penalty": "fine not exceeding RM500,000"
    },
    {
      "party": "network service provider",
      "duty": "Remove or disable access to content flagged as harmful within 24 hours of notice",
      "deadline": "ongoing",
      "penalty": "fine not exceeding RM1,000,000 per day of non-compliance"
    },
    {
      "party": "network service provider",
      "duty": "Submit annual online safety report to the Commission",
      "deadline": "within 30 days of financial year end",
      "penalty": "fine not exceeding RM500,000"
    }
  ],
  "industries": ["tech", "social-media", "telecom"],
  "affected_parties": ["network service provider", "content aggregator"]
}
```

A product manager reads this list and opens three Jira tickets. They do not open the 84-clause bill.

## Triage heuristic

| Scenario | Action |
|----------|--------|
| Your industry is in `industries[]` AND your entity type is in `affected_parties[]` | Legal review required |
| Your industry is in `industries[]` but entity type is absent | Monitor — upstream party's obligations may cascade to you |
| Neither industry nor entity type matches | File as low-priority; re-check when gazette notice issued |
| `confidence < 0.7` | Do not self-serve; send to counsel |

## Gaps to know

- Deadlines may be relative to a gazette commencement date that is not yet published. The bill itself sets the framework; the Minister sets the date.
- Penalty figures in bills are maximums; sentencing guidelines and prosecutorial discretion affect actual exposure.
- Regulations made under a bill (subsidiary legislation) often contain the operational detail. StateConscious will flag when a clause delegates detail to future regulations.
