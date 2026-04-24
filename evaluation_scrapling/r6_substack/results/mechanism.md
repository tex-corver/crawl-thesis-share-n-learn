# R6-Scrapling — Astral Codex Ten Substack

**Date:** 2026-04-22
**Tool:** Scrapling Fetcher (curl_cffi-backed TLS-impersonating HTTP)
**Protection:** none (public JSON API)
**Outcome:** PASS — 30/30
**Wall-clock:** 0.66 s (extract only, not counting the two Phase-0 probes)

## L1 Research (robots.txt, /api/v1/posts endpoint)

`robots.txt` fetch (HTTP 200, Cloudflare-cached, 607 B):

- Disallows: `/action/`, `/publish`, `/sign-in`, `/subscribe`, `/lovestack/*`, `/p/*/comment/*`, `/inbox/post/*`, `/notes/post/*`, `/embed`, `/feed/private`, `/channel-frame`, `/session-attribution-frame`, `/visited-surface-frame`.
- **`/api/v1/posts` is NOT in the disallow list** — path is allowed for `User-agent: *`.
- Sitemap: `https://www.astralcodexten.com/sitemap.xml`.
- Response headers show `server: cloudflare`, `x-cluster: substack`, `x-served-by: Substack`, `x-powered-by: Express` — normal Substack-on-Cloudflare shape, no challenge markers (`cf-mitigated` absent, no `__cf_chl_*` cookies).

