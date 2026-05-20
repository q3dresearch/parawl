---
title: Pending Work
description: Internal reminders for work in progress across machines.
tags: [internal, wip, pending]
---

# Pending Work

Internal notes on work that is in progress but not yet merged or tested end-to-end.

---

## Hansard crawler — awaiting push from other machine

**Status:** In progress on a separate machine. Code not yet pushed to `main`.

**What it covers:**
- `hansard-dewan-rakyat.html?uweb=dr` — live hansard index
- Likely same dhtmlx XML tree format as bills, but unconfirmed until the code is reviewed

**Blocked on:**
- Other machine must push the hansard adapter code to `main`
- Pull here, review the parser, confirm the format
- Then run end-to-end: crawl → CSV → download 3 hansard PDFs → extract → read

**Do not document hansard as working until this is verified locally.**

---

## Bills + hansard end-to-end test — not yet run in parawl

**Status:** Blocked on hansard push above.

**Plan once unblocked:**
1. Pull latest `main`
2. Run bills crawl → confirm CSVs land in `src/out/bills_csv/`
3. Download 3 bill PDFs → confirm `.pdf` + `.meta.json` in `data/raw/`
4. Run extract → confirm `.md` in `data/derived/`
5. Read the output — confirm content is usable
6. Repeat steps 2–5 for 3 hansard PDFs
7. Only after all 6 PDFs are verified: update pipeline docs to reflect actual behaviour and commit

**parawl venv is ready** (dependencies installed 2026-05-20). Run with:

```powershell
cd C:\Users\david\Desktop\q3d\parawl
.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "$PWD\src"
```

---

## Docs pages not yet verified against actual output

These pages were written based on design intent, not observed runs.
Review and update once the end-to-end test above is complete:

- [Download](../pipeline/download.md) — module not yet implemented
- [Extract](../pipeline/extract.md) — output filename (`.md` vs `.txt`) unverified in parawl
- [Analyze](../pipeline/analyze.md) — module not yet implemented
- [Malaysia — Parliament](../sources/my/parliament.md) — crawl strategy diagram needs live verification
