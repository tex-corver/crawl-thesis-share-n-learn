"""Shopee /search?keyword=laptop — Round 10 evaluation (/crawl skill, R5 precedent).

Thesis classification: application-layer protection (silent login requirement
enforced at API layer, error 90309999). Per R5 + R9 evidence, free/local tools
cannot bypass this. This driver attempts the calibrated ladder honestly and
records the failure mode. See mechanism.md for L1..L6.

Re-runnable. Uses research-contact UA. Respects robots.txt crawl-delay.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent
UA = (
    "Mozilla/5.0 (compatible; share-learn-research-contact; "
    "https://git.urieljsc.com/research)"
)
TARGET = "https://shopee.sg/search?keyword=laptop"
API = (
    "https://shopee.sg/api/v4/search/search_items"
    "?by=relevancy&keyword=laptop&limit=30&newest=0"
    "&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2"
)


def phase0_plain_http() -> dict[str, object]:
    """Phase 0: curl-equivalent probe. Already proven in orchestrator run.

    Returns observed classification signals.
    """
    import urllib.request

    req = urllib.request.Request(TARGET, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="replace")
        status = resp.status
        final_url = resp.geturl()
    has_next_data = "__NEXT_DATA__" in html
    has_initial = "__INITIAL_STATE__" in html
    redirected_to_login = "login" in final_url.lower()
    (OUTPUT / "page.html").write_text(html, encoding="utf-8")
    return {
        "phase": "phase0_plain_http",
        "status": status,
        "final_url": final_url,
        "has_next_data": has_next_data,
        "has_initial_state": has_initial,
        "redirected_to_login": redirected_to_login,
        "size": len(html),
    }


def phase0_api_probe() -> dict[str, object]:
    """Probe the documented v4 API. App-layer: error 90309999 means login-required."""
    import urllib.request

    req = urllib.request.Request(
        API,
        headers={
            "User-Agent": UA,
            "Referer": "https://shopee.sg/search?keyword=laptop",
            "X-API-SOURCE": "pc",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        status = e.code
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        parsed = {"_raw": body[:400]}
    return {
        "phase": "phase0_api_probe",
        "status": status,
        "body": parsed,
    }


def phase1_browser_warmed() -> dict[str, object]:
    """Phase 1: Scrapling StealthyFetcher — homepage-first warming then target.

    Per thesis Phase 4 decision tree: for app-layer silent-redirect, homepage-first
    warming is the last honest free attempt. If still blocked, Tier C.
    """
    try:
        from scrapling.fetchers import StealthyFetcher
    except ImportError as e:
        return {"phase": "phase1_browser_warmed", "error": f"scrapling not available: {e}"}

    xhr_log: list[dict[str, object]] = []

    def page_action(page):
        # capture the XHR graph on the SEARCH page
        def on_response(resp):
            try:
                xhr_log.append({
                    "url": resp.url,
                    "status": resp.status,
                    "content_type": resp.headers.get("content-type", ""),
                })
            except Exception:  # noqa: BLE001
                pass

        page.on("response", on_response)
        # Warm homepage first
        page.goto("https://shopee.sg/", wait_until="domcontentloaded", timeout=40_000)
        page.wait_for_timeout(3000)
        # Navigate to target
        page.goto(TARGET, wait_until="domcontentloaded", timeout=40_000)
        page.wait_for_timeout(5000)
        return page

    try:
        result = StealthyFetcher.fetch(
            TARGET,
            headless=True,
            humanize=True,
            real_chrome=False,
            solve_cloudflare=False,  # not CF
            page_action=page_action,
            network_idle=False,
            timeout=60_000,
        )
        html = result.html_content if hasattr(result, "html_content") else str(result)
        (OUTPUT / "page_warmed.html").write_text(html, encoding="utf-8")
        (OUTPUT / "xhr_log.json").write_text(
            json.dumps(xhr_log, indent=2, default=str), encoding="utf-8"
        )
        return {
            "phase": "phase1_browser_warmed",
            "size": len(html),
            "xhr_count": len(xhr_log),
            "final_url": getattr(result, "url", TARGET),
            "status": getattr(result, "status", None),
        }
    except Exception as e:  # noqa: BLE001
        return {"phase": "phase1_browser_warmed", "error": repr(e)}


def main() -> int:
    findings: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []

    print("[Phase 0a] plain HTTP GET of search URL", file=sys.stderr)
    findings.append(phase0_plain_http())

    time.sleep(11)
    print("[Phase 0b] documented v4 API probe", file=sys.stderr)
    findings.append(phase0_api_probe())

    # Only run browser tier if explicitly requested (costs a fetch budget slot)
    if "--browser" in sys.argv:
        time.sleep(11)
        print("[Phase 1] Scrapling browser with homepage warming", file=sys.stderr)
        findings.append(phase1_browser_warmed())

    # Parse API probe outcome
    api_finding = findings[1]
    api_body = api_finding.get("body") if isinstance(api_finding, dict) else None
    is_applayer_blocked = (
        isinstance(api_body, dict)
        and api_body.get("error") == 90309999
        and api_body.get("is_login") is False
    )

    outcome = {
        "target": TARGET,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ua": UA,
        "findings": findings,
        "rows_extracted": len(rows),
        "verdict": (
            "FAIL — application-layer protection (error 90309999, login required). "
            "Per thesis R5/R9 evidence, free tools cannot bypass. Tier-C required."
            if is_applayer_blocked
            else "INCONCLUSIVE — see findings"
        ),
    }
    (OUTPUT / "result.json").write_text(json.dumps([], indent=2), encoding="utf-8")
    (OUTPUT / "findings.json").write_text(
        json.dumps(outcome, indent=2, default=str), encoding="utf-8"
    )

    # Empty CSV with header only
    (OUTPUT / "result.csv").write_text(
        "name,price,image_url,product_url\n", encoding="utf-8"
    )

    print(json.dumps(outcome, indent=2, default=str))
    return 0 if is_applayer_blocked else 1  # blocked-as-expected is "success" for the probe


if __name__ == "__main__":
    raise SystemExit(main())
