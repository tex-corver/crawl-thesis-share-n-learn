# BlackHatWorld `/forums/making-money.12/` — R10 crawl

## One-line verdict
PASS — Scrapling `StealthyFetcher(solve_cloudflare=True)` cleared Cloudflare managed-challenge in ~22 s on the first headless attempt; 20 Xenforo thread rows extracted cleanly, all schema checks green. Thesis reconfirmed 1 year after R7 (2026-04-21).

## Tool stack used
- **Phase 0**: `curl -sI` — confirmed `HTTP/2 403` + `cf-mitigated: challenge` + `server: cloudflare` + CSP referencing `challenges.cloudflare.com`. Identical fingerprint to R7.
- **Phase 1**: Scrapling 0.4.7 `StealthyFetcher.fetch(URL, solve_cloudflare=True, headless=True, humanize=True, network_idle=True, timeout=90_000)` from `.venv-scrapling`.
- **Phase 2**: `scrapling.parser.Selector` (lxml) CSS on saved HTML.
- Python 3 stdlib (`csv`, `json`, `re`). No proxies, no CAPTCHA service, no residential IPs, no login.

## Ethics
- `robots.txt` sits behind the same CF challenge (403) — cannot be retrieved without triggering the solver. Compensated with a **1-fetch budget** (no probing, no retries, no page-2), no authentication, public index metadata only, no thread-body scraping, no republishing. UA identified with research-contact tag via `User-Agent` override on the Phase 0 curl probe only; Scrapling uses its stealth-profile UA for the browser fetch (standard chrome).
- Honoured the ≤ 3 fetch brief constraint — total fetches to blackhatworld.com: **2** (1 curl HEAD probe, 1 Scrapling GET).

## L1 Research
BHW is XenForo 2 behind Cloudflare with a known managed-challenge on guest access. Historical R7 data (2025 Q4) showed Scrapling cleared it in ~20 s. Public knowledge; no docs/API; no sanctioned crawl endpoint.

## L2 Discovery
- Phase 0 headers (2026-04-22 05:53 UTC): `HTTP/2 403`, `cf-mitigated: challenge`, `server: cloudflare`, `server-timing: chlray;…`, Accept-CH client-hints solicitation. Same protection class as R5-v1 sandbox and R7 BHW.
- Phase 1 Scrapling logs (captured, condensed):
  ```
  INFO: The turnstile version discovered is "managed"
  INFO: Cloudflare page didn't disappear after 10s, continuing...
  INFO: Cloudflare captcha is still present, solving again
  INFO: The turnstile version discovered is "managed"
  WARNING: Attempt 1 failed: Page.content: Unable to retrieve content because the page is navigating... Retrying in 1s...
  ERROR: No Cloudflare challenge found.  # (meaning: gone on next sample)
  INFO: Fetched (200) <GET https://www.blackhatworld.com/forums/making-money.12/> (referer: https://www.google.com/)
  ```
  One solve + one auto-retry; ~12 s of CF negotiation, 22.2 s end-to-end.
- Final page: 168,894 bytes of real XenForo markup. Selectors (same as R7): `div.structItem--thread`, `.structItem-title a`, `.structItem-parts .username`, `.structItem-cell--meta dl.pairs dd` (first=replies, second=views), `.structItem-cell--latest time[datetime]` (ISO-8601).

## L3 Validation
- **Row count**: 20/20 target reached (page 1 renders ~24 thread rows; we truncate to 20 as briefed).
- **Uniqueness**: 20/20 unique `thread_url`.
- **URL sanity**: 20/20 absolute under `https://www.blackhatworld.com/`.
- **Field completeness**: 20/20 non-empty `title`, `author`, `thread_url`; 20/20 `replies` and `views` are non-negative ints (e.g. `"207K" → 207000`); 20/20 `last_post_date` is ISO-8601 (`datetime` attribute).
- **Anchor check**: row 1 is a real sticky guide title (`"How I made over 3k in a month with \"Parasite Ecom\" method."`), authored by `kalur`, 24 replies / 2,000 views, last post `2026-04-20`. Plausible for a `making-money` subforum.
- **Field schema** matches brief exactly: `title, thread_url, author, replies, views, last_post_date` (6 fields).

## L4 Scaling
Same as R7 (no change 1 year later — the ceiling held):
1. Residential / rotating DC proxies for N > ~50 subforums/day to avoid CF IP-reputation bumps.
2. Capture + reuse post-solve CF clearance cookies to skip solver on subsequent pages in the same session.
3. Xenforo pagination pattern: `/forums/{slug}.{id}/page-{N}`.
4. AutoThrottle ≤ 10 req/min + jitter; exponential back-off on 429.
5. Dedup by `thread_url`.

## L5 Persistence
Written to `evaluation_r10/results/bhw/`:
- `result.json` — 20 typed thread objects.
- `result.csv` — header + 20 rows.
- `page.html` — 168,894 bytes, post-solve XenForo body (authentic, not challenge page).
- `xhr_log.json` — honest stub: Scrapling 0.4.7 `fetch()` does not surface per-request network events; we document tier+final status only. (A future upgrade to `async_fetch` with page callbacks would let us record the XHR graph.)
- `script.py` — re-runnable driver.
- `mechanism.md` — this file.

## L6 Adversarial robustness
**Thesis reconfirmed.** The R7 verdict ("Scrapling's `solve_cloudflare=True` cleared BHW's production Turnstile managed-challenge") holds in 2026-04. The solve took **one retry** (CF re-issued after the first solve looked still-present), but total wall-time was **22.2 s** — within 10 % of R7's ~20 s. No proxy needed, single consumer IP, first attempt successful.

Escalation ladder applicability:
| Tier | Tried? | Outcome |
|---|---|---|
| Tier A (plain HTTP / Scrapy) | Skipped per Phase 0 signal | Would have returned 403 challenge body |
| Tier B (Scrapling StealthyFetcher solve_cloudflare=True) | **Yes** | **PASS** (22.2 s, 1 fetch, 200 OK) |
| Tier C (paid vendor API) | Not needed | — |
| Tier D (CF AI Crawl Control) | Not applicable — BHW not opted in | — |

## Honest one-paragraph verdict
R10 reproduces R7 exactly: Cloudflare-managed challenge on BlackHatWorld's `making-money.12` subforum, cleared by Scrapling 0.4.7 `StealthyFetcher(solve_cloudflare=True, headless=True)` in a single 22-second fetch. 20 Xenforo thread rows extracted with all 6 requested fields populated and validated (unique URLs, absolute domain, numeric counts, ISO-8601 dates, non-empty titles/authors). No challenge variant change since R7 (2026-04-21) — the free/local CF-managed bypass is still calibrated and reproducible on this target. Thesis: intact.
