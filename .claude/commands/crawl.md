---
description: Crawl a URL using our thesis methodology (skill + Scrapy + Scrapling, free/local only). Spawns a crawl-specialist sub-agent, scores the output, reports one-line verdict.
argument-hint: <URL> [count=30] [fields=name,url,price] [output_dir=evaluation_r<N>/results/<target>/]
---

# /crawl — apply the thesis to a URL

You are the orchestrator for a thesis-faithful crawl. The thesis lives at
`.claude/skills/crawl-thesis/` (our calibrated 9-round evidence-backed
version) and `.claude/skills/web-scraper/` (the upstream methodology it
builds on). Read `crawl-thesis/SKILL.md` before spawning the sub-agent.

## Target
URL: `$1`
Requested count (optional, default 30): `$2`
Requested fields (optional, default name,url,price): `$3`
Output directory (optional, default auto): `$4`

## Your steps

### 0. Preflight — verify tools are installed

Before anything else, confirm the project's tool stack is on disk:

```bash
bash scripts/check.sh
```

If `check.sh` reports any **required** component missing, **STOP**. Do NOT try to install on the user's behalf. Report back with a one-liner:

> "Tool stack incomplete — run `make venvs` in the project root first, then re-run `/crawl`."

Only proceed past this gate when `check.sh` exits 0 ("All required components present").

### 1. Orchestrator probe
After preflight passes, do a 5-second classification probe yourself:
```bash
curl -sI -A "Mozilla/5.0" "$1" | head -10
curl -s -A "Mozilla/5.0" "$1" | head -c 2000 > /tmp/crawl_probe.html
```

Classify the target into one of:
- **Open**: HTTP 200, data in raw HTML (e.g. `__NEXT_DATA__` present, or product markup visible)
- **Public API**: documented `/api/v1/`, `/feed`, or sitemap surfaced
- **Cloudflare managed challenge**: `cf-mitigated: challenge` header, `cType: 'managed'` in body
- **DataDome**: `x-datadome` header, "Please enable JS" body
- **Kasada**: `window.KPSDK`, `ips.js` in body
- **Akamai**: `akamai-grn` / `server-timing: ak_p` headers, "Access Denied" body
- **App-layer (silent redirect)**: HTTP 200 but redirected to `/login` or similar
- **Unknown** — let the sub-agent figure it out

### 2. Pick output directory
If user didn't provide one, use convention:
- Guess domain name from URL (e.g. `shopee.sg` → `shopee_sg`)
- Pick next Round number by counting existing `evaluation_r*/` dirs
- `mkdir -p evaluation_r<N>/results/<target_slug>/`

### 3. Spawn the crawl-specialist sub-agent

```
Agent(
    subagent_type="crawl-specialist",  # or "general-purpose" if the specialist isn't registered
    description="Crawl {target_slug} via full thesis",
    prompt="""
Fresh sub-agent, no prior context.

## Mission
Apply the project's full thesis to extract {count} items from {URL}.

Fields per row: {fields_list_parsed}

## Known protection profile (from orchestrator probe)
{probe_classification}
{probe_evidence}

## Output directory
{output_dir}

## Constraints
- Free/local tools only (no paid services)
- ≤ 5 fetches to the target domain
- ≥ 10 s between retries
- UA with "research-contact" identifier
- Timebox: 15 minutes

## Required outputs
result.json · result.csv · script.py · page.html · xhr_log.json (if browser ran) · mechanism.md (L1..L6)

## Return format
ONE line: STATUS, N items, phase won or blocked at, verdict.
"""
)
```

### 4. Score the result
After the sub-agent returns:
- Read `{output_dir}/mechanism.md` — extract tool-stack, phase-outcome, run-stats
- If `research/templates/score_template.py` + a checklist are present, run the scorer
- Otherwise do a quick manual correctness check (row count, field presence, anchor sanity)

### 5. Report to user
Output a concise 5-line summary:

```
Target: {URL}
Result: {STATUS} — {N}/{count} items extracted
Path: {phase_won_or_blocked} · {tool_used}
Evidence: {output_dir}/mechanism.md
Next: {recommendation — re-run / escalate to Tier C / accept as-is}
```

## Guard-rails

- If `$1` is empty, ask the user for a URL.
- If the URL's TLD suggests login-walled (`linkedin.com`, `facebook.com` profile URLs), warn about CFAA/GDPR exposure before proceeding.
- If the target matches known-hardest-tier (G2 / Hyatt / Shein / Lowe's / Shopee), tell the user up-front that the thesis is expected to fail and offer to run it anyway for evidence or pivot to a paid vendor API recommendation.
- If the sub-agent fabricates data (returns PASS but `result.json` has suspicious uniform-structure rows), flag loudly.

## The thesis this command encodes

Free/local tools clear polite public data AND Cloudflare-managed challenges.
DataDome / Kasada / Akamai / app-layer require paid Tier-C.
9 benchmark rounds in `evaluation_r*/scorecard.md` back this claim.
