"""R7-Scrapling — BlackHatWorld forum thread extraction via StealthyFetcher.

Target: https://www.blackhatworld.com/forums/black-hat-seo.74/
Protection: Cloudflare managed (confirmed via Phase 0 control — HTTP 403 cf-mitigated: challenge)
Tool: Scrapling StealthyFetcher(solve_cloudflare=True)

Runbook:
    /home/hainm/tmp/share_learn_research/.venv-scrapling/bin/python extract.py

Budget:
    ≤ 2 fetches total to blackhatworld.com. This script issues ONE Scrapling
    fetch; the optional control was already performed out-of-band via curl -sI.
"""

from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path

from scrapling.fetchers import StealthyFetcher

TARGET = "https://www.blackhatworld.com/forums/black-hat-seo.74/"
OUT_DIR = Path(__file__).parent
MAX_THREADS = 15


def _parse_count(text: str) -> int | str:
    """Parse XenForo count text like '1.2K', '12,345', '42'."""
    if not text:
        return 0
    cleaned = text.strip().replace(",", "")
    m = re.match(r"^([\d.]+)\s*([KkMm]?)$", cleaned)
    if not m:
        return cleaned
    num = float(m.group(1))
    suffix = m.group(2).upper()
    if suffix == "K":
        return int(num * 1000)
    if suffix == "M":
        return int(num * 1_000_000)
    return int(num)


def _title(html: str) -> str:
    m = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def main() -> None:
    t0 = time.monotonic()
    page = StealthyFetcher.fetch(
        TARGET,
        solve_cloudflare=True,
        headless=True,
        network_idle=True,
    )
    solve_seconds = time.monotonic() - t0

    status = page.status
    html = page.html_content
    (OUT_DIR / "page.html").write_text(html, encoding="utf-8")

    page_title = _title(html)
    rows = page.css(".structItem--thread")
    print(f"status={status} title={page_title!r} rows={len(rows)} solve={solve_seconds:.2f}s")

    threads: list[dict] = []
    for row in rows[:MAX_THREADS]:
        title_anchors = row.css(".structItem-title a")
        if not title_anchors:
            continue
        picked = None
        for a in title_anchors:
            h = a.attrib.get("href", "")
            if "/threads/" in h:
                picked = a
                break
        if picked is None:
            continue
        title = (picked.text or "").strip()
        href = picked.attrib.get("href", "")
        if not title:
            continue
        thread_url = (
            href if href.startswith("http") else f"https://www.blackhatworld.com{href}"
        )
        author = row.attrib.get("data-author", "").strip()
        if not author:
            u = row.css_first(".username")
            author = (u.text or "").strip() if u else ""

        replies_raw = ""
        views_raw = ""
        for dl in row.css(".structItem-minor dl.pairs"):
            dt = dl.css_first("dt")
            dd = dl.css_first("dd")
            if not dt or not dd:
                continue
            label = (dt.text or "").strip().lower()
            value = (dd.text or "").strip()
            if "repl" in label:
                replies_raw = value
            elif "view" in label:
                views_raw = value

        threads.append(
            {
                "title": title,
                "thread_url": thread_url,
                "author": author,
                "replies_count": _parse_count(replies_raw),
                "views_count": _parse_count(views_raw) if views_raw else views_raw,
            }
        )

    (OUT_DIR / "result.json").write_text(
        json.dumps(threads, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with (OUT_DIR / "result.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "thread_url",
                "author",
                "replies_count",
                "views_count",
            ],
        )
        w.writeheader()
        w.writerows(threads)

    meta = {
        "status": status,
        "page_title": page_title,
        "rows_found": len(rows),
        "threads_extracted": len(threads),
        "solve_seconds": round(solve_seconds, 2),
        "guard_just_a_moment": "just a moment" in page_title.lower(),
        "guard_login_wall": "log in" in page_title.lower(),
    }
    (OUT_DIR / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
