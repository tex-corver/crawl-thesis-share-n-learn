# Thesis Runbook — how to apply this thesis to a new target

**Audience:** you (future), teammates, or future-Claude-in-this-project.
**Purpose:** crawl a new target using the thesis (skill + framework + tools) via a fresh sub-agent, in a reproducible way.
**Read time:** 10 min; usable as a copy-paste kit.

---

## 0. The mental model (re-stated)

```
Input:   A URL + a target field list.
Output:  result.json + result.csv + mechanism.md + a re-runnable script.
How:     One sub-agent, fresh context, fed (a) the skill methodology, (b) the
         installed tool stack, (c) a tight rubric, (d) a constrained scope.
         The sub-agent reasons, probes, escalates, reports.
You:     Score what it returns; decide if the output is production-grade.
```

---

## 1. Prerequisites — what must exist on disk

If this directory (or a copy of it) has the layout below, the thesis is "armed." All paths are relative to the project root (`/home/hainm/tmp/share_learn_research/`).

```
.claude/skills/web-scraper/      ← methodology skill (SKILL.md + workflows/ + strategies/)
.venv-scrapy/                    ← Scrapy 2.15 + scrapy-playwright (framework)
.venv-scrapling/                 ← Scrapling 0.4+ (Cloudflare-solver specialty)
.venv-crawl4ai/                  ← Crawl4AI (AI-cleaned markdown + stealth flags)
.venv-r3/                        ← nodriver + Botasaurus + curl_cffi (anti-detect specialties)
node_modules/@playwright/mcp/    ← Microsoft Playwright MCP (browser)
node_modules/chrome-devtools-mcp/ ← Google Chrome DevTools MCP (network inspect)
.proxies                         ← OPTIONAL: one URL per line, 0600 perms
research/templates/              ← this folder — prompt templates
THESIS_RUNBOOK.md                ← this file
```

**Smoke-test this is all present:**

```bash
ls .claude/skills/web-scraper/SKILL.md
ls .venv-scrapy/bin/scrapy .venv-scrapling/bin/python .venv-crawl4ai/bin/python .venv-r3/bin/python
ls node_modules/@playwright/mcp node_modules/chrome-devtools-mcp
```

If any line fails, see §6 "Re-install from scratch."

---

## 2. The full workflow — what YOU do to crawl a new target

```
STEP 1.  Write a one-paragraph task description of what you want.
STEP 2.  Copy `research/templates/agent_prompt_template.md` and fill in the blanks.
STEP 3.  Copy `research/templates/checklist_template.yml` and write your success criteria.
STEP 4.  Create an output directory — conventionally `evaluation_r<N>/results/<target_name>/`.
STEP 5.  Spawn a sub-agent with the Agent tool, pointing it at the filled-in prompt.
STEP 6.  Wait. The agent returns a one-line summary.
STEP 7.  Score the output against your checklist (there's a generic scorer at `research/templates/score_template.py`).
STEP 8.  Read the agent's mechanism.md — decide if the run is production-ready.
```

That's the whole loop. Time: 15-30 min wall-clock per target (5 min for you, 15-25 min for the agent).

---

## 3. The prompt template (the critical artefact)

Save this template at `research/templates/agent_prompt_template.md`. Fill in `{{PLACEHOLDER}}` fields per target.

