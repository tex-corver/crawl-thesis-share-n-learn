"""Tier-B StealthyFetcher attempt against G2 DataDome.

Per thesis R8 evidence, this will fail. StealthyFetcher solves Cloudflare
Turnstile but has no solver for DataDome's CAPTCHA (t='fe').
"""

import json
import time
from pathlib import Path

from scrapling.fetchers import StealthyFetcher

URL = "https://www.g2.com/categories/crm"
OUT = Path(__file__).parent

print("=== Tier-B: Scrapling StealthyFetcher (humanize, real_chrome) ===")
xhr_log = []


def _capture(route, request):
    try:
        xhr_log.append(
            {
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
            }
        )
    except Exception:  # noqa: BLE001
        pass
    route.continue_()


t0 = time.time()
try:
    page = StealthyFetcher.fetch(
        URL,
        headless=True,
        humanize=True,
        real_chrome=False,  # set False for non-interactive run; full attempt below if avail
        solve_cloudflare=False,  # not a CF challenge -- DataDome
        network_idle=True,
        timeout=45_000,
        wait=3000,
    )
    elapsed = time.time() - t0
    print(f"status={page.status} elapsed={elapsed:.1f}s")
    print(f"body_bytes={len(page.html_content or '')}")
    body = page.html_content or ""
    markers = ["captcha-delivery", "Please enable JS", "geo.captcha", "ct.captcha"]
    found = [m for m in markers if m in body]
    has_real_crm = ("Salesforce" in body) or ("HubSpot" in body) or ("Zoho" in body)
    print(f"datadome_markers={found}")
    print(f"contains_real_crm_brand={has_real_crm}")
    (OUT / "stealthy_body.html").write_text(body[:5000])
    (OUT / "stealthy_xhr.json").write_text(json.dumps(xhr_log, indent=2))
except Exception as exc:  # noqa: BLE001
    print(f"EXCEPTION: {type(exc).__name__}: {exc}")
    (OUT / "stealthy_error.txt").write_text(f"{type(exc).__name__}: {exc}")
