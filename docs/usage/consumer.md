# Consumer flow

## What you are trying to answer

- Does this new law give me more rights, or take some away?
- What can a company do with my data / content / phone number under this law?
- If I am harmed, does this bill give me a way to complain or sue?
- Is there anything I need to do by a certain date?

## The problem with reading a raw bill

Bills are not written for the public. They are addressed to institutions — "a licensee shall", "the provider must", "the Commission may". A consumer reads these and cannot easily invert the duty to find the corresponding right.

## How StateConscious helps

**Plain obligations** (`plain_obligations[]`) rewrites each duty in the second person from the consumer's perspective:

> *"Any person who runs an online platform must remove content you flag as harmful within 24 hours of your report."*

Instead of:

> *"A network service provider shall, upon receipt of a harmful content notice, take down or disable access to the harmful content within twenty-four hours."*

**Affected parties** (`affected_parties[]`) tells you whether "the public", "users", "individuals", or "children" are in scope. If you are not listed, the bill may not apply to you directly — or it may apply to parties who hold your data.

**Tags** (`tags[]`) give a plain-language topic list: `data-privacy`, `online-safety`, `financial-services`, `housing`. Use these to filter bills relevant to your life without reading every digest.

## Example — personal data scenario

A consumer reading the Personal Data Protection (Amendment) Bill asks: *"What can I do if a company leaks my data?"*

```json
{
  "plain_obligations": [
    "A company that holds your personal data must notify you within 72 hours of a data breach.",
    "You can request that a company delete your data; they must respond within 30 days.",
    "You can complain to the Personal Data Protection Commissioner if a company ignores your request."
  ],
  "affected_parties": ["individuals", "data subjects"],
  "tags": ["data-privacy", "consumer-rights", "amendment"]
}
```

The consumer gets three actionable sentences. They do not need to read the bill.

## Gaps to know

- `plain_obligations` is LLM-generated and should be verified against the original clause for any decision with real stakes.
- Commencement dates matter: rights granted by a bill only exist after the Act comes into force.
- Some bills affect consumers only indirectly (e.g. a bill regulating banks). StateConscious flags `indirect_impact: true` when the regulated entity is not the consumer but their service provider.
