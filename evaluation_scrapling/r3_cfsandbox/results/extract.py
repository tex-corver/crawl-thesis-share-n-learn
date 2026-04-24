"""R3-Scrapling benchmark — Cloudflare managed challenge sandbox.

Target: https://www.scrapingcourse.com/cloudflare-challenge
Tool: Scrapling StealthyFetcher(solve_cloudflare=True, headless=True)
Run with: /home/hainm/tmp/share_learn_research/.venv-scrapling/bin/python extract.py
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from scrapling.fetchers import StealthyFetcher

URL = "https://www.scrapingcourse.com/cloudflare-challenge"
OUTDIR = Path(__file__).parent


def attempt(humanize: bool) -> tuple[object, float]:
    t0 = time.monotonic()
    page = StealthyFetcher.fetch(
        URL,
        solve_cloudflare=True,
        headless=True,
        network_idle=True,
        humanize=humanize,
    )
    return page, time.monotonic() - t0


def _as_str(body: object) -> str:
    if isinstance(body, bytes):
        return body.decode("utf-8", errors="replace")
    return body or ""  # type: ignore[return-value]


def extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_h1(html: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    raw = match.group(1)
    return re.sub(r"<[^>]+>", "", raw).strip()


def _extract_paragraph(html: str) -> str:
    # Look for the success banner first (h2), then any p/h2 with visible text.
    for tag in ("h2", "p"):
        for match in re.finditer(
            rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.IGNORECASE | re.DOTALL,
        ):
            text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            if len(text) > 20:
                return text[:300]
    return ""


def main() -> None:
    attempts: list[dict[str, object]] = []
    page = None
    elapsed = 0.0

    for idx, humanize in enumerate([False, True], start=1):
        try:
            page, elapsed = attempt(humanize=humanize)
            status = getattr(page, "status", None)
            html = _as_str(getattr(page, "body", ""))
            title = extract_title(html)
            attempts.append(
                {
                    "attempt": idx,
                    "humanize": humanize,
                    "status": status,
                    "title": title,
                    "body_kb": round(len(html) / 1024, 2),
                    "elapsed_s": round(elapsed, 2),
                },
            )
            if status == 200 and "Just a moment" not in title:
                break
        except Exception as exc:  # noqa: BLE001 — benchmark must record anything
            attempts.append(
                {
                    "attempt": idx,
                    "humanize": humanize,
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )

    if page is None:
        (OUTDIR / "result.json").write_text(
            json.dumps({"status": "FAIL", "attempts": attempts}, indent=2),
        )
        print("FAIL — see result.json")
        return

    html = _as_str(getattr(page, "body", ""))
    title = extract_title(html)
    h1 = extract_h1(html)
    paragraph = _extract_paragraph(html)
    url_after = getattr(page, "url", URL)
    status = getattr(page, "status", None)
    snippet = html[:500]

    result = {
        "status": status,
        "page_title": title,
        "h1": h1,
        "sample_paragraph": paragraph,
        "body_length_kb": round(len(html) / 1024, 2),
        "solve_seconds": round(elapsed, 2),
        "url_after_solve": url_after,
        "attempts": attempts,
        "outcome": (
            "PASS"
            if status == 200 and "Just a moment" not in title and len(html) > 2048
            else "FAIL"
        ),
    }
    (OUTDIR / "result.json").write_text(json.dumps(result, indent=2))
    (OUTDIR / "page_snippet.txt").write_text(snippet)
    (OUTDIR / "page.html").write_text(html)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
