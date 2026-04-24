# R3-Scrapling — Cloudflare managed sandbox

**Date:** 2026-04-22
**Tool:** Scrapling `StealthyFetcher(solve_cloudflare=True, headless=True, network_idle=True)`
**Protection:** Cloudflare Turnstile / managed challenge (`cType: managed`)
**Outcome:** **PASS**
**Solve wall-clock:** 20.5 s (single attempt, `humanize=False`)

## L1 Research (prior evidence)

- **R3-original (9 benchmark rounds ago):** 6 generalist tools — plain Playwright, nodriver, Botasaurus, Crawl4AI, curl_cffi impersonation, Scrapy+playwright — all scored 0/6 against this sandbox. Interstitial never cleared.
- **R5-v1:** Scrapling `StealthyFetcher(solve_cloudflare=True)` cleared it in ~20 s. First proof that "solve_cloudflare" is not marketing.
- **R7:** Same recipe, applied to real production (BlackHatWorld forum, Cloudflare-managed). Still worked. Sandbox-to-reality transfer confirmed.
- This round (R3-Scrapling) re-validates R5-v1 with the current `.venv-scrapling` pinning (Scrapling 0.4+ with Camoufox bundled).

## L2 Discovery (Phase 0 control)

```
$ curl -sI -A "Mozilla/5.0 ... Chrome/120" https://www.scrapingcourse.com/cloudflare-challenge
HTTP/2 200
server: cloudflare
cf-ray: 9f02e0b15d61fdfa-SIN
content-type: text/html; charset=UTF-8
...
```

Note: HTTP/2 200 is returned with the **challenge page** as body, not a 403.
Body first 2 KB:

```html
<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>
<meta http-equiv="content-security-policy" content="...script-src '...'
https://challenges.cloudflare.com...">
```

Signature confirmed: `<title>Just a moment...</title>` + challenges.cloudflare.com CSP +
`server: cloudflare` + `cf-ray` header. **Class 3 — Cloudflare managed challenge.**

Plain curl cannot proceed further — no JS engine to execute the Turnstile challenge script.

## L3 Extract (StealthyFetcher)

```python
from scrapling.fetchers import StealthyFetcher

page = StealthyFetcher.fetch(
    "https://www.scrapingcourse.com/cloudflare-challenge",
    solve_cloudflare=True,
    headless=True,
    network_idle=True,
    humanize=False,
)
```

**Attempts:** 1 (success on first attempt — did not need `humanize=True` retry).

**Internal trace (from Scrapling's logger):**

```
07:24:16  INFO: The turnstile version discovered is "managed"
07:24:28  INFO: Cloudflare page didn't disappear after 10s, continuing...
07:24:28  INFO: Looks like Cloudflare captcha is still present, solving again
07:24:28  INFO: The turnstile version discovered is "managed"
07:24:33  INFO: Cloudflare captcha is solved
07:24:34  INFO: Fetched (307) <GET ...cloudflare-challenge>
07:24:34  INFO: Fetched (200) <GET ...cloudflare-challenge>  ← target reached
```

Scrapling's solver took two passes (common — first attempt was deemed still-present after 10 s, second pass completed). Total wall-clock 20.5 s from `fetch()` call to return.

## L4 Validate

| Check | Value | Verdict |
|---|---|---|
| HTTP status after solve | 200 | ✅ |
| `page.url` after solve | `https://www.scrapingcourse.com/cloudflare-challenge` | ✅ (no redirect to challenge URL) |
| Page title | `Cloudflare Challenge - ScrapingCourse.com` | ✅ (NOT "Just a moment...") |
| `<h1>` text | `Cloudflare Challenge` | ✅ (expected sandbox h1) |
| `<h2>` banner | **`You bypassed the Cloudflare challenge! :D`** | ✅ (unambiguous proof — sandbox's explicit success marker) |
| Body size | 4.4 KB (real content, not 1–2 KB challenge shell) | ✅ |
| Body contains `challenges.cloudflare.com/turnstile/v0/api.js` | Yes — but as an external tag in the now-rendered page, not as a CSP directive. The success banner is present alongside it. | ✅ (normal — Turnstile is still embedded on the post-challenge page) |

The h2 `"You bypassed the Cloudflare challenge! :D"` is the sandbox's built-in success affordance. It only appears to clients that cleared the challenge. That's the sandbox's explicit contract.

## L5 Persist

```
evaluation_scrapling/r3_cfsandbox/results/
├── extract.py          # re-runnable driver
├── result.json         # structured outcome
├── page.html           # full 4.4 KB post-challenge body
├── page_snippet.txt    # first 500 chars
└── mechanism.md        # this file
```

## L6 Honest observations — what this means for the thesis

1. **Sandbox trick still transfers.** 20.5 s solve matches R5-v1 and R7 wall-clocks. The Scrapling recipe is stable across Scrapling 0.4+ releases. No regression.
2. **`humanize=True` was not needed.** R5-v1 used it defensively; first-attempt-no-humanize works on Cloudflare-managed sandbox. Worth noting that the thesis runbook defaults to `humanize=True` for tighter production targets (R7 BlackHatWorld), but the sandbox-grade challenge is beatable without mouse-movement simulation.
3. **Two-pass solve is normal.** Scrapling's log "Cloudflare page didn't disappear after 10s, continuing..." followed by a second pass is expected behaviour, not a failure signal. The library waits 10 s, re-inspects, and re-solves as needed. Final success comes from pass #2 in this run.
4. **The only thesis-relevant failure mode for this class is IP reputation.** From a clean VM residential-ish IP the solve is unconditional. R9 evidence (datacenter-ISP proxy) showed that low-reputation IPs cause Cloudflare to re-challenge even after Turnstile success. This run confirms a normal IP has no such issue.
5. **Ceiling confirmed.** Nothing in this run changes the thesis: **Cloudflare managed = clearable with free local tools; DataDome/Kasada/Akamai/app-layer = Tier C.** The 9-round boundary holds after 10 rounds.

## Fetch budget

| Fetch | Purpose | Tool |
|---|---|---|
| 1 | Phase 0 control header probe | `curl -sI` |
| 2 | Phase 0 control body probe | `curl -s` |
| 3 | StealthyFetcher solve + extract | Scrapling |

Total: 3 fetches. Budget respected.
