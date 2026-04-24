# Agent prompt template — fill in `{{PLACEHOLDER}}` fields

Fresh sub-agent, no prior conversation context.

## Mission
Apply our **full thesis** (web-scraper skill methodology + composed free/local tools) to extract **{{N}} {{ITEM_TYPE}}** from {{TARGET_DESCRIPTION}}.

## Target
`{{TARGET_URL}}`

Fields per row:
- `{{FIELD_1}}` — {{FIELD_1_DESC}}
- `{{FIELD_2}}` — {{FIELD_2_DESC}}
- `{{FIELD_3}}` — {{FIELD_3_DESC}}
- `{{FIELD_4}}` — {{FIELD_4_DESC}}
{{OPTIONAL_FIELDS}}

Target N: {{N}} rows.

## Known protection profile (from orchestrator probe)
{{PROBE_RESULTS}}

Examples of good probe-result text:
- *"HTTP 200 to plain curl. Next.js SPA. `__NEXT_DATA__` JSON blob in HTML contains all 4 target fields — expect Phase 0 gate to pass, no browser needed."*
- *"HTTP 403 + `cf-mitigated: challenge`, `cType: managed`. Cloudflare Turnstile — Scrapling.StealthyFetcher(solve_cloudflare=True) has cleared this class before (R7 BHW evidence)."*
- *"HTTP 200 shell but product data absent; robots allows `/search?...`; XHR to `/api/v4/...` returns bot-error code without session cookies — will need homepage-first warming."*
- *"Unknown — run your own Phase 0."*

## Methodology — strict thesis

Read `/home/hainm/tmp/share_learn_research/.claude/skills/web-scraper/SKILL.md` and `workflows/reconnaissance.md` BEFORE writing code.

### Phase 0 (≤ 60 s, no browser)
1. `curl robots.txt`
2. `curl` target with Chrome UA — data in raw HTML? `__NEXT_DATA__`? `__APP_DATA__`? Framework markers?
3. Check for documented public APIs (sitemap.xml, /api/, /feed, /rss)

**Quality Gate A:** if all required fields visible in raw HTML → **skip the browser**, go to Phase 3 with plain HTTP.

### Phase 1 (only if Gate A fails)
Browser recon with XHR capture subscribed *before* navigation:
- `DynamicFetcher` (plain Playwright) or `StealthyFetcher` (Camoufox stealth)
- `page.on('request')` / `page.on('response')` before goto
- For aggressive anti-bot: homepage-first navigation to warm session cookies, then navigate to target URL in the same browser context

### Phase 2 (only if Phase 1 insufficient)
Interactive exploration: scroll, click "load more", trigger lazy XHRs. Subscribe new `page.on` handlers before each action.

### Phase 3 — validate (always run)
- Row count == {{N}} (or document why <)
- All required fields populated, no nulls
- Anchor check (a known-real item appears)
- Unique {{PRIMARY_KEY}} values
- Cross-source sanity if possible

### Phase 4 — escalation if blocked
Based on PROTECTION CLASS observed:
- **Cloudflare managed / Turnstile** → `Scrapling.StealthyFetcher(solve_cloudflare=True, humanize=True, real_chrome=True)`. Proven at R5-v1 + R7.
- **DataDome** → no free solver; document failure, escalate to Tier C.
- **Kasada v3** → no free POW solver; document, escalate to Tier C.
- **Akamai Bot Manager** → try `curl_cffi` with `safari18_0`/`firefox135` profiles first.
- **App-layer (silent redirects, session signature)** → homepage-first warming + fingerprint variants. If still blocked, document and escalate to Tier C.

## Tool stack available (all installed project-local)

| Tool | Path | Import / Invoke |
|---|---|---|
| Fetch MCP | `uvx --from mcp-server-fetch` | `uvx mcp-server-fetch` (stdio MCP) |
| Scrapy 2.15 | `.venv-scrapy/` | `source .venv-scrapy/bin/activate && scrapy ...` |
| Scrapling 0.4+ | `.venv-scrapling/` | `from scrapling.fetchers import Fetcher, DynamicFetcher, StealthyFetcher` |
| Crawl4AI | `.venv-crawl4ai/` | `from crawl4ai import AsyncWebCrawler` |
| nodriver + Botasaurus + curl_cffi | `.venv-r3/` | `import nodriver as uc` / `from botasaurus.browser import browser, Driver` / `import curl_cffi` |
| Playwright Node | `node_modules/playwright` | `require('playwright')` |
| Chrome DevTools MCP | `node_modules/chrome-devtools-mcp/` | stdio MCP |

**Proxy (optional):** if `/home/hainm/tmp/share_learn_research/.proxies` exists (0600), read a random line (`http://user:pass@host:port`), pass via `proxies=` kwarg or `proxy=` kwarg depending on library. **Never write raw proxy URL to any output file.**

## Output directory

Write all files to:
`/home/hainm/tmp/share_learn_research/{{OUTPUT_DIR}}/`

Required:
- `result.json` — array of up to {{N}} typed objects (or `[]` with honest mechanism)
- `result.csv` — same data, header + rows
- `script.py` (or full Scrapy project) — re-runnable
- `page.html` — final body captured (success page or challenge page)
- `xhr_log.json` — if any browser tier ran (list of URL/method/status/content-type)
- `mechanism.md` — ≤ 500 words with these sections:
  - **Tool stack used**
  - **Ethics** (robots, budget, no login, no republish)
  - **Proxy evidence** (if proxy used) — rotation count, no raw URLs
  - **L1 Research**
  - **L2 Discovery** (where data lives, successful path)
  - **L3 Validation** (schema + anchor + cross-source)
  - **L4 Scaling** (what 10× would need)
  - **L5 Persistence** (what was written)
  - **L6 Adversarial** (escalation ladder — what tried, what worked/failed)
  - **Run stats** (wall clock, bytes, fetches, retries)

## Constraints (non-negotiable)

- **Free/local tools only.** No Firecrawl / ZenRows / Scrapfly / Bright Data / CapSolver / 2Captcha / AntiCaptcha / any paid API.
- **No residential proxies unless `.proxies` file exists.** Use via env var reference, not hard-coded.
- **Politeness**: ≤ {{MAX_FETCHES}} fetches to the target domain total. ≥ 10 s between retries. UA with research-contact identifier (e.g. `Mozilla/5.0 (research; thesis-test)`).
- **Off-limits paths** (to avoid contamination): any `round*/`, any `evaluation*/` except `{{OUTPUT_DIR}}`, any `cmc_research/`, any `research/` subdirectories except templates. Proxy file is at `/home/hainm/tmp/share_learn_research/.proxies` — read OK, write NEVER.
- **Honesty**: if you get 0 rows, write `[]` and explain. **Do not fabricate data.** Partial results + honest explanation beat fake completeness.
- **Timebox**: {{TIMEBOX_MINUTES}} minutes total wall clock.

## Return format

Reply with ONE line:
`STATUS, N_items, phase_won_or_blocked_at, one_sentence_verdict`

Examples:
- `PASS, 30 posts, Phase 0 won via /api/v1/posts, polite target — thesis trivial win`
- `FAIL, 0 products, blocked at Phase 4 (DataDome full-enforcement CAPTCHA), Tier C needed`
- `PARTIAL, 12 of 30, Phase 1 extracted page 1 but rate-limit on page 2, need slower throttle`
