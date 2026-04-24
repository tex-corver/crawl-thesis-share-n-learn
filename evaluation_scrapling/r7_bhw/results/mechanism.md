# R7-Scrapling — BlackHatWorld (real CF production)

**Date:** 2026-04-22
**Tool:** Scrapling `StealthyFetcher(solve_cloudflare=True, headless=True, network_idle=True)`
**Python:** `.venv-scrapling` (Scrapling 0.4+ with Camoufox)
**Target:** `https://www.blackhatworld.com/forums/black-hat-seo.74/`
**Protection:** Cloudflare managed (confirmed) + **application-layer login wall at origin** (new since R7)
**Outcome:** PARTIAL — Cloudflare cleared in 17.66 s, but origin now 307-redirects guest requests to `/login/`. 0 threads extracted.
**Solve wall-clock:** 17.66 s (including one re-solve cycle)

---

## L1 Research (what we knew)

From the calibrated ceiling:

- R3 sandbox (`scrapingcourse/cloudflare-challenge`): `StealthyFetcher(solve_cloudflare=True)` cleared Cloudflare managed challenge in ~20 s.
- **R7 BlackHatWorld (prior run)**: same tool cleared the exact same URL and returned 24 validated threads — the evidence cell that "sandbox CF trick transfers to real production".
- Hypothesis for this benchmark: the transfer still holds; BHW is still Cloudflare-managed; Scrapling ought to return ≥10 threads in ~20 s.

Politeness constraints honored: research UA, ≤ 2 fetches (1× `curl -sI` control + 1× Scrapling fetch), no login attempted.

---

## L2 Discovery — control 403 evidence

Phase-0 probe (one `curl -sI`, research UA):

```
$ curl -sI -A "share_learn_research/0.1 (research-contact)" \
       "https://www.blackhatworld.com/forums/black-hat-seo.74/"

HTTP/2 403
content-type: text/html; charset=UTF-8
cf-mitigated: challenge
server: cloudflare
cf-ray: 9f02e2512b320460-HKG
content-security-policy: ... script-src 'nonce-...' https://challenges.cloudflare.com ...
server-timing: chlray;desc="9f02e2512b320460"
```

Signature matches the Class-3 Cloudflare-managed ladder exactly (`cf-mitigated: challenge`, `server: cloudflare`, `challenges.cloudflare.com` CSP allowlist). Textbook Turnstile/managed interstitial — same class Scrapling cleared at R3 sandbox and prior R7.

---

## L3 Extract — StealthyFetcher call + observed behaviour

Call (see [`extract.py`](extract.py)):

```python
from scrapling.fetchers import StealthyFetcher

page = StealthyFetcher.fetch(
    "https://www.blackhatworld.com/forums/black-hat-seo.74/",
    solve_cloudflare=True,
    headless=True,
    network_idle=True,
)
```

Scrapling runtime log (verbatim):

```
[07:24:09] INFO: The turnstile version discovered is "managed"
[07:24:20] INFO: Cloudflare page didn't disappear after 10s, continuing...
[07:24:20] INFO: Looks like Cloudflare captcha is still present, solving again
[07:24:20] INFO: The turnstile version discovered is "managed"
[07:24:23] INFO: Cloudflare captcha is solved
[07:24:24] INFO: Fetched (307) <GET https://www.blackhatworld.com/forums/black-hat-seo.74/>
[07:24:24] INFO: Fetched (403) <GET https://www.blackhatworld.com/forums/black-hat-seo.74/>
```

Final response:

- **HTTP 403** returned to Scrapling after a 307 redirect chain
- **`<title>Log in | BlackHatWorld</title>`** — NOT "Just a moment..."
- **`<body data-template="login">`** — XenForo's login template, not the thread-listing template
- **`<h1 class="p-title-value">Log in</h1>`** visible in the body
- `.structItem--thread` rows: **0** (there are none to find on a login page)

