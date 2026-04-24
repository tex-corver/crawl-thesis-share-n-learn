# Shopee SG `/search?keyword=laptop` — Round 10

**Target:** `https://shopee.sg/search?keyword=laptop`
**Ask:** 30 rows of `name, price, image_url, product_url`.
**Outcome:** **FAIL (as expected).** Application-layer protection (silent redirect to `/buyer/login`). Free/local tools cannot bypass — Tier C required.
**Thesis verdict match:** ✓ Reproduces R5 Shopee precedent exactly.

---

## L1 Research

**robots.txt (shopee.sg)**
- Wildcard `User-Agent: *` policy explicitly **permits** `/search?keyword=<term>` except for a narrow set of query flavours (`?shop=`, `?brands=`, `?originalCategoryId=`, `?utm_source=`, `?searchPrefill`, `?hashtag=`, etc.).
- `Crawl-delay: 1` for `*`, which we observed (≥ 11 s between probes in this run).
- Googlebot/Bingbot get `Crawl-delay: 0.1` — the site is indexable in principle.
- **Legal/ethical posture:** polite reading of public search is not disallowed. No login attempted, no user-data extraction, no republishing of artefacts.

**Prior-art — internal:**
- `evaluation_r5/` Shopee run produced the same silent-redirect signature. R5 was the round that defined the "application-layer" class in our thesis.
- `evaluation_r9/` repeated the attempt from a Singapore residential proxy; still failed. Even a clean in-country IP does not clear Shopee's session-device binding.
- Thesis SKILL.md line 49 (`Application-layer (session/device) — ❌ Tier-C only`) and line 130 (`R5 Shopee evidence (even with ISP proxy: R9)`) predict this outcome.

**Prior-art — external:**
- Shopee error code `90309999` is documented in the community as "login/session required" for unauthenticated v4 API calls. Multiple scraping write-ups (2023–2025) report the same block.
- No public free solver exists for Shopee's SPC_EC / session-token scheme.

---

## L2 Discovery — where does the data live, what did we hit?

**Fetch budget used: 4 of 5 allowed.**

| # | Tier | URL | HTTP | Outcome |
|---|------|-----|------|---------|
| 1 | Orchestrator probe | `GET /search?keyword=laptop` | 200 (157 kB SPA shell) | No `__NEXT_DATA__` / `__INITIAL_STATE__` — data not in raw HTML |
| 2 | Orchestrator probe | `GET /robots.txt` | 200 | `search?keyword=` is allowed; `Crawl-delay: 1` |
| 3 | Phase 0b API probe | `GET /api/v4/search/search_items?keyword=laptop...` | **403** | `{"is_login":false,"action_type":2,"error":90309999,"tracking_id":...}` — **application-layer block** |
| 4 | Phase 1 browser, homepage-warmed | `goto shopee.sg/` → `goto /search?keyword=laptop` | final_url: `/buyer/login?next=...` | **Silent redirect to login after navigation.** 224 XHRs fired; zero `search_items` calls succeeded. |

**Where the data lives (observed via XHR graph during browser run):**
- The SPA intends to call `https://shopee.sg/api/v4/search/search_items` with session cookies (`SPC_EC`, `SPC_F`, `SPC_ST`, `csrftoken`) populated by authenticated users. Without those cookies the server serves the login shell instead of mounting the search component, so that XHR is never issued.
- 22 other `/api/v4/…` endpoints DO return 200 (category tree, banners, search_suggestion, search_prefills) — these are anonymous-safe. The search-results endpoint itself is gated.

**No open alternative data surface:**
- No RSS / sitemap exposing search results (shopee.sg exposes category-sitemaps, not search).
- No documented public developer API for catalog search without merchant credentials.

---

## L3 Validation

N/A — zero rows extracted. Nothing to anchor, schema-check, or cross-source.

Negative validation (what we proved about the block):
- `action_type: 2` in the 403 body is Shopee's documented "enforce session login" action.
- The browser-tier `final_url` ends in `/buyer/login?fu_tracking_id=...&next=%2Fsearch%3Fkeyword%3Dlaptop`. That `fu_tracking_id` + `next=` redirect parameter is the classic R5 silent-redirect fingerprint.
- `xhr_log.json` shows `shopee.sg/api/v2/authentication/get_active_login_page` firing — further confirming the login flow is being activated before search can mount.

---

## L4 Scaling

