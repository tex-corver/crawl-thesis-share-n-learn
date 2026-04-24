# Demo-day script — commands + narration only

Keep this open on a second monitor or printed. Everything is either "TYPE" (into terminal/Claude) or "SAY".

---

## Phase 1 — The prompt (t=0:00)

**SAY:**
> "One prompt. Watch."

**TYPE into Claude Code:**

```
Crawl all products from https://www.scrapingcourse.com/ecommerce/
using the web-scraper skill's Phase 0 methodology, and build a
Scrapy project for it. Put everything under demo/live_run/.
Emit result.json, result.csv, and mechanism.md. Timebox: 6 minutes.
```

---

## Phase 2 — Narrate while Claude works (t=0:30 → 5:00)

**When Claude reads `.claude/skills/web-scraper/SKILL.md`:**

> "Skill loading. This is the methodology half — six phases, quality gates between them."

**When the first `curl` runs:**

> "Phase 0. One curl. If the target data is in raw HTML we skip the browser entirely — that's ~170 MB of Chromium we don't have to download and ~5 seconds of startup we don't spend."

**When the scrapy project directory is created:**

> "Scrapy scaffold. `items.py` holds the schema. `pipelines.py` drops malformed rows. `settings.py` has AutoThrottle and RETRY and FEEDS — every lifecycle dimension as one config line."

**When the spider starts crawling pages:**

> "12 pages, paginated politely. AutoThrottle is in charge of request spacing. The framework does what a hand-rolled script forgets."

**If/when the `DropEmptyPipeline` flags a bug:**

> "There it is. The pipeline caught a malformed row — a sale-priced product that concatenated two `.amount` nodes. A hand-rolled script would have shipped this bad row silently. Claude is about to diagnose and fix the selector."

**When 188 rows are emitted:**

> "188 products. Complete catalogue. Let's verify."

---

## Phase 3 — Verification (t=5:00)

**TYPE:**

```bash
ls -la demo/live_run/
```

**TYPE:**

```bash
cat demo/live_run/result.json | jq 'length'
# expect: 188
```

**TYPE:**

```bash
head -5 demo/live_run/result.csv
```

**SAY:**
> "188 typed rows. JSON and CSV from the same stream."

---

## Phase 4 — Reproducibility proof (t=6:30)

**SAY:**
> "Here's the part that matters if you're shipping this. Claude wrote a Scrapy project. Any engineer can run it."

**TYPE:**

```bash
source .venv-scrapy/bin/activate
cd demo/live_run
scrapy crawl products -L INFO 2>&1 | tail -5
```

**SAY:**
> "One command. Cron-able. Reviewable. The LLM doesn't need to stay in the hot path."

---

## Phase 5 — Honesty about Cloudflare (t=8:30)

**Switch to slide 4 ("But… Cloudflare?")**

**SAY:**
> "Before anyone asks. Cloudflare Turnstile is a different tier. Same site, different URL: `/cloudflare-challenge`. Zero out of six tools bypassed it from this laptop. Six independent agents converged on the same root cause — datacenter IP reputation, not the tool. The fix is residential proxies. That's infrastructure, not LLM."

---

## Phase 6 — Recommended stack (t=10:30)

**Switch to slide 5.**

**SAY:**
> "Three deploy shapes. Left: one-off research, five minutes, zero deps. Middle: the recurrent pipeline — what we just demoed. Right: adversarial tier — don't even try without residential proxies and a legal review."

---

## Phase 7 — Q&A (t=12:00)

Let audience drive. Use `faq.md` cheat sheet.

---

## Emergency fallback

If the live demo hangs / fails at any point:

**SAY:**
> "Live-demo gods say no. Let me show you the rehearsal from earlier."

**TYPE:**

```bash
asciinema play demo/cache/backup_recording.cast
```

or

```bash
cat demo/cache/result_known_good.json | jq 'length'
head -5 demo/cache/result_known_good.csv
```

**Continue with Phase 3 narration onwards — the narrative doesn't change.**
