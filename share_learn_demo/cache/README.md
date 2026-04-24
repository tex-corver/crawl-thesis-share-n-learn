# demo/cache/

Safety-net artefacts for the live demo. Regenerate before each presentation.

## What goes in here

| File | How to produce | Purpose |
|---|---|---|
| `backup_recording.cast` | `asciinema rec` during a successful rehearsal | Played if the live run fails |
| `result_known_good.json` | `cp evaluation_r10/results/ecommerce/result.json .` | Show-and-tell fallback |
| `result_known_good.csv` | same | CSV version |
| `rehearsal_timing.txt` | `time` output from your rehearsal | So you know how long to let the live run go before cutting over |

## Pre-flight refresh (T-24 h)

```bash
cd /home/hainm/tmp/share_learn_research
cp evaluation_r10/results/ecommerce/result.json demo/cache/result_known_good.json
cp evaluation_r10/results/ecommerce/result.csv  demo/cache/result_known_good.csv

# asciinema recording — do the actual demo under this wrapper
asciinema rec demo/cache/backup_recording.cast \
  --title "skill+scrapy demo rehearsal" --overwrite \
  --command "bash"
# Then reproduce the live demo end-to-end, exit with Ctrl-D.
# Playback check:
asciinema play demo/cache/backup_recording.cast
```

## Playback during emergency

```bash
asciinema play demo/cache/backup_recording.cast
```

Or, if you just want to show the *outputs* without the terminal theatrics:

```bash
cat demo/cache/result_known_good.json | jq 'length'   # 188
head -5 demo/cache/result_known_good.csv
```
