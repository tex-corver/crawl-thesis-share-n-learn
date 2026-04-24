"""R2-Scrapling — Binance top 30 USDT spot pairs by 24h quote volume.

Tool: Scrapling Fetcher (plain TLS-aware HTTP).
Strategy: Hit the documented public REST API (data-api.binance.vision/api/v3/ticker/24hr).
The www.binance.com homepage is CloudFront-WAF-gated (HTTP 202, x-amzn-waf-action: challenge),
but the documented API mirror is open and returns full ticker JSON.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from scrapling.fetchers import Fetcher

API_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"
UA = "crawl-thesis-research (contact@example.com)"
OUT_DIR = Path(__file__).parent


def main() -> None:
    t0 = time.perf_counter()

    # Scrapling Fetcher — TLS-aware, no browser, no JS. Public API.
    response = Fetcher.get(API_URL, headers={"User-Agent": UA}, timeout=30)
    if response.status != 200:
        raise SystemExit(f"API returned {response.status}")

    tickers = json.loads(response.body)
    print(f"Raw tickers: {len(tickers)}")

    # Filter to USDT spot pairs. USDT is the quote asset, so symbol endswith 'USDT'.
    # Exclude leveraged tokens (UP/DOWN/BULL/BEAR) and known stablecoin/fiat wrappers
    # where quoteVolume is misleading (a USDT/USDT pair would be nonsense).
    LEVERAGED_SUFFIXES = ("UPUSDT", "DOWNUSDT", "BULLUSDT", "BEARUSDT")
    usdt_pairs = [
        t
        for t in tickers
        if t["symbol"].endswith("USDT")
        and not any(t["symbol"].endswith(s) for s in LEVERAGED_SUFFIXES)
    ]
    print(f"USDT spot pairs (post-filter): {len(usdt_pairs)}")

    # Sort by quoteVolume (USD-equivalent 24h turnover) descending.
    usdt_pairs.sort(key=lambda t: float(t["quoteVolume"]), reverse=True)

    top30 = usdt_pairs[:30]

    rows = [
        {
            "rank": i + 1,
            "symbol": t["symbol"],
            "last_price": float(t["lastPrice"]),
            "change_24h_pct": float(t["priceChangePercent"]),
            "quote_volume_24h_usd": float(t["quoteVolume"]),
        }
        for i, t in enumerate(top30)
    ]

    # Persist JSON
    json_path = OUT_DIR / "result.json"
    json_path.write_text(json.dumps(rows, indent=2))

    # Persist CSV
    csv_path = OUT_DIR / "result.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    wall = time.perf_counter() - t0
    print(f"Wrote {len(rows)} rows in {wall:.2f}s")
    print(f"Top 5: {[(r['rank'], r['symbol'], r['quote_volume_24h_usd']) for r in rows[:5]]}")


if __name__ == "__main__":
    main()
