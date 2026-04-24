"""Crawl Astral Codex Ten via Substack's public v1 API.

Phase 0 alone is sufficient — documented /api/v1/posts returns JSON with all
requested fields. No browser, no challenge solver needed.
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import httpx

OUT_DIR = Path(__file__).parent
BASE = "https://www.astralcodexten.com"
UA = "substack-research-contact (hainguyen@urieljsc.com)"
FIELDS = ("title", "post_url", "post_date", "subtitle", "audience")
TARGET_COUNT = 30


def fetch_posts(count: int) -> list[dict]:
    """Fetch `count` posts via the public v1 API (paginated 25 at a time)."""
    rows: list[dict] = []
    offset = 0
    page_size = 25
    with httpx.Client(headers={"User-Agent": UA}, timeout=20.0) as client:
        while len(rows) < count:
            url = f"{BASE}/api/v1/posts?limit={page_size}&offset={offset}"
            resp = client.get(url)
            resp.raise_for_status()
            page = resp.json()
            if not page:
                break
            rows.extend(page)
            offset += page_size
            if len(rows) >= count:
                break
            time.sleep(2)  # polite pagination on public documented API
    return rows[:count]


def normalize(raw: list[dict]) -> list[dict]:
    out = []
    for p in raw:
        out.append({
            "title": p.get("title", ""),
            "post_url": p.get("canonical_url", ""),
            "post_date": p.get("post_date", ""),
            "subtitle": p.get("subtitle", ""),
            "audience": p.get("audience", ""),
        })
    return out


def main() -> None:
    raw = fetch_posts(TARGET_COUNT)
    items = normalize(raw)

    (OUT_DIR / "result.json").write_text(json.dumps(items, indent=2, ensure_ascii=False))

    with (OUT_DIR / "result.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(items)

    # Persist homepage HTML (page.html) for evidence
    with httpx.Client(headers={"User-Agent": UA}, timeout=20.0) as client:
        html = client.get(BASE + "/").text
    (OUT_DIR / "page.html").write_text(html)

    print(f"Extracted {len(items)} items -> {OUT_DIR}")


if __name__ == "__main__":
    main()
