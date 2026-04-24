---
name: crawl-thesis
description: Apply the share_learn_research crawling thesis — a calibrated, evidence-backed (9 benchmark rounds) methodology for web crawling in 2026. Activates when user asks to "crawl", "scrape", or "extract data from [URL]". Combines the web-scraper skill's phased reconnaissance with our Scrapy + Scrapling + curl_cffi tool stack and honest Tier-A/B/C/D escalation per protection class. Use this skill FIRST for any crawl task; it points to web-scraper for deeper phase-by-phase tactics.
license: MIT
---

# Crawl Thesis — a calibrated, 9-round-validated approach

**Use this skill whenever the user asks to crawl, scrape, or extract data from a URL.** It encodes *our project's* calibrated ceiling, not generic marketing. The underlying phased methodology comes from the companion `web-scraper` skill (see [`../web-scraper/SKILL.md`](../web-scraper/SKILL.md)); this skill tells you *which phases to actually run, with which tools, for which protection class, and when to stop and recommend paid Tier C.*

---

## The thesis in one sentence

> **Free/local tools clear everything up to Cloudflare-managed challenges. DataDome / Kasada / Akamai / application-layer require paid Tier-C infrastructure. Evidence: 9 rounds in `evaluation_r*/scorecard.md`.**

---

## The four layers (what this thesis composes)

1. **Methodology** — phased reconnaissance from the `web-scraper` skill (6 phases + quality gates).
2. **Framework** — `Scrapy 2.15` at `.venv-scrapy/`, with `ROBOTSTXT_OBEY`, `AUTOTHROTTLE`, `FEEDS`, `Items`, `Pipelines` as defaults.
3. **Specialty tools** — right instrument per protection class (see §"Protection-class escalation ladder" below).
4. **LLM orchestration** — Claude runs the loop: reason → probe → decide → act → validate → document.

---

## The workflow — non-negotiable order

### Phase 0 — curl probe (≤ 60 s, no browser)

```bash
curl -sI -A "Mozilla/5.0" "<target>"        # headers — what protection?
curl -s  -A "Mozilla/5.0" "<target>" | head -c 2000    # body — what's there?
curl -s  "<target>/robots.txt"              # politeness baseline
```

**Classify the protection class** from the response (see `reference/protection-classes.md`):

| Signal in response | Class | Can we clear it? |
|---|---|---|
| HTTP 200, `__NEXT_DATA__` / `__APP_DATA__` in HTML | None / SSR | ✅ Trivial — skip to Phase 3 |
| HTTP 200, documented `/api/` / `/feed` / `/rss` | Open API | ✅ Trivial — skip to Phase 3 |
| HTTP 200, SPA shell, empty of data | Needs-JS | ⚠️ Use browser tier |
| `cf-mitigated: challenge`, `cType: managed`, "Just a moment..." | **Cloudflare managed** | ✅ Scrapling `solve_cloudflare=True` clears it (R5-v1 + R7 evidence) |
| `x-datadome`, "Please enable JS and disable any ad blocker" | **DataDome** | ❌ Tier-C only (no free solver) |
| `window.KPSDK`, `/*/ips.js` | **Kasada** | ❌ Tier-C only (no free POW solver) |
| `akamai-grn`, `server-timing: ak_p`, "Access Denied" | **Akamai Bot Manager** | ❌ Tier-C only |
| HTTP 200 but redirects silently to `/login` or similar | **Application-layer** (session/device) | ❌ Tier-C only |

### Quality Gate A (the critical one)

- **All target fields visible in raw HTML?** → skip Phase 1/2, go directly to Phase 3 with plain HTTP + `Scrapy` or `httpx`.
- **Documented public API surfaces the fields?** → same.
- **Otherwise** → continue to Phase 1.

*This gate saves ~80% of the work on polite sites. Round 4 + Round 6 evidence: Phase 0 alone was sufficient, no browser needed.*

### Phase 1 — browser recon (only if Gate A fails)

