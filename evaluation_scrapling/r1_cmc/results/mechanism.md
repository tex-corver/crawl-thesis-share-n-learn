# R1-Scrapling — CoinMarketCap

**Date:** 2026-04-22
**Tool:** Scrapling `Fetcher.get()` (plain HTTPS, TLS impersonation via curl_cffi backend)
**Target protection:** none (Next.js SSR + inline React Query / TanStack hydration blob)
**Outcome:** PASS — 20/20 rows
**Wall-clock:** 0.60 s (single HTTP fetch + in-process JSON walk)
**HTTP fetches to coinmarketcap.com:** 1

## L1 Research

- `https://coinmarketcap.com/` is the canonical top-ranked cryptocurrencies page.
- `robots.txt` was not re-fetched this round (prior runs established it permits `/`).
- Prior-art expectation from the thesis: CMC is a Next.js SSR site — pageProps usually ships hydrated data in the HTML, no browser needed. Confirmed in Phase 0.
- CMC also exposes a documented `data-api` (`api.coinmarketcap.com/data-api/v3/cryptocurrency/listing`) but that's not needed — the same payload is embedded in the homepage HTML. Cheaper to scrape the page once than to hit the API.

## L2 Discovery (Phase 0 evidence)

```
curl -sI https://coinmarketcap.com/
  → HTTP/2 200
  → server: Tengine
  → x-cache: Hit from cloudfront
  → content-security-policy: ... (massive allowlist — production Next.js site)
  → no cf-mitigated, no x-datadome, no akamai-grn, no challenge headers
```

Body fetch: 695 261 bytes of HTML. Grep results on raw body:

| Signal | Count | Meaning |
|---|---|---|
| `__NEXT_DATA__` | 1 | Next.js hydration script tag present |
| `"Bitcoin"` | 55 | Coin data clearly in HTML |
| `"BTC"` | 134 | Symbols in HTML |
| `<tr class=` | 86 | Rendered rows in HTML (not just JSON) |
| `coin-item` | 53 | React component class — rendered table |
| `cryptoCurrencyList` | 1 | **The data blob.** |
| `cf-mitigated` / `x-datadome` / `kpsdk` | 0 | No anti-bot class fires |

**Gate A: PASS.** All target data in raw HTML, zero protection signals. Per the thesis this goes straight to Phase 3 with the cheapest Scrapling fetcher. No browser needed.

### Where the data lives

`__NEXT_DATA__` itself only carries page-level metadata (`pageSize: 100`, `initialTableRankBy: 'rank'`, `globalMetrics`, `cmc100 index value`) — NOT the coin rows.

The rows are shipped in a **separate serialised TanStack Query cache** embedded later in the HTML, keyed by:

```
"cryptoCurrencyList":[ {id, name, symbol, slug, cmcRank, quotes:[{name:"USD", price, marketCap, percentChange24h}, ...]}, ... ]
```

101 items total: 1 sponsored `CMC20` index DTF (no `cmcRank`) at position 0, then 100 properly ranked coins (`cmcRank` 1..100). We filter to `cmcRank is int` and take the first 20.

Each coin's `quotes` array has three entries: `BTC`, `ETH`, `USD`. We select USD by `q.name == "USD"`.

## L3 Extract (Scrapling choice + parsing)

Scrapling **`Fetcher.get()`** is the right fetcher because:

- No JS execution required (data is in raw HTML).
- No anti-bot (so `StealthyFetcher` with Camoufox is pure overkill — ~20× slower for zero benefit).
- No dynamic interaction (so `DynamicFetcher` with Playwright is overkill too).
- `Fetcher` uses curl_cffi under the hood with browser-TLS impersonation, which is insurance against a future IP-level fingerprint tightening without any cost.

Result: **0.60 s** end-to-end (fetch + parse + validate + persist). A browser-class fetcher would have taken 8–20 s and produced identical bytes.

### Parsing — why regex, why a bracket-walker

Two options for reaching the array:

1. Parse all of `__NEXT_DATA__` then deep-walk — but **the list isn't in `__NEXT_DATA__`**, so this approach fails. The list lives in a second JSON blob inline in the HTML body.
2. Locate the `"cryptoCurrencyList":` anchor and extract the immediately-following array — works, but needs depth-tracking because the array contains nested objects + strings with escaped quotes. A naive `rfind(']')` would grab the wrong closing bracket.

We chose option 2 with a **string-aware bracket-depth walker** (`_locate_array`). It tracks:

- `in_str` flag to skip `[`/`]` inside string literals
- `esc` flag to ignore escaped quotes (`\"`) inside strings

This is ~30 lines and handles the actual shape of the document. It's more robust than a regex because the JSON is arbitrary depth.

## L4 Validate

Local assertions in `extract()`:

- `len(rows) == 20` ✓
- `ranks == [1..20]` (no gaps, no duplicates) ✓
- `rows[0].symbol == "BTC"` ✓
- all `price_usd > 0` ✓
- all `market_cap_usd > 1_000_000_000` ✓
- `name` and `symbol` non-empty ✓

Cross-source sanity check (CoinGecko simple price API, separate vendor):

```
CMC homepage blob: BTC = $78,109.73
CoinGecko API:     BTC = $77,922
Delta: +0.24% — well within normal cross-exchange drift (CMC uses VWAP, CoinGecko uses its own source basket)
```

Anchor shape of the top-5 looks correct for late-Apr 2026: BTC dominates, ETH second, USDT third (classic stablecoin in slot 3), XRP, BNB. No obvious data corruption.

## L5 Persist

Files written (all under `evaluation_scrapling/r1_cmc/results/`):

| File | Contents |
|---|---|
| `result.json` | Array of 20 typed dicts: `{rank, symbol, name, price_usd, market_cap_usd, change_24h_pct}` |
| `result.csv` | Same data, header + 20 rows |
| `extract.py` | Reusable script — imports `scrapling.fetchers.Fetcher`, parses, validates, persists |
| `mechanism.md` | This document |

Re-running `extract.py` is idempotent (overwrites outputs with fresh data).

## L6 Honest observations

**What surprised me (mildly):** `__NEXT_DATA__` was not where the coin list lives. CMC upgraded its hydration to ship the TanStack Query cache as a separate inline JSON blob (probably via React Server Components / `useQuery` SSR hydration). The thesis template for "SSR site" assumed `__NEXT_DATA__` → `pageProps.someList`, which was outdated by one Next.js release. I adapted by grep-ing for the actual key name (`cryptoCurrencyList`) and walking the brackets — about 5 extra minutes.

**What I'd change for a recurrent pipeline:** Move this into a Scrapy spider with `AUTOTHROTTLE`, `FEEDS`, and an Item pipeline (`DropEmptyPipeline` + `DedupPipeline`). For a one-shot benchmark, the current 60-line script is sharper.

**What the thesis says about this round:** This is a "Gate A pass" textbook case — exactly like rounds R2 / R4 / R6 in the base benchmarks. The calibrated ceiling doesn't even engage here; free-tier `Fetcher` is 100% sufficient and the extra specialty fetchers (`DynamicFetcher`, `StealthyFetcher`) would waste wall-clock time and yield the same bytes.

**Fetcher choice is the key decision.** Reaching for `StealthyFetcher(solve_cloudflare=True, humanize=True)` on a target like this would be a classic anti-pattern: 20 s of Camoufox warming up to solve a challenge that isn't there. The thesis's insistence on Phase 0 curl-first pays for itself every single time.
