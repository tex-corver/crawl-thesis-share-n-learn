# Demo-day checklist — tick in order

## T-24 hours
- [ ] Read the full `DEMO_PLAN.md` once, uninterrupted
- [ ] Dry-run the live demo on your actual laptop, timer running
  ```bash
  time ~/.venv-scrapy/bin/scrapy --version  # warm caches
  # then type the live prompt into Claude Code and run end-to-end
  ```
  Record wall-clock. Target ≤ 6 min. If > 7 min, cut pagination or switch to cached.
- [ ] Make a backup recording with asciinema:
  ```bash
  asciinema rec demo/cache/backup_recording.cast \
    --title "skill+scrapy demo" --overwrite
  # perform the demo
  # Ctrl-D to stop
  asciinema play demo/cache/backup_recording.cast   # verify
  ```
- [ ] Copy good-known result to cache (already done if R4 results present):
  ```bash
  cp evaluation_r10/results/ecommerce/result.json demo/cache/result_known_good.json
  cp evaluation_r10/results/ecommerce/result.csv  demo/cache/result_known_good.csv
  ```

## T-60 min
- [ ] Target reachable:
  ```bash
  curl -s -o /dev/null -w "%{http_code} %{size_download}\n" \
    https://www.scrapingcourse.com/ecommerce/
  # expect: 200 ~82000
  ```
- [ ] Skill present:
  ```bash
  ls .claude/skills/web-scraper/SKILL.md
  ```
- [ ] Scrapy venv works:
  ```bash
  source .venv-scrapy/bin/activate && scrapy --version && deactivate
  ```
- [ ] Clean `demo/live_run/` so the demo starts from zero:
  ```bash
  rm -rf demo/live_run && mkdir -p demo/live_run
  ```
- [ ] Terminal font 14 pt or larger, high-contrast theme.
- [ ] Close every other window. Nothing in scrollback that could embarrass.
- [ ] Airplane-mode chat apps. Disable notifications.
- [ ] Browser tab with `evaluation_r10/results/ecommerce/result.csv` pre-opened as a safety reference.
- [ ] Power cable in. Lid angle checked against projector glare.

## T-10 min
- [ ] Open Claude Code in the project root:
  ```bash
  cd /home/hainm/tmp/share_learn_research
  ```
- [ ] Have the exact prompt in your copy buffer (from `demo_script.md`).
- [ ] Emergency fallback script (`DEMO_PLAN.md §Emergency`) on a printed sheet or second screen.
- [ ] Water. Deep breath.

## During the demo
- [ ] If Claude starts reading files not in the project → don't panic, narrate it.
- [ ] If the run exceeds 6 min → at 7 min, switch to cached output with the sentence:
      *"Live-demo gods say no. Let me show the rehearsal."*
- [ ] If the site returns 403/429 → it's been throttled (rare). Use cached output.
- [ ] If Claude mis-labels "Scrapy" as something else → correct once, don't harp.
- [ ] Keep slides between live segments — audiences need the rest.

## After the demo
- [ ] Send the 1-pager takeaway to the channel.
- [ ] Commit `demo/live_run/` so the audience can inspect it themselves.
- [ ] Offer 1:1 follow-ups for anyone wanting to replicate.
