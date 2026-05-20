# How humans and agents use this repo

**Single playbook.** Product shape lives in `blueprint/`; repo layout in `ARCHITECTURE.md`; shell commands in `OPERATIONS.md`. **This file** is the contract for **who may touch what**, **how adhoc work flows**, and **what we are building toward** for cron reliability and maintenance—without requiring you to verify a dozen other docs.

---

## 1. Human

### 1.1 Where humans write (only these)

| Location | Role |
|----------|------|
| **`adhoc/todo/`** | **Async prompts.** Functionally like a chat query, but **no instant reply**. The agent picks work up when cron (or a scheduled run) wakes up. One file per topic (e.g. `20260415-bills.md`). Inbox instructions live in **`adhoc/todo/README.md`** and are **not** treated as prompts (`list_todo_markdown()` skips `README.md` and `_*.md`). |
| **`mds/human/`** | **Diary.** Notes for yourself and for the agent’s **context**. The agent **reads** here to stay aligned with your intent; it does **not** edit this tree. |
| **`src/config/`** | **Optional** — secrets, env templates, or other non-URL settings. **Poll URLs** live in each adapter’s **`src/lib/sources/.../seed_urls.txt`**; the agent **may** change `src/config` when justified—you review in git. |

Humans do **not** need to duplicate this playbook into random READMEs; link here instead.

### 1.2 What “adhoc/todo” means

- Not a ticket system—just **markdown files** describing what should happen next (URLs to add, behavior to fix, priorities).
- **Resolved** when the work is reflected in **`src/lib`** (including adapter **`seed_urls.txt`** / **`config.py`** where relevant), **`stateconscious.db`** (via migrations / `init_db` as appropriate), optional **`src/config`**, and **tests** still pass.
- **Archiving:** the human moves completed items from **`adhoc/todo/`** to **`adhoc/done/`** (or deletes them) after review. Keep the repo so that **`adhoc/todo/`** is empty when there is nothing queued.

---

## 2. Agent

### 2.1 Wake-up loop

1. **Run or trigger cron** (whatever entrypoint you use: scripts, CI, local schedule).
2. **Read work items in `adhoc/todo/`** — use **`cron.lib.adhoc.list_todo_markdown()`** (or equivalent) so **`README.md`** and **`_*.md`** are skipped. Nothing in the repo auto-archives this folder; only explicit human moves or `archive_completed()`.
3. **Read `mds/human/`** (optional but recommended) for alignment with the human diary.
4. **Execute** using **deterministic** code in **`src/lib/`** and thin wrappers under **`cron/`** / **`scripts/`**—not one-off mystery cells.

### 2.2 Write permissions

| Allowed | Not allowed |
|---------|-------------|
| **`src/lib/`** — pipelines, adapters, DB access, logging helpers | **`adhoc/todo/`**, **`mds/human/`** — never create or edit |
| **`src/config/`** — when settings must match the implemented crawl/registry | |
| **SQLite** — repo default file is **`stateconscious.db`** (not always named `db.sqlite3`; same role) | |
| **`adhoc/agentHumanChat/`** — only as in §2.3 | |

### 2.3 When the agent needs the human (`adhoc/agentHumanChat/`)

If the agent **cannot finish**, needs **clarification**, or needs a **product decision**:

1. Create **`adhoc/agentHumanChat/YYYYMMDD.md`** (date = local or UTC, be consistent in your team).
2. **YAML frontmatter** at the top to signal topic and status, for example:

   ```yaml
   ---
   topic: parliament-tls-or-seed
   status: open
   ---
   ```

3. Use **thread sections** in the body:
   - **`## agent`** — question or blocker (append new `## agent` sections over time if needed).
   - **`## human`** — answers (human only).

4. **Resolution:** delete the file, or the human moves it to **`adhoc/agentHumanChat/resolved/`** if it contains a lesson worth keeping.

The agent does **not** use `adhoc/agentHumanChat` for routine “I finished the todo” messages—git + empty `adhoc/todo` is enough.

---

## 3. Ideal project (target)

- **Cron** runs a **short, deterministic** sequence of functions already living in **`src/lib/`** (and small **`cron/`** shims), with **`pytest`** green.
- **`adhoc/todo/`** is **empty** (no queued human prompts).
- **`adhoc/agentHumanChat/`** has **no `status: open`** threads (or no files, if everything is closed and archived).

This is an **aspiration**; crawlers will drift and break.

---

## 4. Cron will fail—plan for it

Web crawls **should be expected to fail** (TLS, 403, soft-200 error pages, DOM changes). Design goals:

| Mechanism | Intent |
|-----------|--------|
| **Structured logging** | Every fetch attempt should be auditable (today: `crawl_history` + `runs.jsonl`; extend as needed). |
| **Retries / backoff** | Policy: rerun failed jobs with caps (count + delay), not infinite loops. *Implementation can evolve in `src/lib`.* |
| **Idempotency** | Content-addressed paths (`data/raw/.../<hash>/`) so reruns do not corrupt “latest.” |
| **Alerting** | Human or agent notices repeated `outcome=error` or `soft_200` for the same seed URL. |

**Fallback** is “rerun with the same deterministic code after fixing config or site adapters,” not manual clicking unless automation is blocked.

---

## 5. Debugging, maintenance, and garbage collection (direction)

These are **design targets** so future work stays coherent—**not** a promise that every knob exists yet.

### 5.1 Job stats in SQLite

**Today:** `crawl_history` rows give per-URL outcome, HTTP status, timestamps, paths.**Toward:** optional tables or columns for **job id**, **run duration**, **retry count**, **cron task name**—so you can answer: “what failed last night and for how long?”

### 5.2 Iterative improvement

- **Tests first:** small fixtures (HTML/PDF snippets) + golden expectations; change **`src/lib`** in small steps; keep **`pytest`** green.
- **Cost / performance:** measure time per job in logs/DB; tighten budgets (`pdf_max`, `follow-html`, etc.) on the crawl CLI or in adapter code when stable.

### 5.3 Query / maintenance helpers

**Toward** thin query functions or scripts (in **`src/lib`** or **`scripts/`**) that:

- List recent failures by adapter or URL.
- Find **orphan artifacts** (e.g. files on disk not referenced from any successful crawl row).
- Flag **low-value captures** (e.g. soft-error HTML pages mistaken for good content—use existing `soft_200` signals and PDF magic checks).

**Garbage collection** of code: if a function is never referenced by cron or tests, delete it in a dedicated PR with a short note in `mds/human` or commit message—agents should not delete large areas without human review unless policy says otherwise.

---

## 6. Where other docs fit

| Doc | Use |
|-----|-----|
| **`ARCHITECTURE.md`** | Paths and modules. |
| **`OPERATIONS.md`** | Commands and artifacts. |
| **`mds/agents/crawlerAgent.md`** | Crawl **policy** (format-agnostic, respect, budgets). |
| **`mds/agents/cronAgent.md`** | **Pointer** to this file + minimal cron-specific hints. |
| **`mds/agents/sitesCrawl.md`** | Adapter **`seed_urls.txt`** + **`config.py`** → DB registry. |

If anything disagrees with **this** file for **roles and permissions**, treat **`PROJECT_USE.md`** as authoritative and fix the other doc.
