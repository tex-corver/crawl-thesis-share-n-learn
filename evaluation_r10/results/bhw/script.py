#!/usr/bin/env python3
"""BHW top-N thread extraction (R10 /crawl).

Thesis: Cloudflare-managed challenge → Scrapling StealthyFetcher(solve_cloudflare=True).
R7 precedent: cleared in ~20s headless. Target N=20 (BHW page 1 renders ~24 threads).
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from pathlib import Path

OUT_DIR = Path(__file__).parent.resolve()
URL = "https://www.blackhatworld.com/forums/making-money.12/"
TARGET_N = 20


def views_to_int(s: str) -> int:
    if s is None:
        return -1
    s = s.strip().replace(",", "")
    if not s:
        return -1
    m = re.match(r"^([\d.]+)\s*([KMB]?)$", s, re.I)
    if not m:
        try:
            return int(float(s))
        except ValueError:
            return -1
    num = float(m.group(1))
    suf = m.group(2).upper()
    mult = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[suf]
    return int(num * mult)


def replies_to_int(s: str) -> int:
    if s is None:
        return -1
    s = s.strip().replace(",", "")
    try:
        return int(s)
    except ValueError:
        return views_to_int(s)


def fetch_with_scrapling(headless: bool = True) -> tuple[int, str, list[dict]]:
    """Returns (status_code, html, xhr_log)."""
    from scrapling.fetchers import StealthyFetcher

    xhr_log: list[dict] = []
    # Scrapling 0.4.7 fetch() - we rely on it to manage the browser internally.
    page = StealthyFetcher.fetch(
        URL,
        solve_cloudflare=True,
        headless=headless,
        network_idle=True,
        humanize=True,
        timeout=90_000,
    )
    status = getattr(page, "status", 0) or 0
    html = getattr(page, "html_content", "") or ""
    return status, html, xhr_log


def extract_threads(html: str) -> list[dict]:
    from scrapling.parser import Selector

    sel = Selector(content=html)
    rows = sel.css("div.structItem--thread")

    def first(node, selector):
        hits = node.css(selector)
        return hits[0] if hits else None

    out: list[dict] = []
    for r in rows:
        title_a = first(r, ".structItem-title a")
        title = (title_a.text or "").strip() if title_a is not None else ""
        href = (title_a.attrib.get("href") or "") if title_a is not None else ""
        if href and not href.startswith("http"):
            href = "https://www.blackhatworld.com" + href

        author_el = first(r, ".structItem-parts .username") or first(
            r, ".structItem-minor .username"
        )
        author = (author_el.text or "").strip() if author_el is not None else ""

        replies_s = ""
        views_s = ""
        dds = r.css(".structItem-cell--meta dl.pairs dd")
        if len(dds) >= 1:
            replies_s = (dds[0].text or "").strip()
        if len(dds) >= 2:
            views_s = (dds[1].text or "").strip()

        t_el = first(r, ".structItem-cell--latest time")
        last_post_iso = ""
        last_post_native = ""
        if t_el is not None:
            last_post_iso = t_el.attrib.get("datetime") or ""
            last_post_native = (t_el.text or "").strip()

        out.append({
            "title": title,
            "thread_url": href,
            "author": author,
            "replies": replies_to_int(replies_s),
            "views": views_to_int(views_s),
            "last_post_date": last_post_iso or last_post_native,
        })
    return out


def is_challenge_page(html: str) -> bool:
    if not html:
        return True
    low = html.lower()
    if "just a moment" in low and "cf_chl_opt" in low:
        return True
    if len(html) < 2000 and "cloudflare" in low:
        return True
    return False


def main() -> int:
    start = time.time()
    print("[Phase 1] Scrapling StealthyFetcher headless=True, solve_cloudflare=True ...")
    status1 = 0
    html1 = ""
    xhr_log: list[dict] = []
    try:
        status1, html1, xhr_log = fetch_with_scrapling(headless=True)
    except Exception as e:  # noqa: BLE001
        print(f"[Phase 1] EXCEPTION: {type(e).__name__}: {e}")
    print(f"[Phase 1] status={status1} bytes={len(html1)} challenge={is_challenge_page(html1)}")

    html = html1
    winning_phase = "Phase 1 (headless Scrapling StealthyFetcher)"
    fetch_count = 1

    # Save page.html unconditionally (honest evidence)
    (OUT_DIR / "page.html").write_text(html or "", encoding="utf-8")

    threads: list[dict] = []
    if html and not is_challenge_page(html):
        print("[Phase 2] Extracting Xenforo thread rows ...")
        threads = extract_threads(html)
        threads = threads[:TARGET_N]
        print(f"[Phase 2] extracted {len(threads)} rows (target={TARGET_N})")
    else:
        print("[Phase 2] SKIPPED — still on challenge / empty")

    # Outputs
    (OUT_DIR / "result.json").write_text(
        json.dumps(threads, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with open(OUT_DIR / "result.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["title", "thread_url", "author", "replies", "views", "last_post_date"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in threads:
            w.writerow(row)

    # xhr_log.json — scrapling fetch() doesn't expose network events directly in 0.4.7,
    # so we emit a truthful stub documenting the browser tier ran.
    (OUT_DIR / "xhr_log.json").write_text(
        json.dumps(
            {
                "note": (
                    "Scrapling 0.4.7 StealthyFetcher.fetch() drives a stealth Playwright browser "
                    "internally with solve_cloudflare=True. Raw request/response events are not "
                    "surfaced by the fetch() API in this version; only the final page object "
                    "(status, html_content) is returned."
                ),
                "tier": "browser (Patchright/Playwright under Scrapling)",
                "final_status": status1,
                "final_bytes": len(html1),
                "events": xhr_log,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    issues: list[str] = []
    if threads:
        urls = [t["thread_url"] for t in threads]
        if len(urls) != len(set(urls)):
            issues.append(f"duplicate URLs: {len(urls) - len(set(urls))}")
        for t in threads:
            if not t["thread_url"].startswith("https://www.blackhatworld.com/"):
                issues.append(f"bad URL domain: {t['thread_url']}")
                break
        missing = [k for k in ("title", "author", "thread_url") if any(not t[k] for t in threads)]
        if missing:
            issues.append(f"rows missing fields: {missing}")

    elapsed = time.time() - start
    print(f"\n=== DONE in {elapsed:.1f}s | phase={winning_phase} | rows={len(threads)} | fetches={fetch_count} ===")
    if issues:
        print("Validation issues:", issues)
    print("WINNING_PHASE:", winning_phase)
    return 0


if __name__ == "__main__":
    sys.exit(main())
