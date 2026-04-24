# share_learn_demo — Live demo kit

Everything a presenter needs to run the 15-minute "Crawling with an LLM in the Room" share-and-learn demo.

## What's in here

| File | Purpose | When to read |
|---|---|---|
| [`DEMO_PLAN.md`](DEMO_PLAN.md) | Source of truth — timing, structure, fallbacks | Once, then skim |
| [`../slides.md`](../slides.md) | Slidev presentation at project root (`npm run dev` to preview) | Pre-demo rehearsal |
| [`demo_script.md`](demo_script.md) | Exact commands + narration, word-for-word | On 2nd monitor during demo |
| [`CHECKLIST.md`](CHECKLIST.md) | T-24h / T-60m / T-10m tick-box list | At each checkpoint |
| [`faq.md`](faq.md) | Anticipated Q&A with 1-paragraph answers | Skim T-10 min |
| [`cache/README.md`](cache/README.md) | Backup-recording + known-good-result instructions | T-24 h |

## The demo in one sentence

> Type ONE prompt into Claude Code → watch the web-scraper skill + Scrapy build a production-shape crawler that extracts 188 products from a paginated catalogue in ~10 s, with automatic bug-catching and reproducibility on `scrapy crawl products`.

## Three things the presenter does before the day

1. **T-24 h rehearsal** on the presentation laptop (NOT this dev box) — time it, record with `asciinema rec`, drop the cast in `cache/backup_recording.cast`.
2. **Run slidev** — `npm install && npm run dev` at project root to preview `../slides.md` locally; or `docker build . && docker run -p 8080:80 <image>` for a deployed version.
3. **Refresh the cache** — `cp` the known-good results from `../evaluation_r10/results/ecommerce/` into `cache/`.

## Where the evidence lives (parent project)

- Deep-dive essay: `../essay_deep_dive.md` (~8,000 words)
- Consolidated evidence (all rounds): `../.claude/skills/crawl-thesis/reference/calibrated-ceiling.md`
- Latest live scorecard: `../evaluation_r10/scorecard.md` (R10 meta-validation, 7 protection classes)
- Re-runnable synthesis project (188-product ecomm catalogue): `../evaluation_r10/results/ecommerce/`

## Dependencies the presenter's laptop needs

- Claude Code installed and authenticated
- `.claude/skills/web-scraper/` present in the project root
- `.venv-scrapy/` present with Scrapy 2.15 + scrapy-playwright
- `uvx` available (for any MCP fallback)
- `asciinema` for rehearsal recording (`brew install asciinema` or `apt install asciinema`)
- Outbound HTTPS to `scrapingcourse.com`

Everything else is in this folder.

## One-line emergency plan

If the live demo hangs at any point: say *"Live-demo gods say no"* → `asciinema play cache/backup_recording.cast` → continue narrating. The audience gets the same story.