```markdown
Fresh sub-agent, no prior conversation context.

## Mission
Apply our **full thesis** (web-scraper skill methodology + composed free/local
tools) to extract **{{N}} {{ITEM_TYPE}}** from {{TARGET_DESCRIPTION}}.

## Target
`{{TARGET_URL}}`

Fields per row:
- `{{FIELD_1}}` — {{DESCRIPTION}}
- `{{FIELD_2}}` — {{DESCRIPTION}}
- ... (4-6 fields typical)

Target N: {{N}} rows.

## Known protection profile (from orchestrator probe)
{{PROBE_RESULTS}}
(e.g. "HTTP 200 to plain curl — SPA, no CF challenge, data in __NEXT_DATA__")
(or "HTTP 403 + cf-mitigated: challenge, cType=managed — Scrapling StealthyFetcher
should clear it per R5-v1/R7 evidence")
(or "unknown — run your own Phase 0")

## Methodology — strict thesis

Read `/home/hainm/tmp/share_learn_research/.claude/skills/web-scraper/SKILL.md`
and `workflows/reconnaissance.md` BEFORE writing code. Apply the phases:

### Phase 0 (≤ 60 s, no browser)
1. `curl` robots.txt
2. `curl` the target with Chrome UA — is data in raw HTML? __NEXT_DATA__? Any framework markers?
3. Check for documented public APIs (sitemap.xml, /api/, /feed, /rss)

**Gate A:** if all required fields are visible in raw HTML → **skip the browser**, go straight to Phase 3 with plain HTTP.

### Phase 1 (only if Phase 0 fails)
Browser recon with XHR capture **before** navigation:
- Use `DynamicFetcher` (plain Playwright) or `StealthyFetcher` (Camoufox stealth)
- `page.on('request')` / `page.on('response')` subscribed BEFORE goto
- If site has aggressive anti-bot: homepage-first navigation to warm session cookies, then navigate to target URL in the same browser context

### Phase 2 (only if Phase 1 insufficient)
Interaction to trigger lazy-loaded XHRs: scroll, click "load more," etc.

### Phase 3 (validation — always run)
- Row count == {{N}}
- All required fields populated
- Anchor check (e.g. known-real item appears in results)
- Unique URLs / dedup key
- Cross-source comparison if possible (another endpoint, public feed, etc.)

### Phase 4 — ESCALATION if blocked
Use the escalation ladder based on the PROTECTION CLASS observed:

- **Cloudflare Turnstile / managed challenge** → `Scrapling.StealthyFetcher(solve_cloudflare=True, humanize=True)`. Proven working at R5-v1 (sandbox) + R7 (BlackHatWorld production).
- **DataDome** → will fail without a paid CAPTCHA solver. Document the failure; escalate to Tier C recommendation.
- **Kasada v3** → POW token-mint; no free solver exists. Same — document, escalate.
- **Akamai Bot Manager** → try `curl_cffi` with safari18_0/firefox135 profiles first. If blocked, document.
- **Application-layer** (Shopee-class silent redirects) → try homepage-first session warming. If still blocked, document.

## Tool stack available (all installed project-local)

| Tool | Path | Use for |
|---|---|---|
| Fetch MCP | `uvx --from mcp-server-fetch` | Polite HTTP + markdown conversion |
| Scrapy | `/home/hainm/tmp/share_learn_research/.venv-scrapy/` | Framework: AutoThrottle + Items + FEEDS + robotstxt |
| Scrapling | `/home/hainm/tmp/share_learn_research/.venv-scrapling/` | Fetcher (TLS), StealthyFetcher (CF-solve), DynamicFetcher |
| Crawl4AI | `/home/hainm/tmp/share_learn_research/.venv-crawl4ai/` | AI-cleaned markdown + stealth flags |
| nodriver + Botasaurus + curl_cffi | `/home/hainm/tmp/share_learn_research/.venv-r3/` | Specialty anti-detect + TLS impersonation |
| Playwright MCP | `/home/hainm/tmp/share_learn_research/node_modules/@playwright/mcp/` | JS rendering, browser automation |
| Chrome DevTools MCP | `/home/hainm/tmp/share_learn_research/node_modules/chrome-devtools-mcp/` | Network inspection |

## Output directory

Write EVERYTHING to:
`/home/hainm/tmp/share_learn_research/{{OUTPUT_DIR}}/`

Required files:
- `result.json` — array of up to {{N}} typed objects
- `result.csv` — same, header row + data rows
- `script.py` or full project — re-runnable code
- `page.html` — final fetched body (audit)
- `mechanism.md` — ≤ 500 words with sections:
  - **Tool stack used** (which libraries + config)
  - **Ethics** (robots.txt outcome, fetch budget, no login/auth/PII)
  - **L1 Research** (what you checked before coding)
  - **L2 Discovery** (where data lives — SSR blob, XHR, API, etc.)
  - **L3 Validation** (schema check + anchor)
  - **L4 Scaling** (what 10× data would need)
  - **L5 Persistence** (JSON + CSV + metadata)
  - **L6 Adversarial** (what you tried when blocked; honest failure analysis)
  - **Run stats** (wall clock, bytes, retries, fetches)

## Constraints (non-negotiable)

- **No paid services**: no Firecrawl / ZenRows / Scrapfly / Bright Data / CapSolver / 2Captcha / AntiCaptcha.
- **No paid proxies** unless a `.proxies` file exists at project root. If it does: read random line, use via `proxy=` kwarg, **never write raw proxy URL to any output file**.
- **Politeness**: ≤ {{MAX_FETCHES}} fetches to the target domain total, ≥ 10 s between retries, UA with a research-contact identifier.
- **Off-limits paths**: any `round*/` or other `evaluation*/` directories except your own output dir.
- **Honesty**: if you get 0 rows, write `[]` and explain. **Never fabricate data**. Partial results + honest explanation beat fake completeness.
- **Timebox**: {{TIMEBOX_MINUTES}} minutes total.

## Return format

Reply with ONE line in this format:
`STATUS, N_items, phase_that_won_or_blocked_at, one_sentence_verdict`

Examples:
- `PASS, 30 posts, Phase 0 won via public /api/v1/posts, thesis trivially wins on polite target`
- `FAIL, 0 products, blocked at Phase 4 (DataDome full-enforcement CAPTCHA), free tools cap at CF-managed — Tier C needed`
- `PARTIAL, 12 of 30 products, Phase 1 extracted from first page but pagination hit rate limit, need slower throttle or session rotation`
```

