# crawl-thesis

A calibrated, evidence-backed web-crawling thesis for 2026, packaged as a **Claude Code project**. Validated across 9 benchmark rounds.

> **The thesis in one line:** Free/local tools clear everything up to Cloudflare-managed challenges. DataDome / Kasada / Akamai / application-layer require paid Tier-C infrastructure.

## 1 · Install

The skills and `/crawl` command assume a tool stack is present on disk. **Install it first.**

```bash
git clone <repo-url> share_learn_research
cd share_learn_research

make venvs     # creates 4 Python venvs + runs npm install. Idempotent. ~10-15 min on a fresh machine (mostly Chromium downloads).
make check     # verifies everything is wired up. Exits non-zero if anything required is missing.
```

`make venvs` installs:

| Component | Purpose |
|---|---|
| `.venv-scrapling/` | **Required.** Scrapling 0.4+ — `Fetcher` (Tier A, TLS-impersonating HTTP) and `StealthyFetcher(solve_cloudflare=True)` (Tier B, Cloudflare-managed bypass). Bundles `curl_cffi` and Camoufox. |
| `.venv-scrapy/` | **Required.** Scrapy 2.15 — framework for recurrent pipelines (`AUTOTHROTTLE`, `Item`, `Pipeline`, `FEEDS`, `ROBOTSTXT_OBEY`). |
| `.venv-crawl4ai/` | Optional — AI-cleaned markdown. Used in R3 comparison round. |
| `.venv-r3/` | Optional — `nodriver` + Botasaurus + `curl_cffi` for R3 comparison and Akamai TLS profile variants. |
| `node_modules/@playwright/mcp` + `chrome-devtools-mcp` | **Required.** JS rendering + network inspection. |

Details on what `make venvs` runs under the hood: [`scripts/setup.sh`](scripts/setup.sh). Single-component reinstall: `rm -rf .venv-<name> && make venvs`.

**No auto-install at runtime.** If `make check` flags anything missing, the skills and `/crawl` command refuse to proceed — they tell the user to run `make venvs` first rather than install silently.

## 2 · Use

Open the project in Claude Code (`.claude/skills/`, `.claude/agents/`, `.claude/commands/` auto-discover):

```bash
claude
```

Inside Claude Code, three ways to run the thesis:

**a) Slash command (easiest)** — `/crawl <URL> [count] [fields]` orchestrates the full pipeline: preflight → Phase 0 probe → spawn the `crawl-specialist` sub-agent → score → report.

```
/crawl https://news.ycombinator.com/ 30 title,url,score,by,descendants
```

**b) Natural language** — the instructions in `CLAUDE.md` route any "crawl/scrape/extract" request through the same pipeline.

```
"crawl 30 products from https://example.com/category"
```

**c) Programmatic** — spawn the specialist directly when writing an agent yourself.

```python
Agent(subagent_type="crawl-specialist", prompt="<target spec>")
```

Every run writes `result.json` + `result.csv` + `script.py` + `page.html` + `mechanism.md` (L1-L6 intelligence report) to the chosen output directory. Honest `[]` is the correct output when a target exceeds the thesis's ceiling — fabricating rows is forbidden.

## 3 · Run the slidev presentation

The repo ships with a share-and-learn deck (`slides.md`).

```bash
make slides             # dev mode on :3030
npm run build           # static build to dist/
docker build -t crawl-thesis-slides .   # optional: serve via nginx
```

## 4 · Calibrated scope (9 rounds of evidence)

**✅ Works (free/local):** polite public data · documented APIs · SSR blobs · Cloudflare Turnstile / managed challenge (verified on real production, not just sandboxes).

**❌ Does not work (free/local):** DataDome · Kasada v3 · Akamai Bot Manager · application-layer session signatures (Shopee-class). A datacenter-ISP proxy pool **does not flip** these — it sometimes makes things worse (R9 evidence).

## 5 · What's inside

| Component | Where | Does what |
|---|---|---|
| **Thesis skill** | `.claude/skills/crawl-thesis/` | Project's calibrated methodology + tool-stack mapping + Tier A/B/C/D ladder |
| **Upstream methodology skill** | `.claude/skills/web-scraper/` | Phased reconnaissance workflow from `yfe404/web-scraper` that the thesis builds on |
| **Sub-agent** | `.claude/agents/crawl-specialist.md` | Spawnable agent with the thesis baked in |
| **Slash command** | `.claude/commands/crawl.md` | `/crawl <URL>` orchestrator |
| **Makefile + scripts** | `Makefile` · `scripts/setup.sh` · `scripts/check.sh` | Tool-stack install + preflight |
| **Operator runbook** | `THESIS_RUNBOOK.md` | How-to for applying the thesis to a new target |
| **Deep-dive essay** | `essay_deep_dive.md` | ~8000 words, 6 benchmark rounds, full write-up |
| **Benchmarks** | `evaluation_r10/` · `evaluation_scrapling/` | Per-round scorecards + `mechanism.md` self-reports |
| **Slidev deck** | `slides.md` | Share-and-learn presentation |

## 6 · Project instructions for Claude

Claude Code reads [`CLAUDE.md`](CLAUDE.md) on every session in this project — it tells Claude how to route crawl requests, where the tools live, the ethics defaults, and what *not* to do.

## 7 · License + contributing

MIT — see [`LICENSE`](LICENSE). Contributions should add evidence, not subtract discipline. Every new benchmark round ships a `result.json` + `result.csv` + re-runnable `script.py` + an honest `mechanism.md` with L1-L6 sections. Honest failure reports are as valuable as successes.
