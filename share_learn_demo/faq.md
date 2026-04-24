# Demo Q&A — anticipated questions + 1-paragraph answers

### Q: How much did the LLM call cost?
The Round 4 benchmark used ~105 k total tokens across one agent turn. On Claude 4.7 that's roughly $0.30. The tradeoff is obvious — 15 minutes of senior engineer time saved per bootstrap dwarfs the token cost.

### Q: What if the site changes tomorrow?
Two answers. **(1)** The `items.py` schema + `DropEmptyPipeline` fail loud when a field disappears — you learn in the next cron run, not in a month. **(2)** You re-run the LLM bootstrap, diff the new spider against the committed one, review, commit. The LLM doesn't sit in the hot path — it bootstraps once and audits periodically.

### Q: Is what we just did legal?
Separate question. The demo target is an explicit scraping sandbox. For real sites the rules: public + factual + polite + no personal data is *probably* fine. Anything else → consult counsel. The essay has a 5-minute primer on hiQ v LinkedIn (CFAA narrowed), GDPR on "public" personal data, and the KASPR €240k fine.

### Q: Why Scrapy over a one-off Python script?
Every Scrapy default is a lifecycle dimension you don't have to remember: `ROBOTSTXT_OBEY`, `AUTOTHROTTLE`, `RETRY_TIMES`, `FEEDS`, `Item` validation. A hand-rolled script re-implements these, or skips them. For anything running on cron, Scrapy is the correct floor.

### Q: Could we get past Cloudflare with a paid service?
Yes. [Scrapfly](https://scrapfly.io/), [ZenRows](https://www.zenrows.com/), [ScrapingBee](https://www.scrapingbee.com/) are competitive. ~$30–$200/month for modest volume. Their business is the infrastructure layer we deliberately skipped — residential proxy fleets + TLS impersonation + challenge solvers, all behind one endpoint. That's the correct tradeoff if you have legal clearance and a budget.

### Q: What about CAPTCHAs?
Our benchmark explicitly forbade CAPTCHA-solver APIs. On sites you have permission to scrape, [2Captcha](https://2captcha.com/), [CapSolver](https://www.capsolver.com/), [AntiCaptcha](https://anti-captcha.com/) exist — same economic tradeoff as Scrapfly. Our rule: only when the data justifies the ethics + cost.

### Q: Does the skill work standalone without Scrapy?
Yes — in Round 2 of our benchmark it ran with bare `curl` + Python. The Scrapy pairing is what bumps the lifecycle score from 20/25 to 29/30. **Skill alone** = good thinking, manual plumbing. **Scrapy alone** = good plumbing, occasional wasted browser launch. **Together** = no waste.

### Q: What if Claude picks the wrong CSS selector?
Exactly what happened in Round 4. First spider version selected `.amount` and got `"32.0024.00"` for a sale-priced item (two `<span>`s concatenated). `DropEmptyPipeline` flagged the row, Claude re-inspected the HTML, changed the selector to prefer `<ins> .amount`, re-ran. 188 clean rows. **No human intervention.** That's the synthesis earning its keep.

### Q: Will this scale to 10,000 URLs?
Scrapy's AutoThrottle + CONCURRENT_REQUESTS handle it. For this target (188 products over 12 pages) the code is trivially 10× scalable — same spider, more domains in `start_urls`. Real-world concerns at that scale: (1) per-domain throttling — Scrapy already does it; (2) storage — switch FEEDS to a DB; (3) observability — Scrapy stats + a Prometheus exporter is a 50-line extension.

### Q: Can I use this on `[site]`?
Three-step check: **(1)** robots.txt — does it forbid your path? **(2)** ToS — is scraping called out as prohibited? **(3)** Is the data personal? If yes to any → stop and consult counsel. If no to all → run Phase 0 and see what happens.

### Q: What's the minimum useful version for a new hire?
`.claude/skills/web-scraper/` + `.venv-scrapy/` in the project. That's it. Everything else — the three rounds of benchmarks, the scorecards, the deep-dive essay — is archive material. The daily driver is the two directories.

### Q: Why is the cloudflare-challenge sibling site failing if /ecommerce/ works?
Different Cloudflare configurations on the same domain. The `/cloudflare-challenge` path has a strict Bot Management policy; `/ecommerce/` has a permissive one. ScrapingCourse's whole point is to let scrapers practice against varying strictness levels. Our Round 3 scorecard covers this in detail.

### Q: Is this the same as using Firecrawl / Tavily / Apify?
No. Those are commercial services that front the middle layer (proxies, browsers, challenge solvers) for you. They're the right answer when you're willing to pay per-request for the infrastructure. We evaluated free/local tooling only; commercial services are the correct alternative when the economics justify it and the legal ground is solid.

### Q: Can we put this behind a Slack bot?
Yes. The Scrapy project is runnable headless. Wire it to a slash command that parameterises `start_urls` and returns a link to the result artifact in S3. The LLM stays at the bootstrap/audit layer, not the hot path.

### Q: Timeline for adoption?
Three phases. **(1) This week:** teammates install `.claude/skills/web-scraper/` + `.venv-scrapy/` and run the demo target themselves. **(2) Next sprint:** pick one internal use case, bootstrap it with the skill+Scrapy combo, deploy on cron. **(3) Q+1:** revisit with enough cron-runs to evaluate skill-vs-hand-roll empirically on our data.