Use the correct tool **for the observed protection class** (see `reference/tool-stack.md`):

- No anti-bot / needs-JS → `Scrapling.DynamicFetcher` (plain Playwright)
- **Cloudflare managed** → `Scrapling.StealthyFetcher(solve_cloudflare=True, humanize=True, real_chrome=True)` — **proven at R5-v1 sandbox + R7 BlackHatWorld production**
- Any case with aggressive anti-bot → **homepage-first navigation** in the same browser context to warm session cookies, THEN navigate to the target URL

Subscribe to `page.on('request')` / `page.on('response')` **before** navigation to capture the XHR graph.

### Phase 2 — interactive exploration (only if Phase 1 insufficient)

Scroll, click "load more", trigger lazy XHRs. Log new endpoints surfaced.

### Phase 3 — extract + validate (always run)

- Row count meets target (or document why less)
- All required fields non-empty
- Anchor check — a known item appears (e.g. `BTC` in a crypto list, `Lenovo` in laptops)
- Unique primary keys
- Cross-source sanity check if available (RSS vs API, two XHR endpoints, etc.)

### Phase 4 — honest escalation when truly blocked

**DO NOT keep flailing.** Map the observed failure mode to the right response:

| Failure mode | Right next step |
|---|---|
| Still "Just a moment..." after Scrapling StealthyFetcher | Rotate to fresh proxy IP or accept: this particular IP is too flagged. |
| DataDome CAPTCHA served (`t=fe`) | **Stop.** Free tools cannot solve DataDome's full-enforcement CAPTCHA. Recommend Tier C. |
| Kasada `ips.js` challenge | **Stop.** No free POW solver exists for Kasada v3. Recommend Tier C. |
| Akamai "Access Denied" / `_abck` sensor challenge | Try `curl_cffi` with `safari18_0`/`firefox135` profile first. If still blocked, Tier C. |
| Silent redirect to `/login` or similar | Homepage-first warming. If still blocked (R5 Shopee evidence), app-layer — Tier C. |
| HTTP 429 / persistent rate limit | Scrapy `AUTOTHROTTLE` + `RETRY_TIMES=3` with exponential backoff. |

### Phase 5 — produce the intelligence report (mechanism.md)

ALWAYS write a `mechanism.md` with these 6 sections:

- `## L1 Research` — robots.txt + docs + known writeups
- `## L2 Discovery` — where the data lives + successful endpoint
- `## L3 Validation` — schema + anchor + cross-source
- `## L4 Scaling` — what 10× data would need
- `## L5 Persistence` — JSON + CSV + metadata written
- `## L6 Adversarial` — escalation ladder tried (worked/failed, with evidence)

Honest failure is valuable. Round 5 + Round 8 evidence shows that a rigorous failure report with captured error codes + fingerprint-telemetry endpoints beats any "we succeeded" screenshot.

---

## Tool decision tree (the calibrated answer)

```
QUESTION 1: Is target data in raw HTML / SSR / public API?
  YES → Scrapy + httpx + curl  (Tier A)
  NO  → continue.

QUESTION 2: What class of anti-bot fires?
  Cloudflare managed / Turnstile → Scrapling.StealthyFetcher(solve_cloudflare=True)  (Tier B)
                                   ✓ R5-v1 sandbox, ✓ R7 BlackHatWorld real

  DataDome                       → stop. Tier C (paid vendor API or residential proxies).
                                   ✗ R8 G2 evidence.

  Kasada v3                      → stop. Tier C (no free POW solver anywhere).
                                   ✗ R8 Hyatt evidence.

  Akamai Bot Manager             → try curl_cffi safari18_0/firefox135 first;
                                   otherwise Tier C.
                                   ✗ R8 Lowe's evidence.

  Application-layer (silent redirect to /login)
                                 → homepage-first warming; otherwise Tier C.
                                   ✗ R5 Shopee evidence (even with ISP proxy: R9).

QUESTION 3: One-shot or recurrent pipeline?
  One-shot   → plain httpx / Scrapling Fetcher / curl + jq
  Recurrent  → Scrapy project (AutoThrottle, FEEDS, Items, Pipelines, RobotsTxt)
```

