---
title: Contributing
description: How to add a new source adapter or contribute to parawl.
tags: [contributing, adapters, open-source]
---

# Contributing

## Adding a new source adapter

Each country/chamber is a self-contained adapter. Adding a new one does not require touching any existing code.

**1. Create the adapter folder:**

```
src/lib/sources/<country>/<adapter_id>/
  __init__.py
  seed_urls.txt     # one entry URL per line
  config.py         # SOURCE_ID, RESOURCE_KIND, any site-specific headers
  fetch.py          # HTTP fetch logic
  parse.py          # HTML / XML / PDF link extraction
  crawl.py          # CLI entrypoint
  README.md         # site quirks, known errors, format notes
```

Use `src/lib/sources/my/parliament_my/` as the reference implementation.

**2. Document it:**

Add a page under `docs/sources/<country>/<adapter_id>.md` covering:

- What the source covers and its URL
- The crawl strategy (with a Mermaid diagram if the flow is non-trivial)
- Any site-specific quirks or required config vars
- Known gaps or limitations

Add the page to the nav in `mkdocs.yml` under the appropriate country.

**3. Add tests:**

At minimum, add a fixture and a parse test so the adapter's core logic is covered without hitting the live site.

**4. Document any required config:**

If the adapter needs env vars (cookies, API keys), add them to `.env.example` and document them in [Configuration](config.md) under a per-adapter section.

---

## Fixing a parser or crawl bug

1. Add a failing test that reproduces the bug (fixture or synthetic input — no live network)
2. Fix the code
3. Confirm tests pass: `pytest -v`
4. Update the relevant docs page if the behaviour changed

---

## Reporting a broken source

If a government site has changed its format and the adapter stops working, open an issue on GitHub with:

- The adapter ID (`parliament_my`, etc.)
- What changed (screenshot or URL is helpful)
- When it stopped working (approximate date)
