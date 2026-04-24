# Mechanism — Astral Codex Ten (Substack)

**Target:** https://www.astralcodexten.com/
**Requested:** 30 items × fields: `title, post_url, post_date, subtitle, audience`
**Result:** PASS — 30/30 items extracted via Phase 0 (public API), no browser needed.
**Tool:** `httpx` against documented Substack v1 API.
**Protection class:** **Public API** (Cloudflare CDN in front, but no challenge fires).

---

## L1 Research

- `robots.txt` — Allows `/` for generic `User-agent: *`. Disallows only admin/auth surfaces (`/action/`, `/publish`, `/sign-in`, `/subscribe`, `/feed/private`, etc.). `/api/v1/posts` is NOT disallowed.
- `sitemap.xml` + `news_sitemap.xml` exposed.
- Substack publishes a de-facto public REST surface under `/api/v1/*` (posts, publication, profile, archive). Heavily used by the Substack iOS/Android apps and the site's own JS — well known, documented via community reverse-engineering (e.g. `substack-api` npm package, scraping guides 2022–2025).
- User-Agent identifies the crawler with a research-contact email.
- Politeness: 2s between paginated API calls (2 calls total for 30 items at page_size=25).

## L2 Discovery

- **Headers from `curl -sI`:** `HTTP/2 200`, `server: cloudflare`, `cf-ray: ...`, `x-service: web`, `x-sub: astralcodexten`, `x-powered-by: Express`. **No `cf-mitigated: challenge`**, **no Turnstile**, **no DataDome / Kasada / Akamai markers**. Cookies (`__cf_bm`, `ab_experiment_sampled`, `ab_testing_id`) are session/AB-test cookies, not a challenge.
- **Quality Gate A — PASS.** Documented public API surfaces all fields. Skip Phase 1/2 per thesis.
- **Endpoint used:** `GET /api/v1/posts?limit=25&offset={N}` → returns a JSON array of `Post` objects.
- **Relevant response fields:**
  - `title` → `title`
  - `canonical_url` → `post_url`
  - `post_date` (ISO-8601) → `post_date`
  - `subtitle` → `subtitle` (ACX uses literal `"..."` as default; preserved verbatim)
  - `audience` → `audience` (`"everyone"` for all 30, i.e. free-tier posts)
- Pagination: `offset` increments by the number of items returned; empty array terminates.

## L3 Validation

- **Row count:** 30/30 ✓
- **Unique primary keys:** 30 unique `post_url` values ✓
- **Field coverage:** `title` 30/30, `post_url` 30/30, `post_date` 30/30, `subtitle` 30/30, `audience` 30/30 ✓
- **Anchor check:** First item is `"Half A Month Of Consolation Writing Advice"` dated `2026-04-21` — matches the live site homepage (top post as of probe time). ✓
- **Cross-source sanity:** `canonical_url` values all begin with `https://www.astralcodexten.com/p/` as expected for Substack post URLs.
- **Date ordering:** `post_date` descending from `2026-04-21` → `2026-03-04` across 30 posts, which is plausible ACX cadence (~6 posts/week, ~7 weeks).
- **Note on `subtitle = "..."`:** The literal string `"..."` is what Substack returns from the API — verified directly by curling the endpoint. Not a truncation artifact. ACX routinely omits subtitles with this placeholder.

## L4 Scaling

- **10×** (300 items): same endpoint, 12 pages at `limit=25`, offsets 0..275. Roughly 24s at 2s/page, well under any rate limit. Zero additional tooling.
- **Full archive** (~1,500+ posts since 2020 launch): loop until empty array. Add exponential backoff on HTTP 429 (never observed in probe). A Scrapy spider with `FEEDS`, `AUTOTHROTTLE`, and `RETRY_TIMES=3` would be overkill for a one-shot but is the recurrent-pipeline answer.
- Switch to `?limit=50` if Substack accepts it (common max), halving request count.

## L5 Persistence

| File          | Bytes   | Purpose |
|---------------|---------|---------|
| `result.json` |   6,850 | Array of 30 typed objects |
| `result.csv`  |   3,896 | Same data, header + 30 rows |
| `script.py`   |   2,289 | Re-runnable driver (`python3 script.py`) |
| `page.html`   | 390,827 | Homepage HTML snapshot for evidence |
| `mechanism.md`|       — | This report |

No `xhr_log.json` — no browser tier ran.

## L6 Adversarial

**Escalation ladder — tried / not-needed:**

| Tier | Tool | Tried? | Outcome |
|------|------|--------|---------|
| Phase 0 curl probe | `curl -sI`, `curl -s` | ✓ | HTTP 200, no challenge markers, documented API found. **Sufficient.** |
| Tier A — Scrapy / httpx on public API | `httpx` | ✓ | 30/30 items, all fields, 2 requests. **PASS.** |
| Tier B — Scrapling StealthyFetcher | — | not needed | Cloudflare serves this publication uncontested (CDN only). |
| Tier C — paid vendor API | — | not needed | — |
| Tier D — sanctioned (Cloudflare AI Crawl Control) | — | not applicable | Substack has a public API already. |

**Thesis verdict:** This is the textbook Phase-0 win. A documented public v1 API on a polite, non-adversarial target. Free/local tools (`curl` + `httpx`, <50 lines of code) do the entire job in ~5 seconds of wall-clock wire time. Matches the "Open API" row of the Phase-0 classification table in `crawl-thesis/SKILL.md`. No protection circumvention occurred; no robots.txt rule was violated; identifiable UA was used throughout.
