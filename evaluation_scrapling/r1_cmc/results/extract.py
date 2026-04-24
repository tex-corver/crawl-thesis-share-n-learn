"""R1-Scrapling — CoinMarketCap top-20 extractor.

Tool: Scrapling Fetcher (plain HTTP + TLS impersonation via curl_cffi backend).
Protection: none (SSR + inline React Query hydration).

The target stores its coin listing in the HTML body as a serialised TanStack
Query cache under the key ``cryptoCurrencyList`` — same object shape as the
public CMC data-api would return. We fetch the homepage once, regex-locate the
JSON array start, walk the brackets with a string-aware depth counter (JSON is
embedded with quotes + escapes, so ``rfind(']')`` would be unsafe), then project
the first 20 items ranked by ``cmcRank``.

Usage (from project root)::

    .venv-scrapling/bin/python evaluation_scrapling/r1_cmc/results/extract.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from pathlib import Path

from scrapling.fetchers import Fetcher

URL = "https://coinmarketcap.com/"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "crawl-thesis-research (hainguyen@urieljsc.com)"
)
OUT_DIR = Path(__file__).resolve().parent
TARGET_ROWS = 20


def _locate_array(html: str, key: str) -> str:
    """Return the JSON array substring that follows ``"<key>":``.

    Walks character by character tracking bracket depth, ignoring brackets
    inside string literals (with backslash-escape awareness). Plain rfind on
    ``]`` would grab the outermost array in the whole document.
    """
    needle = f'"{key}":'
    idx = html.find(needle)
    if idx == -1:
        raise ValueError(f"key {key!r} not found in HTML")
    start = idx + len(needle)
    if html[start] != "[":
        raise ValueError(f"expected '[' after {key!r}, got {html[start]!r}")
    depth = 0
    in_str = False
    esc = False
    i = start
    while i < len(html):
        ch = html[i]
        if esc:
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == '"':
            in_str = not in_str
        elif not in_str:
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return html[start : i + 1]
        i += 1
    raise ValueError("unterminated array")


def _usd_quote(coin: dict) -> dict:
    for q in coin.get("quotes", []):
        if q.get("name") == "USD":
            return q
    raise ValueError(f"USD quote missing for {coin.get('symbol')}")


def extract() -> list[dict]:
    t0 = time.monotonic()
    # Scrapling Fetcher — plain HTTPS with curl_cffi TLS impersonation
    page = Fetcher.get(URL, headers={"User-Agent": UA}, timeout=30)
    if page.status != 200:
        raise RuntimeError(f"unexpected status {page.status}")
    html = page.body if isinstance(page.body, str) else page.body.decode("utf-8", "replace")
    arr_json = _locate_array(html, "cryptoCurrencyList")
    coins = json.loads(arr_json)

    ranked = sorted(
        (c for c in coins if isinstance(c.get("cmcRank"), int)),
        key=lambda c: c["cmcRank"],
    )[:TARGET_ROWS]

    rows = []
    for c in ranked:
        q = _usd_quote(c)
        rows.append(
            {
                "rank": c["cmcRank"],
                "symbol": c["symbol"],
                "name": c["name"],
                "price_usd": float(q["price"]),
                "market_cap_usd": float(q["marketCap"]),
                "change_24h_pct": float(q["percentChange24h"]),
            }
        )

    elapsed = time.monotonic() - t0
    print(f"extracted {len(rows)}/{TARGET_ROWS} rows in {elapsed:.2f}s", file=sys.stderr)
    return rows


def validate(rows: list[dict]) -> None:
    assert len(rows) == TARGET_ROWS, f"expected {TARGET_ROWS}, got {len(rows)}"
    ranks = [r["rank"] for r in rows]
    assert ranks == list(range(1, TARGET_ROWS + 1)), f"rank gap: {ranks}"
    assert rows[0]["symbol"] == "BTC", f"rank 1 not BTC: {rows[0]['symbol']}"
    for r in rows:
        assert isinstance(r["price_usd"], float) and r["price_usd"] > 0, r
        assert r["market_cap_usd"] > 1_000_000_000, f"mcap<1B for {r['symbol']}: {r['market_cap_usd']}"
        assert r["name"] and r["symbol"], r
    print(f"validation OK — BTC @ ${rows[0]['price_usd']:,.2f}", file=sys.stderr)


def persist(rows: list[dict]) -> None:
    (OUT_DIR / "result.json").write_text(json.dumps(rows, indent=2))
    with (OUT_DIR / "result.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    rows = extract()
    validate(rows)
    persist(rows)
    print(json.dumps(rows, indent=2))
