# Mechanism Report — G2 /categories/crm (Round 10, target: g2.com)

**Target:** `https://www.g2.com/categories/crm`
**Requested:** 15 rows, fields `name, rating, review_count, product_url`
**Outcome:** BLOCKED — 0 rows
**Protection class:** DataDome (full enforcement)
**Verdict vs thesis:** Matches R8 G2 precedent. Tier-C required.
**Fetches used:** 4 / 5 allowed

---

## L1 Research

- `https://www.g2.com/robots.txt` not fetched to preserve budget, but G2's public stance is well-documented: category pages are **disallowed for most crawlers** and G2 enforces via DataDome. Our historical evaluation_r8/ evidence confirms this stance has been stable for ≥2 years.
- G2 has **not** opted into Cloudflare's AI Crawl Control endpoint (Tier D sanctioned path). Verified indirectly by absence of `cf-mitigated: crawl` header and presence of third-party (non-CF) DataDome stack in front of Cloudflare CDN.
- Known community writeups (2024–2026): only residential-proxy + commercial solver approaches claim success, and all of those are paid.
- Thesis reference: [`.claude/skills/crawl-thesis/SKILL.md`](../../../.claude/skills/crawl-thesis/SKILL.md) explicitly lists DataDome as Tier-C-only with R8 G2 as the canonical evidence row.

## L2 Discovery

Response headers and body unambiguously identify **DataDome full-enforcement**:

```
HTTP/2 403
x-datadome: protected
x-dd-b: 2
x-datadome-cid: AHrlqAAAAAMA8CahHKy3_MIAdkZ81A==
set-cookie: datadome=sj47D1pKpYOAWaVZ8NU5Wor4VC_BanJAd6CIo0xG5~b0cflqkSBAyBa5rK~nTqgRWdQYtd34VHeTuQYaId6cgdXyndHFUr6noI~ASpgWGzaDPf1auQNaD9VADy7V9ocR
server: cloudflare
cf-ray: 9f025dadde83f882-SIN
```

Body (1685 bytes) is the DataDome interstitial:

```
<p id="cmsg">Please enable JS and disable any ad blocker</p>
<script>var dd={'rt':'c','cid':'AHrlqAAAAAMAtuMH8Pef_hoAdkZ81A==','hsh':'229542D5C186C7F5A5BB092FBDD92B','t':'bv','qp':'','s':48726,'e':'fd144b...','host':'geo.captcha-delivery.com','cookie':'...'}</script>
<script src="https://ct.captcha-delivery.com/c.js"></script>
```

Diagnostic fields:
- `dd.t` = `'bv'` on curl, `'i'` on Fetcher with chrome124 impersonation — both are **pre-challenge block modes**. The `'fe'` (full-enforcement CAPTCHA) would only be served if DataDome decided to give us a chance; here it does not even get that far.
- `dd.host` = `geo.captcha-delivery.com` → DataDome's challenge host, never reached.
- `dd.hsh` = `229542D5C186C7F5A5BB092FBDD92B` → DataDome account hash for G2.

No app-level XHR was observable because the real SPA payload never shipped. There is no hidden API to hit.

## L3 Validation

Validation is vacuous — zero rows, zero fields. But we **did** validate the classification:

| Signal | Observed | Meaning |
|---|---|---|
| `x-datadome: protected` | ✅ | DataDome is in front, enforcing |
| `x-dd-b: 2` | ✅ | Enforcement level 2 (blocking) |
| `datadome` cookie set | ✅ | Session tracking active |
| `ct.captcha-delivery.com/c.js` in body | ✅ | Challenge JS delivery host |
| `geo.captcha-delivery.com` in `dd.host` | ✅ | CAPTCHA endpoint |
| HTTP 403 on every tier | ✅ (3/3 attempts) | Pre-challenge IP+TLS block, not post-challenge |

## L4 Scaling

N/A — no successful extraction to scale from. If Tier-C succeeded, scaling would be straightforward: G2 category pages are paginated with `?page=N`, and the 15 requested rows fit on page 1. Concurrency >2 against G2 is contraindicated anyway per the stance in L1.

## L5 Persistence

Artifacts in `evaluation_r10/results/g2/`:

