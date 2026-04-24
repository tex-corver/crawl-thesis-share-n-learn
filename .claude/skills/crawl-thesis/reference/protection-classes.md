# Protection classes — diagnostic signatures + escalation ladders

**Use this when** your Phase 0 curl probe returns something other than the data you wanted. Identify the class → apply the matching ladder → stop at the first success OR the first Tier-C line.

---

## Class 1 — No anti-bot

**Signature:** HTTP 200, target data visible in raw HTML response body.

**Ladder:** None needed. Parse HTML or call the public API directly. Use Scrapy if recurrent.

**Evidence:** Round 1 (CMC), Round 2 (Binance), Round 4 (sandbox ecomm), Round 6 (Substack).

---

## Class 2 — JS rendering (SPA, no anti-bot)

**Signature:** HTTP 200, but response body is an empty SPA shell (no target data). Often contains references to `_next/`, `/assets/`, etc.

**Ladder:**

```
Tier A.1  Check for __NEXT_DATA__ / __APP_DATA__ inline scripts in the HTML
          → if present, parse that JSON directly. No browser needed.

Tier A.2  Check for documented public APIs (/api/, /feed, /rss, sitemap.xml)
          → call them directly.

Tier B.1  Scrapling.DynamicFetcher (plain Playwright) with network_idle=True.
          Subscribe to page.on('request'/'response') BEFORE navigation to
          capture XHRs.

Tier B.2  If internal XHRs surface a clean JSON endpoint, replay them
          directly (downgrade to plain HTTP for scaled fetching).
```

**Evidence:** Round 2 (Binance) used Tier A.1 — `__APP_DATA__` blob. Round 4 (sandbox ecomm) used Tier A.1 — raw HTML with product markup.

---

## Class 3 — Cloudflare managed challenge / Turnstile ✓ PASSES free tier

**Signature:**
- HTTP 403 (or 503)
- Response headers: `server: cloudflare`, `cf-mitigated: challenge`
- Response body: `<title>Just a moment...</title>`, `_cf_chl_opt`, `challenges.cloudflare.com` in CSP
- The challenge script URL contains `cType: 'managed'` or `cType: 'interactive'`

**Ladder:**

```
Tier A.1  curl the /cdn-cgi/... challenge URL directly
          → typically returns 403; no path here for plain HTTP.

Tier B.1  Scrapling.StealthyFetcher(url, solve_cloudflare=True,
                                    humanize=True, real_chrome=True,
                                    network_idle=True)
          ✓ PROVEN at R5-v1 sandbox (scrapingcourse/cloudflare-challenge)
          ✓ PROVEN at R7 real production (BlackHatWorld MMO forum)
          ~20 s solve time. Rotate proxy if this particular IP has been flagged.

Tier B.2  If B.1 hangs: try headed mode under Xvfb
          (rare; only if Cloudflare's "attack mode" is active).

Tier C   If nothing works and IP is the gating factor:
         rotate to a fresh residential proxy.
         Real residential > datacenter-ISP proxies (R9 evidence).
```

**Evidence:** R5-v1 sandbox + R7 BlackHatWorld. Same ~20 s solve both times — sandbox trick transfers to real production.

---

## Class 4 — DataDome ✗ FAILS free tier

**Signature:**
- HTTP 403 (pre-challenge) or 200 with DataDome interstitial
- Response headers: `x-dd-b: 1` or `2`, `x-datadome: protected`, `x-datadome-cid: ...`
- Response body: `<p id="cmsg">Please enable JS and disable any ad blocker</p>`
- Or the full DataDome CAPTCHA iframe from `geo.captcha-delivery.com`

**Ladder:**

```
Tier A.1  Fetcher.get(url, impersonate="chrome")
          → 403 with x-dd-b: 1 (edge-level pre-challenge block).
          Free TLS impersonation alone is insufficient.

Tier B.1  StealthyFetcher(url, humanize=True)
          → 403 with CAPTCHA iframe (t=fe full enforcement).
          Camoufox fingerprint-masking hides WebDriver but DataDome's
          signal is higher-level (TLS/JA3 + mouse behaviour + proxy ASN).

Tier B.2  nodriver + proxy
          → same CAPTCHA iframe served. nodriver's raw-CDP doesn't help
          where DataDome's decision is NOT WebDriver-based.

Tier C   Escalate. DataDome's full-enforcement CAPTCHA requires either:
         - Paid vendor API (Scrapfly / ZenRows / Bright Data) that bundles
           a CAPTCHA-solver backend.
         - Residential proxy + 2Captcha/CapSolver (≥$100/mo infrastructure).
```

