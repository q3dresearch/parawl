# Journalist flow

## What you are trying to answer

- What does this bill actually do, in one sentence I can put in a headline?
- Who wins and who loses?
- What is the strongest quote-worthy clause?
- What is controversial about this, and where will the pushback come from?
- Is there a human story here — a real person this law will affect?

## The problem with reading a raw bill

A 40-page bill takes an hour to read carefully. On a deadline, a journalist needs the story in five minutes. The risk is missing the significant clause buried on page 31, or leading with the bill title when the real news is a ministerial exemption power on page 28.

## How StateConscious helps

**Summary** (`summary`) is the first paragraph of your story — 2–3 sentences that explain what the bill does in plain English. Verify it, then use it.

**Purpose** (`purpose`) is the government's stated intent. Compare it against the `key_clauses[]` to find the gap between what the government says the bill does and what it actually does.

**Affected parties** (`affected_parties[]`) are your sources and your subjects. The people named in this field are the people your editors want you to call.

**Key clauses** (`key_clauses[]`) with `impact` fields surface the most newsworthy provisions without requiring a legal background to identify them.

**Tags** (`tags[]`) place the bill in a story context instantly: `data-privacy`, `press-freedom`, `platform-regulation`, `ministerial-power`.

## Example — newsroom workflow

Journalist receives a tip: "There's something big in the Online Safety Bill, check clause 83."

With StateConscious:

```json
{
  "summary": "Parliament is considering a bill that would require social media platforms to remove flagged content within 24 hours and creates a new government-appointed Online Safety Commission to police online speech.",
  "purpose": "To make the internet safer for Malaysians, especially children.",
  "key_clauses": [
    {
      "section": "61",
      "change": "New criminal offence: publishing content causing fear of violence",
      "impact": "Individual users — not just platforms — face criminal liability; maximum fine RM500,000 or 10 years imprisonment"
    },
    {
      "section": "83",
      "change": "Minister may exempt any person from any provision of this Act",
      "impact": "Government retains power to exempt politically connected entities from the law's reach"
    }
  ],
  "affected_parties": ["individual user", "network service provider", "children", "content creator"],
  "tags": ["online-safety", "press-freedom", "platform-regulation", "ministerial-power"]
}
```

The story writes itself: the stated purpose is child safety; clause 83 gives the government unchecked exemption power; clause 61 exposes ordinary users, not just corporations, to criminal liability.

Headline option A: *"New online safety law could jail Malaysians for speech that 'causes fear' — but government can exempt anyone it chooses"*

Headline option B: *"Online Safety Bill: what it actually does vs what the Minister says it does"*

## Story patterns that tags reliably surface

| Tag | Story angle |
|-----|------------|
| `ministerial-power` | Executive overreach / checks and balances |
| `data-privacy` | What companies can do with your data |
| `press-freedom` | Chilling effect on reporting |
| `platform-regulation` | Tech industry response and lobbying |
| `children` | Child protection frame — high public interest |
| `amendment` | What changed from the previous version of the law |

## Verification note

StateConscious outputs are AI-generated and should be verified against the original bill text before publication. The `confidence` score signals extraction quality — treat low-confidence outputs as leads, not facts. Clause numbers and penalty figures must always be cross-checked against the tabled bill or the Gazette.