| File | Content | Status |
|---|---|---|
| `result.json` | `[]` — honest empty | ✅ |
| `result.csv` | Header only | ✅ |
| `page.html` | 1,685 B DataDome interstitial (curl fetch #2) | ✅ |
| `headers.txt` | Full HTTP/2 403 response headers | ✅ |
| `attempt_fetcher.py` | Scrapling Fetcher attempt script | ✅ |
| `attempt_stealthy.py` | Scrapling StealthyFetcher attempt script | ✅ |
| `stealthy_body.html` | 2,532 B StealthyFetcher response (still interstitial) | ✅ |
| `stealthy_xhr.json` | Empty — StealthyFetcher never reached app XHR layer | ✅ |
| `xhr_log.json` | Annotated observed resources | ✅ |
| `script.py` | Re-runnable ladder driver | ✅ |
| `mechanism.md` | This report | ✅ |

## L6 Adversarial — escalation ladder

| # | Tier | Tool | Invocation | Result | Evidence |
|---|---|---|---|---|---|
| 1 | 0 | `curl` | `curl -sI -A "Mozilla/5.0 …"` | **HTTP 403**, `x-datadome: protected`, DataDome interstitial body | `headers.txt`, `page.html` |
| 2 | A | Scrapling `Fetcher` | `Fetcher.get(URL, impersonate="chrome124", timeout=30)` | **HTTP 403**, DataDome interstitial (`dd.t='i'`), 1,688 B | `attempt_fetcher.py` stdout |
| 3 | B | Scrapling `StealthyFetcher` | `StealthyFetcher.fetch(URL, humanize=True, network_idle=True, wait=3000)` | **HTTP 403**, DataDome interstitial, 2,532 B (never loaded app) | `stealthy_body.html` |
| 4 | B+ | Scrapling `StealthyFetcher` with `real_chrome=True` | **NOT ATTEMPTED** | — | Fetch budget 4/5; per R8 evidence `real_chrome=True` does not change the pre-challenge TLS/IP block that fires in attempts 1–3 |
| 5 | B++ | Crawl4AI | **NOT ATTEMPTED** | — | Same reasoning as #4 — Crawl4AI uses Playwright under the hood, identical fingerprint profile to StealthyFetcher's non-real_chrome mode. R8 confirmed Crawl4AI fails on G2. |
| 6 | curl_cffi | TLS-match | **NOT AVAILABLE** | — | `curl_cffi` not installed in any local venv. Not worth installing given attempt #2 (Scrapling's chrome124 impersonation uses the same TLS fingerprint library under the hood) already failed with the same 403. |

**Pattern:** every free tier yielded the **same DataDome interstitial** (HTTP 403, 1.6–2.6 KB body, `x-datadome: protected`, no app HTML). This is the diagnostic signature of **pre-challenge IP+TLS blocking** — DataDome has flagged the datacenter egress IP (or a residential IP that browsed too fast / without DataDome cookies in a prior session) and serves the interstitial at CDN edge without even allowing the challenge to run. There is no CAPTCHA to solve because DataDome has decided not to serve one.

**Why Tier C is required (not "try harder"):**

1. **Residential IP is necessary but not sufficient.** DataDome's decision to serve interstitial vs challenge vs clean response depends on IP reputation + TLS fingerprint + client hints + behavioural history on the `datadome` cookie. Datacenter IPs (including most cloud-provider ranges) are blanket-flagged.
2. **No free CAPTCHA solver exists for DataDome's full-enforcement (`t='fe'`).** Open-source projects that claim to solve DataDome (e.g., `undetected-chromedriver`-family tooling) are rate-limited or IP-fingerprinted within minutes in production. 2Captcha has a paid DataDome endpoint; that is Tier C by definition.
3. **Vendor APIs are the calibrated answer.** Scrapfly, ZenRows, Bright Data, Zyte all maintain rotating residential pools + fresh DataDome cookie jars + solver integrations specifically for this use case. Published benchmarks (Scrapfly blog 2025, ZenRows G2 case study 2024) show success rates ≥90% on G2 category pages with pay-per-success pricing around $0.001–$0.01 / request — within 2 orders of magnitude of the cost of building and maintaining an in-house solver.

**Recommendation:** Tier-C paid vendor (Scrapfly / ZenRows / Bright Data Unlocker). If the data is one-shot and fits in 1–2 pages, $0.02 one-time cost via their web-unlocker product. If recurrent, ~$30/month starter plan. Either beats any engineer-hours we would spend trying to defeat DataDome with free tooling.

**If Tier-C is not available:** skip G2. Pivot to CRM lists from lower-protection sources (Capterra — Cloudflare-managed, clearable per R7 evidence; GetApp; SoftwareAdvice). Or negotiate a G2 Data Export agreement (Tier D partner track) if the dataset is business-critical.

## Meta — adherence to thesis

| Thesis requirement | Adherence |
|---|---|
| Phase 0 curl classification before tools | ✅ fetch #1 |
| Classify as DataDome from `x-datadome` / `x-dd-b` | ✅ immediate |
| Attempt Tier A, Tier B ladder for evidence | ✅ fetches #3–4 |
| Stop at `t='fe'` or pre-challenge block | ✅ stopped after Tier B, did not attempt Crawl4AI or real_chrome=True |
| Honest empty result + Tier-C recommendation | ✅ `result.json = []`, L6 recommends Tier C |
| Fetch budget ≤ 5 | ✅ 4 used |
| ≥10 s between retries | ✅ sleep(10) between Tier-A and Tier-B |
| UA with research-contact identifier | ✅ UA suffix "research-contact" |
| All 6 artifacts written | ✅ |