The Cloudflare-managed stage was solved cleanly (Scrapling's internal log: `"Cloudflare captcha is solved"`). The 403 on the second log line is BHW's origin returning a login-wall page (XenForo's own enforcement), not Cloudflare still challenging — evidenced by the `data-template="login"` DOM and absence of `cf-mitigated: challenge` headers on that response's body content.

---

## L4 Validate — validation decision

The validation checklist could not run: 0 rows, 0 threads. The page guards ran instead:

| Guard | Result |
|---|---|
| "Just a moment" in page title? | **No** — CF did not serve the challenge on this response |
| "Log in" in page title? | **Yes** — origin login wall |
| Status 200 with thread listing? | No — status 403, login template |
| `.structItem--thread` rows ≥ 10? | No — 0 rows |

**Final result: `result.json = []`, `result.csv` = header only.** Honest empty output per thesis "Honesty > completion" + "fabricating rows forbidden".

---

## L5 Persist

Files in this directory:

| File | Purpose |
|---|---|
| `result.json` | `[]` — honest empty output |
| `result.csv` | Header-only CSV |
| `meta.json` | Status 403, title "Log in \| BlackHatWorld", rows 0, solve 17.66 s |
| `page.html` | 37 KB XenForo login template for auditing |
| `extract.py` | Re-runnable driver |
| `mechanism.md` | This report |

---

## L6 Honest observations

### 1. Cloudflare remains clearable — this is NOT a CF-tier failure

The Cloudflare managed challenge was solved in ~17 s (vs R3's ~20 s). Scrapling's StealthyFetcher did its job. The tool category — "Tier B for Cloudflare managed" — is still valid on BHW's edge. **The thesis's upper bound on CF is intact.**

### 2. What changed since R7: BHW moved guest browsing behind login

Prior R7 evidence (same URL, same tool): "24 validated threads extracted". This run: 0. The difference is an **application-layer change at BHW's origin**, not in Cloudflare's edge behaviour:

- The final HTML is XenForo's `data-template="login"` page, served directly by BHW.
- There is no "Just a moment..." anywhere in the response.
- Request chain shows `307 → 403` AFTER the CF token was minted — the origin is doing the blocking, not the edge.
- `<meta name="robots" content="noindex">` is set on the login page (normal XenForo behaviour).

This is a site-policy change — at some point between R7 (earlier benchmark) and 2026-04-22, BHW reconfigured the black-hat-seo subforum so guest requests redirect to login. Likely motivation: reduce scraping pressure on the flagship SEO board; logged-in users still get the listing.

### 3. Map the new failure onto the protection-class taxonomy

Per `reference/protection-classes.md`, this is now **Class 8 — Authentication required** (login wall), layered behind Class 3 (Cloudflare managed). The Class-8 ladder is explicit:

> **Tier A STOP.** This thesis is public-data-only by design. Login brings CFAA, GDPR, ToS exposure into scope.

Correct action: stop. Report honestly. Do not attempt to log in, do not attempt `/register/`, do not try credential-less session shenanigans. This matches the ethics block in the repo CLAUDE.md ("No login, no authentication").

### 4. Thesis implication — the calibrated ceiling needs an R7 addendum

The prior R7 cell — "Cloudflare Turnstile / managed on real production" — remains correct for **sites that still publish threads to guests**. But specific-site policy can shift underneath us:

> **A Cloudflare-cleared response is necessary but not sufficient for data extraction.** Origin-layer policy (login walls, rate limits, regional blocks, subscription paywalls) sits behind the CDN and can change independently of the anti-bot tier.

Suggested update to `reference/calibrated-ceiling.md`: keep the R7 "sandbox → real CF" claim (tool mechanism still works), but **note the R7-recheck observation that BHW now gates this subforum behind login as of 2026-04-22**. Good candidates for a still-open guest CF target: XenForo forums without subscription gating, XenForo-powered wikis, sites that advertise public content (news, open community forums, documentation portals).

### 5. What would actually extract threads now — and why we won't do it

Paths that would work but violate this thesis's scope:

- **Log in with a real account** → Class 8 says stop (CFAA/ToS/GDPR exposure).
- **BHW partner/API negotiation** → valid Tier D but requires a business relationship, not a tool.
- **Cached/archived data via Archive.org Wayback** → different URL surface, different thesis (historical crawl), out of scope here.
- **Different XenForo target that is still guest-readable** → would retest the thesis mechanism but changes the target; belongs in a separate R7b run.

Tier-C paid APIs (Scrapfly et al.) **also** can't bypass an intentional origin login wall without credentials — this is an application-policy problem, not an anti-bot problem. Paying more money doesn't unlock what the site owner has set behind auth.

### 6. Budget accounting

- Fetches to `blackhatworld.com`: **2** (1× `curl -sI` control, 1× Scrapling `StealthyFetcher.fetch`).
- Time budget: well under 10 min (whole run ~25 s).
- No homepage-first retry attempted (would have been fetch #3, over budget; also unlikely to change an intentional origin login redirect).
- No login, no registration, no credentials — ethics preserved.

### 7. Summary for the scorecard

| Dimension | Result |
|---|---|
| Cloudflare managed challenge solved? | ✅ Yes (17.66 s) — thesis mechanism confirmed at tool layer |
| Threads extracted? | ❌ 0 — origin login wall, not a CF failure |
| Honest output? | ✅ `[]` + page.html + mechanism.md |
| Thesis invalidated? | ❌ No — Class-3 ladder works; Class-8 (auth) correctly stops us |
| Action | Route this target to Tier D (partner API) or drop it from the guest-CF canon |
