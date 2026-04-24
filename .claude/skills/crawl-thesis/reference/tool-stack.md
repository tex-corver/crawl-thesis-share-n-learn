# Tool stack — which tool for which protection class

All tools are **project-local** — venvs live at the repo root, no `~/.claude/` writes needed, no `sudo`.

## Installed locations

| Tool | Path | Purpose |
|---|---|---|
| Fetch MCP | invoked via `uvx --from mcp-server-fetch` | Polite HTTP + markdown conversion |
| Scrapy 2.15 + scrapy-playwright | `.venv-scrapy/` | Framework: AutoThrottle + Items + FEEDS + robotstxt_obey |
| Scrapling 0.4+ (Camoufox + curl_cffi bundled) | `.venv-scrapling/` | Cloudflare bypass (StealthyFetcher) + TLS impersonation (Fetcher) |
| Crawl4AI 0.8+ | `.venv-crawl4ai/` | AI-cleaned markdown, some stealth flags |
| nodriver + Botasaurus + curl_cffi | `.venv-r3/` | Anti-detect specialties + TLS profile variants |
| Playwright (Node) | `node_modules/playwright` | JS rendering, browser automation |
| Chrome DevTools MCP | `node_modules/chrome-devtools-mcp/` | Network inspection (optional) |

## Protection-class × tool mapping

### No anti-bot / SSR / public API

```bash
# fastest — plain HTTP
curl -s "$URL" | python3 -c "import json, sys, re; ..."

# OR Fetch MCP for markdown conversion
uvx --from mcp-server-fetch mcp-server-fetch
```

### Needs-JS but no anti-bot

```python
# Scrapling DynamicFetcher — plain Playwright
from scrapling.fetchers import DynamicFetcher
page = DynamicFetcher.fetch(url, network_idle=True, wait_selector="div.products")
```

### Cloudflare Turnstile / managed challenge — ✓ PASSES

```python
# THE proven recipe (R5-v1 sandbox, R7 BHW real-world)
from scrapling.fetchers import StealthyFetcher
page = StealthyFetcher.fetch(
    url,
    solve_cloudflare=True,
    humanize=True,
    real_chrome=True,
    network_idle=True,
)
# ~20 s solve time; log shows turnstile version detection + solve
```

### DataDome — ✗ FAILS free tier (requires Tier C)

```python
# All of these will still return the DataDome challenge:
from scrapling.fetchers import Fetcher, StealthyFetcher
Fetcher.get(url, impersonate="chrome")    # 403 pre-challenge
StealthyFetcher.fetch(url, humanize=True) # full JS CAPTCHA served, can't solve

# Escalate to Tier C: Scrapfly/ZenRows/Bright Data/Zyte/Oxylabs.
```

### Kasada v3 — ✗ FAILS free tier (no POW solver exists)

```python
# Escalate to Tier C immediately. Kasada requires x-kpsdk-ct / -cd tokens
# that only vendor-provided POW solvers can mint.
```

### Akamai Bot Manager — mostly ✗ free tier

```python
# Worth trying curl_cffi with specific profiles (sometimes succeeds):
import curl_cffi
for profile in ["safari18_0", "firefox135", "chrome131"]:
    r = curl_cffi.get(url, impersonate=profile, timeout=30)
    if r.status_code == 200 and b"product" in r.content:
        break  # rare but possible

# If the response is HTTP 200 with only a JS sensor page (~2.5 KB), you need
# a real browser that also evades Akamai's JS fingerprint. Browser tiers
# (Camoufox, patchright, nodriver) all tested and fingerprinted — R8 Lowe's.

# Escalate to Tier C.
```

### Application-layer (Shopee-class silent redirect)

```python
# ALWAYS do homepage-first navigation in the same browser context:
from scrapling.fetchers import StealthyFetcher

# Warm session cookies from homepage
page_home = StealthyFetcher.fetch(
    f"https://{domain}/",
    real_chrome=True, humanize=True, network_idle=True,
)
cookies = page_home.cookies  # collect SPC_*, csrftoken, etc.

# Then navigate to search/target in same context (capture XHRs before nav!)
# R5 evidence: this DOES collect the cookies but the API still returns error 90309999
# unless the IP is also whitelisted. → Escalate to Tier C with residential proxy.
```

## Scrapy defaults — the lifecycle hygiene floor

For recurrent pipelines, prefer Scrapy. Every default is a lifecycle dimension you don't have to remember:

```python
# settings.py
ROBOTSTXT_OBEY = True
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 0.25
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429, 500, 502, 503, 504, 522, 524, 408, 202]

USER_AGENT = "crawl-thesis-research (contact@example.com)"

FEEDS = {
    "result.json": {"format": "json", "indent": 2, "overwrite": True},
    "result.csv":  {"format": "csv",  "overwrite": True},
}

ITEM_PIPELINES = {
    "myproject.pipelines.DropEmptyPipeline": 100,
    "myproject.pipelines.DedupPipeline": 200,
}
```

Round 4 evidence: `DropEmptyPipeline` caught a real sale-price-concatenation bug (`"32.0024.00"`) mid-run, no human intervention. A hand-rolled script would have shipped it silently.

## Optional — proxy integration

If `.proxies` exists at project root (0600 permissions):

```python
import os, random
# Find project root — either cwd if we're already there, or the skill's grandparent×3
proxy_file = os.environ.get(
    "PROXY_FILE",
    os.path.join(os.getcwd(), ".proxies"),
)
proxies = open(proxy_file).read().strip().split("\n")
proxy_url = random.choice(proxies)

# Scrapling supports proxy= kwarg on all fetchers
page = StealthyFetcher.fetch(url, proxy=proxy_url, solve_cloudflare=True)
```

**Never write the raw proxy URL to any output file.** Reference it as `$PROXY` env var in logs. R9 evidence: ISP-class proxies flip failure mode but not outcome for Tier-C protection classes.

## Not using (and why)

| Tool we haven't integrated | Why |
|---|---|
| Firecrawl | Paid service. Breaks free-tier premise. |
| ZenRows | Paid service. |
| Scrapfly | Paid service (though they're the "correct Tier C answer" for hard targets). |
| Bright Data | Paid residential + vendor API. |
| 2Captcha / CapSolver / AntiCaptcha | Paid CAPTCHA solvers. Ethical category separate from "scraping." |
| FlareSolverr | Depends on `nodriver` internally; we just use `nodriver` directly. |
| undetected-chromedriver | Superseded by `nodriver` (same author). |
| puppeteer-stealth | Deprecated Feb 2025 (upstream notice). |

See `reference/protection-classes.md` for the escalation ladder per class.
