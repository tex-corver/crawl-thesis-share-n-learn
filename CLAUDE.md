# share_learn_research — crawling thesis project

This repo is a calibrated, evidence-backed thesis for web crawling in 2026, built from 9 benchmark rounds of sub-agent experiments. It's a Claude Code project — clone it, open Claude Code inside it, and `.claude/skills/`, `.claude/agents/`, `.claude/commands/` auto-discover.

## When the user says "crawl", "scrape", "extract data from [URL]", or references the thesis

**Preflight first.** Before any of the three paths below, run `bash scripts/check.sh` (or read its most recent output if run in the same session). If it reports any **required** component missing, **STOP and tell the user to run `make venvs` first** — do NOT try to create venvs / install packages on their behalf. The correct message is:

> "The tool stack isn't installed. Run `make venvs` in the project root first (takes ~10-15 min on a fresh machine, mostly Chromium downloads), then re-run your request."

Once preflight passes:

1. **Prefer the `/crawl` slash command** if available — it handles the entire orchestration (probe → sub-agent → score → report).
2. **Fallback**: spawn the `crawl-specialist` sub-agent directly, giving it the URL + fields + output dir.
3. **Deeper fallback** (if the specialist isn't registered): fill in `research/templates/agent_prompt_template.md`, spawn a `general-purpose` sub-agent with that prompt.

## The thesis in one line

> **Free/local tools clear everything up to Cloudflare-managed challenges. DataDome / Kasada / Akamai / application-layer require paid Tier-C infrastructure.**

Evidence: 9 benchmark rounds in `evaluation_r*/scorecard.md`. Full essay: [`essay_deep_dive.md`](essay_deep_dive.md). Operator runbook: [`THESIS_RUNBOOK.md`](THESIS_RUNBOOK.md).

## What's installed (project-local — no ~/.claude/ writes required)

| Asset | Path | Purpose |
|---|---|---|
| **Skill** — web-scraping methodology | `.claude/skills/web-scraper/` | Phased reconnaissance workflow (Phase 0 → Gate A → Phase 1/2 → validate → report) |
| **Sub-agent** — crawl-specialist | `.claude/agents/crawl-specialist.md` | Spawnable agent that bakes in the thesis |
| **Slash command** — `/crawl <URL>` | `.claude/commands/crawl.md` | One-liner orchestration |
| **Prompt template** | `research/templates/agent_prompt_template.md` | Fallback if /crawl and specialist aren't registered |
| **Runbook** | `THESIS_RUNBOOK.md` | Operator's how-to |

## What the thesis expects on disk (tool stack)

| Tool | Path | When used |
|---|---|---|
| Scrapling 0.4+ (curl_cffi + Camoufox bundled) | `.venv-scrapling/` | **Required.** Tier A `Fetcher` + Tier B `StealthyFetcher(solve_cloudflare=True)` |
| Scrapy 2.15 + scrapy-playwright | `.venv-scrapy/` | **Required.** Recurrent pipelines — AutoThrottle + Items + Pipelines + FEEDS |
| Crawl4AI 0.8+ | `.venv-crawl4ai/` | Optional — AI-cleaned markdown, R3 comparison tool |
| nodriver + Botasaurus + curl_cffi | `.venv-r3/` | Optional — R3 comparison round + Akamai TLS profile variants |
| Playwright (Node) + Chrome DevTools MCP | `node_modules/` | **Required.** JS rendering, network inspection |

**Installation is not automatic.** The skills and `/crawl` command assume the venvs already exist. If they're missing, running `/crawl` fails fast with a message telling the user to run `make venvs`.

## Quick start for a new teammate

```bash
git clone <repo-url> share_learn_research
cd share_learn_research
make venvs          # installs all 4 Python venvs + npm deps (idempotent, ~10-15 min)
make check          # verifies everything is wired up; fails loud if anything missing
claude              # opens Claude Code; skill/agent/command auto-discover from .claude/
```

Inside Claude Code:

```
/crawl https://news.ycombinator.com/ 30 title,url,score,by,descendants
```

or natural language:

```
"crawl 30 posts from https://example.com/feed"
```

Full installer details (what `make venvs` runs under the hood) are in `scripts/setup.sh`. Reinstall a single venv with `rm -rf .venv-<name> && make venvs`.

## Calibrated scope — read before committing to a target

Based on 9 rounds of evidence, this thesis works for:

- ✅ Polite public data / documented APIs / SSR blobs (CMC, Binance, Substack, ecommerce sandboxes)
- ✅ Cloudflare Turnstile / managed-challenge sites (verified at real production: BlackHatWorld forum)

This thesis does NOT work (free-tier) for:

- ❌ DataDome-protected sites (G2 — pre-challenge IP block)
- ❌ Kasada v3 (Hyatt — POW token-mint, no free solver exists)
- ❌ Akamai Bot Manager (Lowe's — JS sensor + browser fingerprint detection)
- ❌ Application-layer session signature (Shopee — silent login redirect + device telemetry)

A datacenter-ISP proxy pool **does not flip** these (R9 evidence in `.claude/skills/crawl-thesis/reference/calibrated-ceiling.md`). True residential proxies + paid solvers are the Tier-C floor.

## Ethics defaults (automated)

- `robots.txt` respected where readable
- User-Agent includes a research-contact identifier
- ≤ 5 fetches to any single target domain per run
- ≥ 10 s between retries
- No login, no authentication, no user-data extraction
- No republishing — artefacts stay in the repo

## Deeper reading

- [`essay_deep_dive.md`](essay_deep_dive.md) — full 8000-word share-and-learn essay
- [`THESIS_RUNBOOK.md`](THESIS_RUNBOOK.md) — operator runbook with templates
- [`share_learn_demo/`](share_learn_demo/) — live-demo kit (presenter script + slides + fallback recording instructions)
- [`research/hard_targets_2026.md`](research/hard_targets_2026.md) — which sites are worth a challenge
- [`evaluation_r10/scorecard.md`](evaluation_r10/scorecard.md) — latest meta-validation; per-round evidence is consolidated in [`.claude/skills/crawl-thesis/reference/calibrated-ceiling.md`](.claude/skills/crawl-thesis/reference/calibrated-ceiling.md)

## Don't

- Don't add paid-service calls (Firecrawl / ZenRows / Scrapfly / CapSolver / 2Captcha) — breaks the free-tier premise.
- Don't write raw proxy URLs into any committed artefact. `.proxies` is 0600 and gitignore-worthy.
- Don't touch `~/.claude/`. Everything in this repo is project-local by design.
- Don't fabricate rows. `[]` + honest explanation is the correct output on failure.
