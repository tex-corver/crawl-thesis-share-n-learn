"""Re-runnable driver for the G2 /categories/crm crawl attempt.

Status: BLOCKED at DataDome. Free tools cannot bypass DataDome full-enforcement.
This script preserves the ladder we attempted so the failure can be reproduced.

Ladder (each step confirmed fail in this run):
  1. curl with UA                     -> HTTP 403, x-datadome: protected
  2. Scrapling Fetcher impersonate=chrome124 -> HTTP 403, DataDome interstitial
  3. Scrapling StealthyFetcher (humanize=True) -> HTTP 403, DataDome interstitial

Recommendation: Tier-C paid vendor (Scrapfly / ZenRows / Bright Data) with
published DataDome-bypass track record, or Tier-D partner/Cloudflare AI
Crawl Control (only if G2 has opted in, which they have not as of 2026-04).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

URL = "https://www.g2.com/categories/crm"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 research-contact"
OUT = Path(__file__).parent


def tier0_curl() -> tuple[int, str]:
    """Phase 0 probe — cheap curl for classification."""
    result = subprocess.run(  # noqa: S603
        ["curl", "-sI", "-A", UA, URL],  # noqa: S607
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    headers = result.stdout
    status = 0
    for line in headers.splitlines():
        if line.startswith("HTTP/") and "403" in line:
            status = 403
        elif line.startswith("HTTP/") and "200" in line:
            status = 200
    return status, headers


def tier_a_fetcher() -> dict[str, object]:
    """Scrapling Fetcher + chrome124 TLS impersonation."""
    from scrapling.fetchers import Fetcher

    page = Fetcher.get(URL, impersonate="chrome124", timeout=30)
    body = page.html_content or ""
    return {
        "tier": "A",
        "tool": "Scrapling.Fetcher(impersonate=chrome124)",
        "status": page.status,
        "body_bytes": len(body),
        "datadome_markers": [m for m in ["captcha-delivery", "Please enable JS"] if m in body],
    }


def tier_b_stealthy() -> dict[str, object]:
    """Scrapling StealthyFetcher + humanize."""
    from scrapling.fetchers import StealthyFetcher

    page = StealthyFetcher.fetch(
        URL,
        headless=True,
        humanize=True,
        real_chrome=False,
        solve_cloudflare=False,
        network_idle=True,
        timeout=45_000,
        wait=3000,
    )
    body = page.html_content or ""
    return {
        "tier": "B",
        "tool": "Scrapling.StealthyFetcher(humanize=True)",
        "status": page.status,
        "body_bytes": len(body),
        "datadome_markers": [
            m for m in ["captcha-delivery", "geo.captcha", "ct.captcha"] if m in body
        ],
    }


def main() -> int:
    ladder_results: list[dict[str, object]] = []

    status, headers = tier0_curl()
    is_datadome = "x-datadome" in headers.lower() or "x-dd-b" in headers.lower()
    ladder_results.append(
        {
            "tier": "0",
            "tool": "curl",
            "status": status,
            "is_datadome": is_datadome,
        }
    )
    print(json.dumps(ladder_results[-1], indent=2))

    if not is_datadome:
        print("UNEXPECTED: DataDome signal missing. Rerun classification.")
        return 2

    # Per thesis: DataDome => Tier C. We try Tier A and Tier B only to DOCUMENT
    # the failure mode, not hoping for success.
    time.sleep(10)  # ethics: ≥10s between fetches
    ladder_results.append(tier_a_fetcher())
    print(json.dumps(ladder_results[-1], indent=2))

    time.sleep(10)
    ladder_results.append(tier_b_stealthy())
    print(json.dumps(ladder_results[-1], indent=2))

    (OUT / "ladder_results.json").write_text(json.dumps(ladder_results, indent=2))
    print("BLOCKED at DataDome. Recommend Tier C.", file=sys.stderr)
    return 1  # non-zero: honest failure


if __name__ == "__main__":
    sys.exit(main())