---

## What Tier C and D look like (for when we recommend paying or pivoting)

**Tier C — paid infrastructure** for DataDome / Kasada / Akamai / app-layer targets:

- **Vendor APIs** — [Scrapfly](https://scrapfly.io/), [ZenRows](https://www.zenrows.com/), [Bright Data](https://brightdata.com/), [Zyte](https://www.zyte.com/), [Oxylabs](https://oxylabs.io/). ~$30-500/month, pay-per-success, known working against DataDome/Kasada/Akamai per their published benchmarks.
- **Residential proxy pool + in-house solver** — ~$50-500/month residential egress + engineering time to integrate a CAPTCHA solver (2Captcha / CapSolver) for the interactive cases. Significant build cost.

**Tier D — sanctioned path (when the target has opted in)**:

- **Cloudflare's [AI Crawl Control / `/crawl` endpoint](https://developers.cloudflare.com/changelog/post/2026-03-10-br-crawl-endpoint/)** — 2026-03-10 release. If the target site has opted into AI Crawl Control and your purpose fits AI training / RAG / research, this is the cheapest AND legally cleanest path. Pay via Workers + Browser Rendering quota. Target must be Cloudflare-fronted AND opted in.
- **Partner API direct negotiation with the target** — zero per-request cost, potentially high upfront cost. Appropriate when the data is business-critical.

The job of THIS skill is to **recognize when Tier C or D is appropriate and tell the user honestly**, not to flail uselessly in Tier A/B.

---

## Ethics (automated)

- Read and honour `robots.txt` (Scrapy's `ROBOTSTXT_OBEY=True` does this for free).
- User-Agent identifies the crawler: `"<yourname>-research (contact@example.com)"`.
- ≤ 5 fetches per target domain per one-shot run; `AUTOTHROTTLE` for recurrent.
- ≥ 10 s between retries.
- No login, no authentication, no user-data extraction (GDPR landmine).
- No republishing — artefacts stay in the repo.
- Legal primer and jurisdictional notes in the [deep-dive essay §1.4](../../../essay_deep_dive.md).

---

## Required output

Every crawl run produces these files in the chosen `OUTPUT_DIR`:

| File | Contents |
|---|---|
| `result.json` | Array of typed objects (or `[]` with honest explanation) |
| `result.csv` | Same data, header + rows |
| `script.py` | Re-runnable driver |
| `page.html` | Final fetched body (success or challenge page) |
| `xhr_log.json` | If any browser tier ran — list of URL/method/status/content-type |
| `mechanism.md` | L1..L6 sections — the intelligence report |

---

## Reference material in this skill

- [`reference/calibrated-ceiling.md`](reference/calibrated-ceiling.md) — per-round evidence table from our 9 benchmarks
- [`reference/tool-stack.md`](reference/tool-stack.md) — which tool, which venv, which kwarg, per protection class
- [`reference/protection-classes.md`](reference/protection-classes.md) — per-class escalation detail + diagnostic signatures

## See also

- The **methodology** skill this thesis builds on: [`../web-scraper/SKILL.md`](../web-scraper/SKILL.md) by `yfe404`. Read for deeper phase-by-phase tactics (quality gates, framework detection, interactive probing). This thesis tells you *when to apply which phase*; `web-scraper` tells you *how*.
- The **sub-agent** that spawns with the thesis baked in: [`../../agents/crawl-specialist.md`](../../agents/crawl-specialist.md).
- The **slash command** that orchestrates a crawl end-to-end: [`../../commands/crawl.md`](../../commands/crawl.md).
- The **deep-dive essay** (8,000 words, 9 rounds): [`../../../essay_deep_dive.md`](../../../essay_deep_dive.md).
- The **operator runbook**: [`../../../THESIS_RUNBOOK.md`](../../../THESIS_RUNBOOK.md).
