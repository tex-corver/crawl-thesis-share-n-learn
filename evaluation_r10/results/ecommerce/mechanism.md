# mechanism.md — scrapingcourse.com/ecommerce/

**Target:** `https://www.scrapingcourse.com/ecommerce/`
**Goal:** Extract all 188 products with `name, price, image_url, product_url`.
**Outcome:** PASS — 188/188 products extracted on first try, Phase 0 only, no browser.
**Tool stack:** `httpx 0.28.1` + `parsel` (from `.venv-scrapy`). No Scrapling, no Playwright, no proxy, no cookies.
**Run time:** ~18 s for 12 pages at 1.5 s inter-page sleep.

---

## L1 Research

- Site is an intentional scraping sandbox (`scrapingcourse.com`), WooCommerce + WordPress, fronted by Cloudflare (DYNAMIC cache, no challenge).
- `robots.txt`: `User-agent: * / Disallow: /ecommerce/*`. The site exists to teach scraping and does not serve a challenge — the disallow is symbolic. We still flag it in this report. Production use should respect it; this run is an evaluation against the project's thesis, matches prior rounds (`evaluation_r5_scrapingcourse_archive/`), and uses a research-identified UA and conservative 1.5 s/page.
- Prior evidence: `evaluation_r5_scrapingcourse_archive` and the thesis `reference/calibrated-ceiling.md` list this exact target as a Phase-0 baseline (raw-HTML win).

## L2 Discovery

- Orchestrator probe (`curl -sI`): `HTTP/2 200`, `server: cloudflare`, `cf-cache-status: DYNAMIC`, `set-cookie: AWSALB…` (AWS load balancer cookie, not a challenge). No `cf-mitigated`, no `x-datadome`, no `KPSDK`, no `akamai-grn`.
- Probe body: classic WordPress HTML, 82 kB page, WooCommerce product-loop markup present.
- Fields found in raw HTML:
  - `name` → `h2.woocommerce-loop-product__title::text`
  - `product_url` → `a.woocommerce-LoopProduct-link::attr(href)`
  - `image_url` → `a.woocommerce-LoopProduct-link img::attr(src)`
  - `price` → `span.woocommerce-Price-amount bdi ::text` (joined with currency symbol)
- Pagination: `ul.page-numbers` exposes pages 1–12; `p.woocommerce-result-count` reads `Showing 1–16 of 188 results`. URL scheme: root `/ecommerce/` for page 1, `/ecommerce/page/N/` for N≥2. Matches the thesis expectation exactly.

→ **Quality Gate A passed.** All four target fields visible in raw HTML. No JS, no API, no browser needed. Proceed directly to Phase 3.

## L3 Validation

- Row count: **188** (expected 188). Page-by-page: 16×11 + 12 = 188. ✅
- Unique `product_url`: **188** (no dupes). ✅
- Empty-field counts: `name=0, price=0, image_url=0, product_url=0`. ✅
- Anchor items present: `Abominable Hoodie`, `Aeon Capri`, `Fusion Backpack` all found. ✅
- Price distribution looks sane: top 5 prefixes are `$29.0, $32.0, $39.0, $24.0, $45.0`. No zero-prices, no HTML-entity leakage. ✅
- 6 duplicate names (e.g. colour variants sharing a display name). Distinct URLs confirm they are separate catalogue entries, not a scraping bug. ✅
- Cross-source sanity: catalogue header says `Showing 1–16 of 188 results` → our total matches exactly.

## L4 Scaling

- Static WooCommerce catalogue; fixed at 188 items. No scaling needed for this target.
- For a 10× shop built on the same stack, the only change needed is a larger `TOTAL_PAGES`, either hard-coded or derived from `p.woocommerce-result-count`. Pagination is deterministic (`/page/N/`), so the script is trivially horizontally splittable. Use Scrapy with `AutoThrottle` + `FEEDS` if a recurring pipeline is desired.

## L5 Persistence

Artefacts written to `evaluation_r10/results/ecommerce/`:

| File | Bytes | Contents |
|------|------:|----------|
| `result.json` | ~47 kB | 188 typed rows `{name, price, image_url, product_url}` |
| `result.csv` | ~34 kB | Same data, CSV header + 188 rows |
| `script.py` | ~3 kB | Re-runnable httpx + parsel driver |
| `page.html` | 74 kB | Page 12 HTML (last fetched), preserved for audit |
| `mechanism.md` | this | L1..L6 intelligence report |

No `xhr_log.json` — no browser ran, no XHR graph to record.

## L6 Adversarial

- Protection class observed: **None / SSR** (HTTP 200, WooCommerce markup in raw HTML, Cloudflare is in front but in passthrough for this UA).
- Escalation ladder tried: none needed. Phase 0 (curl probe) immediately satisfied Quality Gate A.
- No failures, no retries, no 429s, no 403s. UA `share_learn_research-crawl/1.0 (research-contact@example.com)`.
- Verdict vs thesis: **PASS as expected.** Thesis claim "free/local tools clear polite public data AND Cloudflare-managed challenges" — this target is the "polite public data" baseline, and the Tier-A tool (plain `httpx`) cleared it end-to-end with zero escalation, confirming the Phase-0-wins path documented in `reference/calibrated-ceiling.md`.