Not applicable in a failed state. If Tier C were engaged, scaling would be:
- Rotate a **residential IP pool** (not datacenter — Shopee fingerprints ASN) per search query.
- Warm **session cookies with real login + 2FA** via a vendor that handles device-ID (SPC_DEVICE_ID) generation.
- Throttle to the observed polite rate (`Crawl-delay: 1`) and shard by category to stay under request-rate heuristics.
- Cache the search_items JSON by `(keyword, page, country)`; dedup by `itemid` across pages.

---

## L5 Persistence

| File | Bytes | Status |
|---|---|---|
| `page.html` | 157 513 | Empty SPA shell from first anonymous GET — no product data |
| `page_warmed.html` | 185 381 | Body at final login-redirect URL — proves silent redirect |
| `xhr_log.json` | ~33 kB | 224 entries from the browser run; `grep search_items` → 0 hits, `grep /login` → 4 hits |
| `findings.json` | ~1.2 kB | Structured probe outcomes |
| `result.json` | `[]` | **Empty by design — honest failure, no fabricated rows** |
| `result.csv` | header only | Same |
| `script.py` | — | Re-runnable; `python script.py` for Phase 0 only, `--browser` to also run Phase 1 |

---

## L6 Adversarial — the escalation ladder, rung-by-rung

| Rung | Technique | Result | Evidence |
|---|---|---|---|
| A | Plain HTTP GET with research-contact UA | 200 OK, 157 kB SPA shell, **no data in HTML** | `page.html`; 0 hits for `__NEXT_DATA__` / `__INITIAL_STATE__` / product markup |
| B | Documented v4 API GET with browser-like headers (`Referer`, `X-API-SOURCE: pc`) | **403** with `error: 90309999, is_login: false, action_type: 2` | `findings.json` phase0_api_probe |
| C | `Scrapling.StealthyFetcher` in headless mode | Tried (see D) — subsumed by homepage warming | — |
| D | Same, with **homepage-first warming** (R5 recommended last-free-rung) | Browser DOM resolves to `final_url = /buyer/login?next=/search?keyword=laptop` | `page_warmed.html`; xhr_log has 4 login XHRs, 0 `search_items` XHRs |
| E | curl_cffi TLS-fingerprint rotation | **Not attempted** — rung B shows the block is not at TLS/header layer; the API explicitly refuses anonymous sessions by app policy, not by bot fingerprinting |
| F | ISP/residential proxy rotation | **Not attempted in this round** — R9 already proved a clean SG residential IP does not clear this block; repeating would waste budget |
| G | Login-walled fetch with real credentials | **Ethically off-limits** — thesis rule: no login, no authentication, no user-data extraction |

### Failure classification

- **NOT** Cloudflare managed challenge — no `cf-mitigated`, no `cType`, no Turnstile.
- **NOT** DataDome — no `x-datadome` header, no "Please enable JS and disable any ad blocker".
- **NOT** Kasada — no `KPSDK`, no `ips.js`.
- **NOT** Akamai — no `akamai-grn`, no `server-timing: ak_p`.
- **IS** application-layer (session/device-bound). Server: `SGW`. Block is policy-enforced at the application layer — a logged-in session with a valid `SPC_EC` cookie + matching device-ID would succeed.

### Tier-C recommendation

Per thesis, the path forward is **paid infrastructure**:

1. **Vendor API** (fastest integration): Bright Data / Oxylabs / Scrapfly / ZenRows all publish Shopee-specific endpoints that maintain warmed session pools. Typical cost: $1–5 per 1 000 rows.
2. **In-house residential proxy + session automation**: $50–500 / mo residential egress + engineering time to generate and rotate `SPC_DEVICE_ID` / `SPC_EC` tokens. Significant build; only worth it at sustained high volume.
3. **Tier D (sanctioned)**: Shopee has no public partner API for external catalog search. The sanctioned path is a merchant relationship, not a crawl. If the research use case is academic, direct outreach to Shopee's data team is the honest ask.

**What free/local tools can still contribute** on Shopee: metadata-only public endpoints (`search_suggestion`, `search_prefills`, `category_tree`) are anonymous-safe and return useful data for query-space mapping. They are **not** a substitute for product listings.

---

## One-line verdict

> FAIL, 0/30 items, Phase 1 blocked by application-layer silent redirect to `/buyer/login`, matches thesis R5/R9 prediction exactly — Tier C required.