Known surface from prior R6 pass: `https://www.astralcodexten.com/api/v1/posts?limit=N&offset=M` returns a JSON array of post envelopes. Confirmed shape on this probe (keys[0] includes `title`, `subtitle`, `canonical_url`, `post_date`, `wordcount`, `reaction_count`, plus ~60 other fields we don't need).

**Gate A passes immediately.** No Phase-1 browser recon needed.

## L2 Discovery (JSON shape sample, field mapping)

Sample response (keys trimmed to what we care about):

```json
{
  "title": "Half A Month Of Consolation Writing Advice",
  "subtitle": "...",
  "canonical_url": "https://www.astralcodexten.com/p/half-a-month-of-consolation-writing",
  "post_date": "2026-04-21T15:14:10.213Z",
  "wordcount": 5903,
  "reaction_count": 419,
  ...58 other fields ignored
}
```

Field mapping:

| Spec field | Substack key | Type | Notes |
|---|---|---|---|
| `title` | `title` | str | always present |
| `subtitle` | `subtitle` | str \| null | can be empty on Open Threads |
| `canonical_url` | `canonical_url` | str | `https://www.astralcodexten.com/p/<slug>` |
| `post_date_iso` | `post_date` | str (ISO 8601 UTC with `T` + `Z`) | directly ISO 8601 |
| `word_count` | `wordcount` | int | present for every post (Open Threads range 38-521, essays 2000-6000) |
| `like_count` | `reaction_count` | int | present for every post |

All six requested fields are first-class properties of the API envelope — no nested joining needed.

## L3 Extract (Scrapling Fetcher, one call)

**Why Scrapling Fetcher and not DynamicFetcher/StealthyFetcher:**

Per the thesis tool-stack decision tree, when Phase-0 confirms a public JSON API with HTTP 200 and no anti-bot signals, the correct instrument is the lightest HTTP client available. `Scrapling.Fetcher` wraps curl_cffi for TLS-profile impersonation (Chrome/Firefox/Safari JA3+H2) — effectively the same "curl + `-A` UA" call, with the bonus that our TLS handshake looks like a real browser. Overkill for this target, but aligned with the project convention of always using Scrapling rather than raw `requests` so the extractor degrades gracefully if the API ever starts TLS-filtering.

Rejected alternatives:
- `DynamicFetcher` (Playwright): would work but adds ~3 s of browser launch + page nav for a pure JSON response. Wasteful.
- `StealthyFetcher(solve_cloudflare=True)`: only justified when `cf-mitigated: challenge` appears. It did not.
- `requests` / `httpx`: fine, but breaks the "one fetcher family per venv" convention.

The single call:

```python
Fetcher.get(
    "https://www.astralcodexten.com/api/v1/posts?limit=30&offset=0",
    headers={"User-Agent": UA, "Accept": "application/json"},
    timeout=30,
)
```

Returns HTTP 200 + JSON list of 30 envelopes in 0.66 s wall-clock (includes Python startup + Scrapling init + one round-trip over the Pacific).

## L4 Validate (date parse, URL shape, freshness)

Asserted in `extract.py`:

- `len(posts) == 30` ✓
- `canonical_url.startswith("https://")` for all 30 ✓
- `"substack" in url or "astralcodexten" in url` for all 30 ✓
- `"T" in post_date_iso` for all 30 (ISO 8601 with time component) ✓
- Freshness: latest post `2026-04-21T15:14:10.213Z` → **yesterday**. Site is clearly active.

Spot-check of the first 5 extracted rows:

| # | Date | Words | Likes | Title |
|---|---|---|---|---|
| 1 | 2026-04-21 | 5903 | 419 | Half A Month Of Consolation Writing Advice |
| 2 | 2026-04-20 |  521 |  43 | Open Thread 430 |
| 3 | 2026-04-16 | 2051 | 791 | Orban Was Bad, Even Though We Don't Have A Perfect Word For It |
| 4 | 2026-04-13 |  102 |  63 | Open Thread 429 |
| 5 | 2026-04-08 |   38 |  43 | Open Thread 428.5 + Zagreb Update |

Pattern is consistent with ACX's cadence (weekend essays + periodic Open Threads), which anchors that we're pulling real current content, not a stale cache.

## L5 Persist

Written to `/home/hainm/tmp/share_learn_research/evaluation_scrapling/r6_substack/results/`:

| File | Size | Contents |
|---|---|---|
| `extract.py` | 3.4 KB | Re-runnable extractor (Scrapling Fetcher + JSON parse + CSV write) |
| `result.json` | 7.6 KB | Array of 30 typed objects, UTF-8, indented |
| `result.csv`  | 3.9 KB | Header + 30 rows, 6 columns |
| `mechanism.md` | (this file) | L1..L6 intelligence report |

## L6 Honest observations

**Is this the easiest thesis target?** Yes — by a country mile. Substack ships a fully-documented public JSON API (`/api/v1/posts`) whose envelope already carries every field a curator-audience use-case would want (title, subtitle, canonical URL, ISO date, word count, reaction count, plus 58 more we ignored). No pagination gymnastics, no auth, no XHR-sniffing, no Cloudflare challenge — even though Cloudflare is in front of the domain, the WAF doesn't trigger on a polite GET to a documented path.

**Lesson for the thesis:**

1. **The "protection ladder" has a zeroth rung: no protection at all.** Always probe first. Any tool works; the cheapest is right. We used Scrapling Fetcher (one line of code, TLS impersonation we didn't need) but `curl | python -c 'import json,sys; ...'` would have produced the same bytes in a quarter of the wall-clock. The only reason to prefer Scrapling here is codebase-consistency and graceful-degradation-if-Substack-starts-filtering.

2. **robots.txt is the contract, not the server response.** Substack's robots.txt explicitly disallows `/subscribe`, `/action/*`, `/p/*/comment/*` — so even though the server would happily return those, the ethics rule says no. For `/api/v1/posts` there is no prohibition. That is the compliance test, not "did I get a 200".

3. **Platform APIs beat every extraction technique.** When a site publishes a JSON endpoint, using it is categorically better than scraping the rendered page: more fields, better types, no layout drift, no selector rot. The R6 outcome is free-tier success because Substack *wants* us to be able to do this — the API powers their own homepage, RSS, and third-party readers. This is the sanctioned Tier-D path by default (no payment needed).

4. **The thesis calibration holds.** Cloudflare is in the path (`cf-ray: 9f02e1b77b740454-HKG`, `server: cloudflare`) and the fetch still succeeded without any Cloudflare-solver tricks. Cloudflare's *managed challenge* is the protection class we said free tools clear; plain Cloudflare-as-CDN (no challenge fired) is below even that line. Substack-on-Cloudflare at a public API path is the "public SSR + documented API" row of the matrix — Tier A, no escalation ever needed.

**Wall-clock budget:** 5 min target, actual ~1 min total including reconnaissance. This target is the short end of the crawl-difficulty distribution — it exists in the thesis benchmark set precisely so we can anchor one end of the curve against the hard end (R8 DataDome/Kasada/Akamai failures, R9 no-flip proxies).
