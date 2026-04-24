# Scrapling-across-everything benchmark · scorecard

**Date:** 2026-04-22
**Tool under test:** Scrapling 0.4.7 — `Fetcher` / `DynamicFetcher` / `StealthyFetcher`
**Method:** 6 fresh sub-agents, one per target, each with access only to the project skills + Scrapling venv. No Scrapy, no plain `requests`, no vendor APIs.
**Purpose:** prove (or falsify) that Scrapling alone covers the full thesis range — not just the Cloudflare-managed tier it's famous for.

## Results

| Round | Target | Protection class | Fetcher chosen | Outcome | Rows | Wall-clock | Notes |
|---|---|---|---|---|---|---|---|
| **R1-Scrapling** | CoinMarketCap top-20 | None (Next.js SSR) | `Fetcher` | ✅ PASS | 20/20 | **0.60 s** | Data was in a TanStack Query cache blob, not `__NEXT_DATA__` — required a bracket-walker parse. BTC price within 0.24 % of CoinGecko. |
| **R2-Scrapling** | Binance top-30 USDT | WAF-gated SPA + documented API | `Fetcher` | ✅ PASS | 30/30 | **0.79 s** | Hit `data-api.binance.vision/api/v3/ticker/24hr` directly. WAF ignored. |
| **R3-Scrapling** | scrapingcourse CF sandbox | Cloudflare managed / Turnstile | `StealthyFetcher(solve_cloudflare=True)` | ✅ PASS | (bypass) | **20.5 s** | `<h2>You bypassed the Cloudflare challenge! :D</h2>` — sandbox's built-in success banner. Two-pass solve, no humanise. |
| **R4-Scrapling** | scrapingcourse ecommerce (188 prods) | None | `Fetcher` | ✅ PASS | 188/188 | **28.4 s** | Sale-price pitfall caught by `<ins>`-aware selector + regex guard. 12 paginated pages, 1.2 s polite spacing. |
| **R6-Scrapling** | Astral Codex Ten Substack | None (public JSON API) | `Fetcher` | ✅ PASS | 30/30 | **0.66 s** | `/api/v1/posts?limit=30` — one call, all six fields direct. Latest post 2026-04-21 (yesterday). |
| **R7-Scrapling** | BlackHatWorld forum | **Cloudflare + origin login wall** | `StealthyFetcher` | 🟡 PARTIAL | 0 | 17.66 s | **CF cleared in 17.66 s** (tool works). But BHW now 307-redirects guests to `/login/` — application-layer change since prior R7. Honest `[]`. |

**Aggregate:** 5 PASS · 1 PARTIAL · 0 FAIL. Scrapling handled every *solvable* class with one venv, one API, three fetcher choices.

## What this proves

1. **One tool, full thesis range.** Scrapling's `Fetcher` handles polite HTML and documented JSON at HTTP-client speed (< 1 s). `StealthyFetcher(solve_cloudflare=True)` clears Cloudflare managed challenges at ~20 s. Fetcher choice is a one-line switch inside the same library.

2. **Polite-path speed is competitive with Scrapy.** R2/R6/R1 all completed in < 1 s. R4 is 2.8× slower than Scrapy (28.4 s vs 10.2 s for 12 paginated pages) — Scrapling does per-fetch TLS-impersonation setup that Scrapy's reactor amortises. Still inside any reasonable wall-clock budget; for recurrent high-volume pipelines, Scrapy wins; for one-shot research, Scrapling wins on simplicity.

3. **Cloudflare-managed solve is stable across releases.** R3 solved in 20.5 s matches R5-v1 (~20 s) and the prior R7 (~20 s). No regression on Scrapling 0.4.7.

4. **CF-cleared ≠ data-extracted.** The R7 partial is the most important finding of this batch. BlackHatWorld's Cloudflare edge still yields to `StealthyFetcher` in 17.66 s, but the XenForo origin now redirects guests to `/login/`. The tool did its job; site policy changed underneath. **A cleared CF response is necessary but not sufficient.**

## What this does NOT prove

- Scrapling is not tested here against DataDome, Kasada, Akamai, or application-layer signatures (Shopee-class). The prior R8/R9 evidence stands: those require Tier-C paid infrastructure regardless of the free-tier tool chosen.
- No proxy variance was introduced. All runs are from the same clean IP. R9 already showed that a bad-ASN proxy can *worsen* outcomes on Akamai.

## The updated calibrated ceiling, with Scrapling as the instrument

```
Polite / SSR / documented API   →  Scrapling Fetcher          →  ✅ PASS  (R1, R2, R4, R6)
Cloudflare managed / Turnstile  →  StealthyFetcher            →  ✅ PASS  (R3 sandbox)
Cloudflare on real production   →  StealthyFetcher            →  ✅ SOLVE · 🟡 ORIGIN  (R7)
App-layer signature / login     →  any free tool              →  ❌ FAIL  (R5 Shopee, R7 now)
DataDome / Kasada / Akamai      →  any free tool              →  ❌ FAIL  (R8)
Any of the above, ISP proxy     →  any free tool              →  ❌ FAIL  (R9 — same or worse)
```

## Artefacts

Each round ships `result.json`, `result.csv`, `extract.py`, `mechanism.md` in `evaluation_scrapling/r<N>_<target>/results/`. All re-runnable; all self-audited.

- [R1 CMC](r1_cmc/results/mechanism.md)
- [R2 Binance](r2_binance/results/mechanism.md)
- [R3 CF sandbox](r3_cfsandbox/results/mechanism.md)
- [R4 ecommerce](r4_ecommerce/results/mechanism.md)
- [R6 Substack](r6_substack/results/mechanism.md)
- [R7 BHW](r7_bhw/results/mechanism.md)

## One-line thesis, updated

> **Free/local tools — with Scrapling as the single instrument — clear every protection class up to and including Cloudflare-managed challenges. DataDome / Kasada / Akamai / application-layer (including login walls) require Tier-C paid infrastructure or a business relationship.**