---

## 4. The checklist template

Save at `research/templates/checklist_template.yml`. Fill in target-specific criteria.

```yaml
benchmark: {{TARGET_NAME}}
task: "{{ONE_LINE_TASK_DESCRIPTION}}"

entry_url: "{{TARGET_URL}}"

correctness:
  # Binary pass/fail per target
  - id: C1
    name: row_count_N
    check: "result.json has exactly {{N}} rows (or {{MIN}}-{{N}} range if partial OK)"
  - id: C2
    name: required_fields_present
    fields: [{{FIELD_1}}, {{FIELD_2}}, ...]
  - id: C3
    name: anchor_sanity
    check: "a known-real item (e.g. 'Apple' for a laptop search) appears in results"
  - id: C4
    name: unique_keys
    check: "no duplicate {{PRIMARY_KEY}} values"
  - id: C5
    name: types_valid
    check: "all {{NUMERIC_FIELD}} values are parseable numbers"
  # add more per target

quality:
  Q1: setup_friction     # 5=one command, 1=>4 steps
  Q2: wall_clock         # 5=<15s, 3=<60s, 1=>180s
  Q3: payload_efficiency # 5=<500KB, 3=<5MB, 1=>5MB
  Q4: robustness         # 5=no retries, 3=self-recovered, 1=crashed
  Q5: output_structure   # 5=JSON+CSV+metadata, 3=JSON only
  Q6: ethics             # 5=robots+UA+rate-limit, 3=defaults

lifecycle:
  L1: research           # Phase 0 coverage
  L2: discovery          # Where data lives
  L3: validation         # Schema + anchor + cross-source
  L4: scaling            # Pagination + concurrency + retry
  L5: persistence        # JSON + CSV + metadata
  L6: adversarial        # Escalation ladder documented

scoring:
  PASS: "all C1..C5 pass"
  PARTIAL: "C1 partially met; C2..C5 pass on what was extracted"
  FAIL: "C1 fails completely"
```

---

## 5. The invocation — how to call the Agent tool

Once you've filled in the template, the sub-agent call looks like this (pseudocode — in practice just prompt the assistant):

```python
# What you'd say to Claude (or paste into an Agent tool call)

Agent(
    subagent_type="general-purpose",
    description="Crawl {{TARGET_NAME}} via full thesis",
    prompt=open("research/templates/agent_prompt_template.md").read()
           .replace("{{TARGET_URL}}", "https://example.com/data")
           .replace("{{N}}", "30")
           .replace("{{ITEM_TYPE}}", "products")
           # ... etc
)
```

In practice in a Claude Code session:

> **You, to Claude:**
> *"Run the thesis on `https://example.com/category/widgets`. Extract 20 products with name, price, url, rating. Use the template at `research/templates/agent_prompt_template.md`. Output to `evaluation_r10/results/example_com/`. Time-box 15 min. Spawn a sub-agent and report back."*

Claude fills in the template, spawns the Agent tool, waits, scores, returns a summary. You review.

---

## 6. Worked example — what this looks like end-to-end

**Suppose you want to crawl `https://www.coingecko.com/en/coins/bitcoin`** — a public crypto data page.

**Your one paragraph to Claude:**

> *"Apply the thesis to coingecko.com — extract Bitcoin's top 20 related metrics: price, market cap, 24h volume, circulating supply, max supply, ath, atl, price change %. Output to `evaluation_r10/results/coingecko_btc/`. 10-min timebox. Use the template."*

**Claude automatically:**

