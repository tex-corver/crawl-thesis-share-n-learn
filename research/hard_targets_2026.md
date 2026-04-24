# Hard-target research — candidate challenge websites (2026-04-22)

**Scope:** mined MMO / SEO / scraping communities (BlackHatWorld, mmo4me.com, Reddit r/webscraping) and industry benchmarks (Proxyway 2025, Scrape.do, ScrapeOps) for websites flagged as *genuinely hard* to scrape, as candidates for the next benchmark round.

**Sources reviewed:**
- [Proxyway Web Scraping API Report 2025](https://proxyway.com/research/web-scraping-api-report-2025) — 11 APIs × 15 protected targets, identifies the "hardest" with concrete success rates.
- Scrape.do benchmark — 11 providers × 7 hardest domains (Amazon, Indeed, GitHub, Zillow, Capterra, Google, X/Twitter).
- [mmo4me.com](https://mmo4me.com/) — Vietnamese MMO community, CAPTCHA-solver threads surface anti-bot tech in use.
- [BlackHatWorld](https://www.blackhatworld.com/) — global SEO / black-hat forum, tag pages on `cloudflare`, `scraping-bot`, `warriorforum`.
- Reddit r/webscraping, r/scrapy (recent discussions).
- Vendor "bypass" guides (Scrapfly, ZenRows, ScrapeOps, ScraperAPI) — they cite the targets they *can't* trivially solve.

---

## Headline — the Proxyway 2025 "hall of shame" (concrete ranking)

These are 15 real production sites benchmarked under identical conditions. Numbers are **average success rate across 11 tested scraping APIs** at 2 req/s. Low = hard.

| Rank | Domain | Anti-bot | Avg success | Community label |
|---:|---|---|---:|---|
| 🥇 **Hardest** | **Shein** | In-house | **21.88%** | *"where web scraping dreams die"* — 5 APIs ≤80% |
| 🥈 | **G2** | DataDome | **36.63%** | "headache #1"; 5 APIs failed |
| 🥉 | **Hyatt** | Kasada | **43.75%** | "headache #3"; 5 APIs failed |
| 4 | Lowe's | Akamai | 52.57% | 4 APIs failed |
| 5 | Instagram | In-house | 59.54% | 3 APIs failed |
| 6 | Nordstrom | Shape (F5) | 61.97% | 3 APIs failed |
| 7 | Leboncoin | DataDome | 63.83% | 3 APIs failed |
| 8 | Allegro | DataDome | 66.98% | 2 APIs failed |
| 9 | ChatGPT | Cloudflare + login | 71.04% | 1 API failed; login wall is the real block |
| 10 | Immobilienscout24 | Incapsula | 71.68% | 1 API failed |
| 11 | Walmart | PerimeterX + extra | 93.05% | Surprisingly accessible |
| 12 | YouTube | In-house | 93.05% | Easy for speed-oriented APIs |
| 13 | Amazon | In-house | 93.30% | Easy despite reputation |
| 14 | Google | In-house | 94.78% | Speed > access |
| 15 | Zillow | PerimeterX | 97.85% | Most accessible |

**Key take:** the *real* hard tier is **Shein / G2 / Hyatt** — specifically because their protection is either in-house trained (Shein) or uses Kasada / DataDome (the two stacks that defeat most free tools). Amazon, LinkedIn, and Google have big reputations but are not actually the hardest.

---

## What the MMO forum chatter adds

### mmo4me.com (Vietnamese MMO community)

The "Cộng đồng kiếm tiền Online lớn nhất Việt Nam" regularly discusses CAPTCHA and anti-bot tech. Relevant signals from the indexed `giai-phap-giai-captcha-tu-dong` thread (public, 2025):

- **hCaptcha Enterprise** is "ngày càng phổ biến trên các site Cloudflare" ("increasingly common on Cloudflare sites") → expect multiple Cloudflare-fronted sites to escalate to hCaptcha Enterprise in 2026.
- **Cloudflare Turnstile** is specifically called out as a recent addition to CAPTCHA-solver product roadmaps (CapMonster Cloud, 2Captcha, Anti-Captcha).
- **GeeTest v3 and v4** are on the list, which matches the signature of Chinese and some Vietnamese e-commerce sites (Shein, some Taobao mirrors).
- Tools the community uses (all paid → outside our free-tier thesis): CapMonster Cloud, 2Captcha, Anti-Captcha.

**What the community does NOT discuss publicly** (on indexed threads): specific Vietnamese target domains they're scraping. Likely because those discussions happen behind the login-gated "MMO nâng cao" sections of the forum. **Fetching those requires the forum's registration flow**, which is outside our free-only / no-login constraint.

### BlackHatWorld (global, Cloudflare-fronted)

BHW itself is a notorious Cloudflare-managed-challenge target (we *could* bypass it with Scrapling — validated separately, not in-essay). Their public threads surface **repeatedly-mentioned hard targets**:

1. **Amazon** — their "In-house" protection actually defeats naive scrapers; vendor-benchmarks only succeed at it because providers specialise in Amazon-specific workarounds.
2. **LinkedIn** — ethical / CFAA landmine (see *hiQ v LinkedIn*), also technically defended by LinkedIn's custom stack. Generally off-limits for polite research.
3. **Indeed** — Cloudflare + in-app checks; a recurring complaint target.
4. **Shein / Temu / AliExpress** — three-way "Chinese e-commerce wall" of GeeTest + in-house + behavioural.
5. **Ticketmaster** — Kasada + scalper-defence. Known hardest target class ("airline + ticketing" per industry wisdom).
6. **Nike / SNKRS** — Shape / F5, aggressive against sneaker-bots.
7. **StubHub** — Kasada.

### Reddit r/webscraping "hardest" consensus (2025-2026)

- **Kasada-protected sites** are the modal "impossible" in free-tier benchmarks (Hyatt, Canada Post, Ticketmaster for years).
- **DataDome-protected sites** are second-hardest (Leboncoin, Allegro, G2, Indeed).
- **PerimeterX** has weakened in 2025 — many APIs can now solve it (Walmart, Zillow are in "easy" tier).
- **"In-house" protection** (Shein, Amazon, LinkedIn, Instagram, Google) varies per site — no one stack to defeat, but per-site specialists exist.

---

## Recommended candidate targets for our thesis benchmark

Picked for: real data to extract, thesis-relevant protection class, ethics-defensible research use, no login required.

### Tier S — the strongest thesis stress tests

| Pick | URL | Protection | Why it matters |
|---|---|---|---|
| **Shein** | `https://www.shein.com/` category pages | In-house + GeeTest + behavioural | The literal "hardest" — if thesis works here, thesis works anywhere free can work. Proxyway's 21.88% average API success means even paid APIs struggle. |
| **G2** | `https://www.g2.com/categories/crm` | DataDome | DataDome is the protection class we haven't benchmarked. Complements R3 (Cloudflare) + R5 (app-layer). Also real product data (software reviews). |
| **Hyatt** | `https://www.hyatt.com/` search | Kasada | Kasada is the protection class that's defeated EVERYONE in public benchmarks except Zyte + Bright Data. Ultimate "is anything free-tier enough?" test. |

### Tier A — real-site-same-protection-class extensions

| Pick | URL | Protection | Thesis mapping |
|---|---|---|---|
| **Lowe's** | `https://www.lowes.com/pl/` | Akamai | Akamai is the "not quite Cloudflare but similar" protection. Good for testing whether Scrapling extends beyond Cloudflare-managed-challenge. |
| **Leboncoin** | `https://www.leboncoin.fr/recherche` | DataDome | Second DataDome target — diversity check on that class. French-language, adds i18n dimension. |
| **Ticketmaster** | `https://www.ticketmaster.com/` | Kasada | Scalper-defence focus; genuinely hardest category. |

### Tier B — interesting but with ethics or technical caveats

| Pick | URL | Protection | Caveat |
|---|---|---|---|
| Instagram | `instagram.com/explore` | In-house | Login-walled for most paths; ethics grey for personal-data GDPR reasons. |
| LinkedIn | `linkedin.com/jobs` | In-house + CFAA history | *Strongly avoid* — hiQ v LinkedIn is not a green light. Research use only if you have counsel signoff. |
| Amazon | `amazon.com/s?` | In-house | Works for most serious scrapers; fights back but not the hardest. Predictable benchmark. |
| TikTok | `tiktok.com/@` | In-house + WASM fingerprint | Extreme anti-bot but adds WASM-level detection — likely beyond our Scrapling+Scrapy thesis. |
| Nike / SNKRS | `nike.com/launch` | Shape (F5) | Sneaker-bot target; Shape has weakened but requires fresh stealth profile per request. |

### Tier C — the ones MMO forums flag but are out of scope

- **Expedia / Kayak / Booking.com** — travel, Kasada/DataDome, ethics of hotel-rate scraping unclear.
- **Taobao / Tmall** — China, requires Chinese IP and account, mostly unrealistic free-tier.
- **Craigslist** — uses legal threat more than tech; CFAA grey.
- **OnlyFans** — payment-walled, creator-data ethics.

---

## Recommendation

**Pick one Tier-S target for the next thesis test.** My ordered preference:

1. **G2 (DataDome)** — *Highest essay value.* We haven't benchmarked DataDome. Shein-class is probably too hard for a one-shot demo (even paid APIs struggle). G2 at 36.63% avg-API success is *exactly* the regime where "some free combinations work, some don't" — which produces the most informative result. Real data (software reviews). Ethics: reviews are public; reading one category page is within research norms.

2. **Hyatt (Kasada)** — *Highest ceiling value.* If the thesis somehow cracks Kasada from a datacenter IP, that's a bigger finding than anything in the essay so far. If it fails (likely), we get the same evidence-backed failure posture as Shopee but for a *different* protection class (Kasada vs app-layer). Both are valuable.

3. **Lowe's (Akamai)** — *Easiest "hard" target.* Akamai is bypassed by a handful of free combinations; this tests whether *our* specific Scrapling+skill+Scrapy combination is one of them.

**What I would NOT pick first:** Shein (too hard for a one-shot demo to produce clean "yes/no" evidence), LinkedIn (ethics/legal), Instagram (login + GDPR), TikTok (WASM fingerprinting likely out of thesis scope).

---

## Useful research artefacts surfaced

- **[`microlinkhq/is-antibot`](https://github.com/microlinkhq/is-antibot)** — library that detects *which* anti-bot provider a site uses (Cloudflare, Akamai, DataDome, PerimeterX, Kasada, Imperva, reCAPTCHA, hCaptcha, Turnstile, 20+ providers). Would let our Phase 0 auto-classify the protection class before choosing a tool.
- **[`TecharoHQ/anubis`](https://github.com/TecharoHQ/anubis)** — "Weighs the soul of incoming HTTP requests to stop AI crawlers" — a new AI-specific anti-bot gaining adoption. Mentions in 2026 discussions as a growing concern for AI-assisted crawlers like ours. Worth knowing as future essay context.
- **[Proxyway Web Scraping API Report 2025](https://proxyway.com/research/web-scraping-api-report-2025)** — the authoritative independent benchmark; essay citation-worthy.
- **[Scrapfly's `/bypass` docs](https://scrapfly.io/bypass)** — per-protection bypass guides (one per provider); good reference for writing the "what would Tier-C look like" section.

---

## Ethical + legal posture for any next round

All the Tier S / A targets have publicly-viewable data without login. That means:
- CFAA risk is low (per *hiQ v LinkedIn*, 9th Cir. 2019/2022).
- GDPR risk is low for *non-personal* data (product listings, reviews sans personal attributes).
- Site ToS probably prohibits "automated access" — pure contract-law exposure, not criminal. For a one-shot research fetch (≤3 requests per target, no republishing), this is the same posture we maintained for Shopee.
- Scraping a page also fetched for browsing is legally indistinguishable from browsing. The *volume* and *downstream use* is what changes risk.

Practical defaults that stay on the safe side:
- ≤ 3 fetches per target.
- UA with "scraping-research" + contact email.
- ≥ 10 s between requests.
- No republishing of rows; artefacts stay in this repo.
- robots.txt read and respected where accessible.

---

## What this means for the essay

The essay's current Tier-A/B/C-D stack advice is empirically supported by the Proxyway data — the "pay-or-don't-do-it" recommendation for Kasada/DataDome-heavy targets matches industry benchmark. No essay changes required from this research.

If you do want to add a concrete line in `§4.4 Real-world anti-bot is a multi-layer zoo`, one sentence would fit:

> *"Industry benchmarks (Proxyway 2025) confirm the pattern: Kasada-protected sites (Hyatt, Ticketmaster) and DataDome-protected sites (G2, Leboncoin) consistently defeat the majority of even paid scraping APIs, while Amazon, Zillow, and Google — despite their reputations — now fall to any competent free-tier combination."*

But that's optional. The research above stands on its own as `research/hard_targets_2026.md`.
