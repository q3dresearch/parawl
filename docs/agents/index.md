# Working with an AI Agent

You don't need to read every page of this docs site before getting started.
If you have an AI coding agent available — Claude Code, Cursor, Copilot, Windsurf, or similar —
you can hand the project to it and let it orient itself.

This page tells you exactly what to do.

---

## What the agent will be able to do

Once set up, an agent can:

- crawl the bill and Hansard indexes to discover documents
- download PDFs and extract them to Markdown
- run the test suite and explain failures
- add a new country adapter from scratch
- wire parawl's output into your own app (search, RAG, analytics)

It reads the source code, the docs, and the data it produces.
You steer with plain English; it handles the terminal.

---

## Setup (do this yourself — takes ~2 minutes)

Clone the repo and create a virtual environment.

=== "macOS / Linux"

    ```bash
    git clone https://github.com/q3dresearch/parawl
    cd parawl
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    ```

=== "Windows (PowerShell)"

    ```powershell
    git clone https://github.com/q3dresearch/parawl
    cd parawl
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    ```

Open the `parawl/` folder in your agent's IDE or point its CLI at that directory.
That's it — the agent can take over from here.

---

## First prompt to give your agent

Paste this verbatim into the agent chat to orient it:

```
You are working inside the parawl repo.

parawl is a Southeast Asian parliamentary document crawler and parser.
It crawls bill and Hansard URLs from government websites, downloads the PDFs,
and extracts them to Markdown. The pipeline has three stages: crawl → download → extract.

Read CLAUDE.md if it exists, then read README.md and docs/index.md to orient yourself.
Then run the sample crawl to confirm the environment works:

  PYTHONPATH=src python scripts/sample_crawl.py --insecure

(--insecure is needed because parlimen.gov.my has a self-signed TLS cert on some networks.)

After the crawl completes, tell me what was downloaded and where the extracted files are.
Then ask me what I want to do next.
```

!!! tip "Why --insecure?"
    The Malaysian parliament site (`parlimen.gov.my`) uses a certificate chain that some
    machines cannot verify. `--insecure` skips TLS verification locally — it does not affect
    the content of what is downloaded.

---

## What to ask for next

After the agent confirms the sample crawl worked, here are useful starting points:

**Download specific documents**
> "Download all bills from 2023 and extract their text."

**Explore the data**
> "Open one of the extracted Hansard Markdown files and summarise what it contains."

**Add a new source**
> "I want to add a source for Singapore parliament. Walk me through what a new adapter needs."

**Run the tests**
> "Run the test suite and explain any failures."

**Use the output in my app**
> "I have a FastAPI app. Show me how to load parawl's extracted Markdown files into it."

---

## If the agent gets confused

Give it the docs site URL so it can read the full reference:

```
Read the docs at https://q3dresearch.github.io/parawl/ — start with Architecture,
then Pipeline, then the Malaysia source page.
```

Or point it at specific files in the repo:

| Topic | File to read |
|---|---|
| How the crawl works | `src/lib/sources/my/parliament_my/crawl.py` |
| How PDFs are extracted | `src/lib/pipeline/extract.py` |
| Path conventions | `src/lib/paths.py` |
| Config values (timeouts, headers) | `src/lib/sources/my/parliament_my/config.py` |

---

## Agents that work well with this repo

| Agent | How to open |
|---|---|
| **Claude Code** | `claude` in the terminal from the `parawl/` directory |
| **Cursor** | File → Open Folder → `parawl/` |
| **GitHub Copilot (VS Code)** | Open `parawl/` in VS Code, activate Copilot Chat |
| **Windsurf** | Open `parawl/` as the project root |

Any agent with file-system access and a terminal will work.
The repo is self-contained — no database, no cloud account, no API keys required.
