"""Tier-A Fetcher attempt against G2 DataDome.

Per thesis R8 precedent, this is expected to fail. Full-enforcement DataDome
blocks TLS fingerprint at edge before browser tier can even execute.
"""

from scrapling.fetchers import Fetcher

URL = "https://www.g2.com/categories/crm"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 research-contact"

print("=== Tier-A: Scrapling Fetcher with impersonate=chrome124 ===")
try:
    page = Fetcher.get(URL, impersonate="chrome124", timeout=30)
    print(f"status={page.status}")
    print(f"body_bytes={len(page.html_content or '')}")
    head = (page.html_content or "")[:500]
    print(f"head={head!r}")
    # Check for DataDome CAPTCHA markers
    markers = ["captcha-delivery", "Please enable JS", "x-dd-b", "t:'bv'", "t:'fe'"]
    found = [m for m in markers if m in (page.html_content or "")]
    print(f"datadome_markers={found}")
except Exception as exc:  # noqa: BLE001
    print(f"EXCEPTION: {type(exc).__name__}: {exc}")