1. **Orchestrator probe** — `curl https://www.coingecko.com/en/coins/bitcoin`
   → HTTP 200, HTML, check for `__NEXT_DATA__` → likely present.
2. **Fills in the prompt template:**
   - `{{TARGET_URL}}` = `https://www.coingecko.com/en/coins/bitcoin`
   - `{{N}}` = 1 row with 20 fields (OR pivot: `{{N}}` = 20 metric rows)
   - `{{PROBE_RESULTS}}` = "HTTP 200, Next.js SPA, __NEXT_DATA__ detected in HTML — expect Phase 0 gate to pass"
   - `{{MAX_FETCHES}}` = 3
   - `{{TIMEBOX_MINUTES}}` = 10
3. **Spawns Agent** with the filled-in prompt.
4. **Agent returns** ~5 min later with `PASS, 20 metrics, Phase 0 won via __NEXT_DATA__ parse, trivial win`.
5. **Claude scores** against the checklist, presents result.

You never touch the prompt template unless the target needs a custom twist.

---

## 7. Re-install from scratch (if prerequisites are missing)

```bash
# Core: Python venvs
cd /home/hainm/tmp/share_learn_research  # or wherever project root is

# Scrapy
python3 -m venv .venv-scrapy
. .venv-scrapy/bin/activate
pip install scrapy scrapy-playwright
deactivate

# Scrapling
python3 -m venv .venv-scrapling
. .venv-scrapling/bin/activate
pip install "scrapling[fetchers]"
scrapling install  # downloads Camoufox etc.
deactivate

# Crawl4AI
python3 -m venv .venv-crawl4ai
. .venv-crawl4ai/bin/activate
pip install crawl4ai
python -m playwright install chromium
crawl4ai-setup
deactivate

# Anti-detect specialties
python3 -m venv .venv-r3
. .venv-r3/bin/activate
pip install curl_cffi nodriver botasaurus
deactivate

# Node + MCPs
npm init -y
npm install @playwright/mcp chrome-devtools-mcp
npx playwright install chromium

# The skill
mkdir -p .claude/skills
git clone --depth 1 https://github.com/yfe404/web-scraper .claude/skills/web-scraper
```

**Total install time:** ~10-15 min on a fresh machine (mostly Chromium downloads).

---

## 8. What the sub-agent pattern relies on

Two Claude Code primitives:

1. **The `Agent` tool (`subagent_type="general-purpose"`)** — spawns a fresh agent with its own context. The parent orchestrator's conversation is NOT visible to the sub-agent. This is the "no prior context" guarantee that makes the benchmark fair and the mechanism.md honest.

2. **Project-local tooling** — everything lives in the project directory, so any user with a clone can re-run. No MCP server registered at session start is required; agents invoke the installed libraries directly via Bash.

3. **Optional — MCP servers** registered in `.mcp.json` at session start. If Claude Code is restarted with the `.mcp.json` in place, MCP tools (Fetch / Playwright / Chrome DevTools) become first-class. In the current session that hasn't happened; agents used direct library invocation. Both modes work.

---

## 9. When NOT to use this thesis

- **Kasada-protected targets** (Hyatt, Ticketmaster, some StubHub) — no free POW solver exists. The thesis will produce an honest failure report, but no extraction.
- **Sites requiring login** — scope-creep into auth, CSRF, credential storage. Thesis stays public-data only.
- **GDPR-sensitive personal data** — regardless of whether you can extract it, the legal/ethics call is upstream. See essay §1.4.
- **Anything under active Ticketmaster/Scalper-defence litigation** — legal exposure outweighs tool capability.
- **When you need >10k URLs/day** — thesis is tuned for research + polite batch. Production-scale would need Tier-C paid infrastructure from the start.

---

## 10. One-paragraph summary you can paste into any future session

> **"Apply the thesis defined in `THESIS_RUNBOOK.md` at project root. Read the web-scraper skill at `.claude/skills/web-scraper/SKILL.md` and any of the 5 venvs as needed. Spawn a sub-agent with the template at `research/templates/agent_prompt_template.md`, filling in the target URL / fields / timebox. Constrain to free/local tools only. Output to `evaluation_r<N>/results/<target>/`. The agent should produce `result.{json,csv}` + `script.py` + `page.html` + `mechanism.md` with L1..L6 sections. Score against the checklist template; report ONE-LINE verdict and the mechanism summary."**

That paragraph — plus the URL and fields — is the entire human-to-Claude-to-sub-agent handoff. Future-you should never need more.