**Evidence:** R8 G2, R9 G2 retest with proxy (proxy flips edge-block → JS challenge, still can't solve).

---

## Class 5 — Kasada v3 ✗ FAILS free tier (no solver exists)

**Signature:**
- HTTP 429 (with Kasada challenge) or HTTP 403 (edge-reject)
- Response body: `window.KPSDK={}`, `<script src="/{UUID}/2d206a39-.../ips.js?...&x-kpsdk-im=AAIk..."></script>`
- Kasada is often layered on Akamai: `server-timing: ak_p` + Kasada shell

**Ladder:**

```
Tier A.1  Fetcher.get(url, impersonate="chrome") → 429 with Kasada shell.

Tier B.1  DynamicFetcher → 429 with Kasada ips.js challenge.
Tier B.2  StealthyFetcher(humanize=True) → 429, Kasada doesn't auto-solve.

Tier C   IMMEDIATE. Kasada v3 requires x-kpsdk-ct / x-kpsdk-cd tokens minted
         by solving their proprietary POW challenge. No open-source solver
         exists anywhere as of 2026-04-22. Only Zyte / Oxylabs / Bright Data
         have verified Kasada bypass.
```

**Evidence:** R8 Hyatt — 4 tiers tried, all blocked at Kasada POW.

---

## Class 6 — Akamai Bot Manager (mixed — sometimes free tier works)

**Signature:**
- HTTP 403 with "Access Denied" HTML (~450 B block page)
- Response headers: `akamai-grn: 0.*`, `server-timing: ak_p; desc="..."`
- Or HTTP 200 with a 2.5 KB JS sensor page (path like `/SZrnEFaAqVDtZY6zWkp5/.../sensor_data`)
- `_abck` cookie challenge

**Ladder:**

```
Tier A.1  curl_cffi with varied profiles — try ALL of these:
          for profile in ["chrome131", "chrome120", "safari18_0", "firefox135"]:
              r = curl_cffi.get(url, impersonate=profile)
          Some targets pass one profile but fail others. R8 Lowe's evidence:
          safari18_0 got HTTP 200 (with sensor, not products).

Tier A.2  curl_cffi + Referer: https://www.google.com/
          Akamai sometimes whitelists Google-originated traffic.

Tier A.3  Scrapling.Fetcher with impersonate profile variants.

Tier B.1  DynamicFetcher / StealthyFetcher / Crawl4AI — tested on R8 Lowe's,
          ALL detected pre-sensor by Akamai's fingerprint layer.

Tier C   If Tier A returns 200 with a sensor page instead of products:
         - residential proxy (Akamai ASN-reputation-sensitive)
         - OR vendor API with Akamai-aware unblocker
         - OR hand-tuned Chrome with aged profile + residential egress
           (engineering-heavy)
```

**Evidence:** R8 Lowe's — curl_cffi firefox135 returned sensor challenge (HTTP 200, 2.5 KB) but no products. Browser tiers all fingerprinted. R9 retest with proxy actually made it WORSE (proxy ASN on Akamai's bad list).

---

## Class 7 — Application-layer (Shopee-class) ✗ FAILS free tier

**Signature:**
- HTTP 200 (everything looks fine)
- But page silently redirects to `/login` or `/buyer/login` or `/captcha`
- Target URL hydrates but internal XHRs return site-specific bot codes
  (Shopee: `{"error": 90309999}`, others may differ)
- Often accompanied by fingerprint-telemetry exfil endpoints
  (Shopee: `df.infra.shopee.sg/v2/shpsec/web/report`)

**Ladder:**

```
Tier B.1  Homepage-first navigation to warm session cookies:
          browser.goto("https://" + domain + "/")
          # wait for network-idle, collect all cookies
          browser.goto(target_url)  # in same context
          # subscribe to XHR capture BEFORE each goto

Tier B.2  With warm cookies, replay the observed XHR directly with curl:
          curl --cookie-jar cookies.txt ... \
               -H "x-csrftoken: $(grep csrftoken cookies.txt | awk '{print $7}')" \
               $observed_api_url

Tier C   If Tier B.1-B.2 still returns the bot code (R5 Shopee evidence:
         all 3 Scrapling tiers + 14 warm cookies + CSRF + full Sec-Fetch-*
         returned HTTP 403 + error 90309999), the block is at IP-reputation
         + device-fingerprint-telemetry layers. Free tools genuinely cannot
         clear this. Options:
         - Residential proxy + rotating device fingerprint SDK (engineering-heavy)
         - Vendor partner API (if target offers one)
         - Paid API (Scrapfly etc., which handle session warmth + residential)
```

**Evidence:** R5 Shopee (2 attempts incl. thesis-faithful with 62 XHR capture), R9 Shopee retest with ISP proxy (helped homepage, search still blocked).

---

## Class 8 — Authentication required (login wall)

**Signature:** 401, or 302 → login page, or page contains only "Please sign in..." content.

**Ladder:**

```
Tier A   STOP. This thesis is public-data-only by design.
         Login brings CFAA, GDPR, ToS exposure into scope.
         If the data is business-critical, negotiate a partner API with the
         target rather than automating login.
```

**Evidence:** We deliberately did not test any R5+ target that requires login. See the essay's §1.4 legal primer.

---

## Class 9 — Hybrid / stacked (multiple protections)

Common stacks:
- **Akamai + Kasada** (Hyatt) — Akamai decides whether to serve Kasada
- **Cloudflare + DataDome** (G2 in some configurations) — CF edge + DD at app layer
- **Cloudflare + rate limiting** (many SaaS products)

**Ladder:**
1. Identify the outer (reverse-proxy-visible) protection first.
2. Solve it.
3. THEN re-probe and identify the inner protection.
4. Apply the matching ladder.

The outer layer's behaviour often determines whether you see the inner challenge at all.

---

## The binary rule of thumb

| Gate | Can the free thesis clear it? |
|---|---|
| No anti-bot | ✅ Yes — trivially |
| JS rendering only | ✅ Yes — Playwright/Scrapling |
| Cloudflare Turnstile / managed | ✅ Yes — Scrapling `solve_cloudflare=True` |
| Rate limiting | ✅ Yes — Scrapy AutoThrottle + RETRY |
| **DataDome** | ❌ No — Tier C |
| **Kasada** | ❌ No — Tier C (no solver exists) |
| **Akamai** | ⚠️ Sometimes — curl_cffi profiles, often Tier C |
| **Application-layer** | ❌ No — Tier C |
| **Hybrid of above with any ❌** | ❌ No — Tier C |

Nine rounds of evidence. The boundary is stable.
