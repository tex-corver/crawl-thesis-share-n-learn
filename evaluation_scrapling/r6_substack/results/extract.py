"""R6-Scrapling — Extract 30 most recent posts from Astral Codex Ten.

Uses Scrapling Fetcher (TLS-impersonating HTTP) for a single GET against
Substack's public JSON API. No browser, no solver — this is a documented
public endpoint that returns structured JSON.

Run:
    /home/hainm/tmp/share_learn_research/.venv-scrapling/bin/python extract.py
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

from scrapling.fetchers import Fetcher

API_URL = "https://www.astralcodexten.com/api/v1/posts?limit=30&offset=0"
UA = "share-learn-research (hainguyen@urieljsc.com)"
OUT_DIR = Path(__file__).parent


def main() -> int:
    t0 = time.monotonic()

    # Scrapling Fetcher — async TLS-impersonating HTTP client (curl_cffi under the hood).
    # Chosen over DynamicFetcher/StealthyFetcher because the target is a public JSON API:
    # no JS rendering needed, no anti-bot challenge present (Phase 0 confirmed HTTP 200).
    resp = Fetcher.get(
        API_URL,
        headers={"User-Agent": UA, "Accept": "application/json"},
        timeout=30,
        stealthy_headers=False,  # don't need stealth for public API
    )

    if resp.status != 200:
        print(f"HTTP {resp.status} — abort", file=sys.stderr)
        return 1

    payload = json.loads(resp.body)
    if not isinstance(payload, list):
        print(f"Unexpected payload type: {type(payload).__name__}", file=sys.stderr)
        return 1

    posts = []
    for raw in payload:
        posts.append(
            {
                "title": raw.get("title") or "",
                "subtitle": raw.get("subtitle") or "",
                "canonical_url": raw.get("canonical_url") or "",
                "post_date_iso": raw.get("post_date") or "",
                "word_count": raw.get("wordcount"),
                "like_count": raw.get("reaction_count"),
            }
        )

    # Validate
    assert len(posts) == 30, f"Expected 30 posts, got {len(posts)}"
    for p in posts:
        assert p["canonical_url"].startswith("https://"), f"Bad URL: {p['canonical_url']}"
        assert "substack" in p["canonical_url"] or "astralcodexten" in p["canonical_url"], (
            f"URL not on expected domain: {p['canonical_url']}"
        )
        # ISO 8601 parse sanity: just check it contains a 'T' and looks like a date
        assert "T" in p["post_date_iso"], f"Bad date format: {p['post_date_iso']}"

    # Freshness sanity
    latest_year = posts[0]["post_date_iso"][:4]
    print(f"Latest post year: {latest_year} — date: {posts[0]['post_date_iso']}")

    # Persist JSON
    (OUT_DIR / "result.json").write_text(json.dumps(posts, indent=2, ensure_ascii=False))

    # Persist CSV
    with (OUT_DIR / "result.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "subtitle",
                "canonical_url",
                "post_date_iso",
                "word_count",
                "like_count",
            ],
        )
        writer.writeheader()
        writer.writerows(posts)

    wall = time.monotonic() - t0
    print(f"OK — {len(posts)} posts extracted in {wall:.2f}s")
    print(f"JSON: {OUT_DIR / 'result.json'}")
    print(f"CSV:  {OUT_DIR / 'result.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
