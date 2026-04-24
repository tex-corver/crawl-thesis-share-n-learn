"""R10 — Lowe's Akamai Bot Manager probe (thesis Tier A.1 ladder).

Target: https://www.lowes.com/pl/Lawn-mowers-Outdoor-power-equipment-Outdoors/4294857935

Per the thesis (crawl-thesis/reference/protection-classes.md#class-6),
Akamai is a "mixed" free-tier class:
  - Tier A.1: curl_cffi with varied impersonate profiles.
    R8 Lowe's evidence: safari18_0 got HTTP 200 but with SENSOR page, not products.
  - Tier A.2: + Referer Google.
  - Tier B:  all browser tiers detected pre-sensor.
  - Tier C:  residential proxy / vendor API.

We run profiles in the order the thesis recommends and distinguish:
  - 403 edge-deny (~450 B Access Denied page) — Akamai won't even serve sensor
  - 200 with sensor script (~2.5 KB, contains '_abck', 'akamai', 'sensor_data')
  - 200 with products (body contains product tiles / __NEXT_DATA__ etc.)

Budget: ≤ 6 fetches total. ≥ 10 s between retries.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from curl_cffi import requests as cffi_requests

URL = "https://www.lowes.com/pl/Lawn-mowers-Outdoor-power-equipment-Outdoors/4294857935"
OUT = Path(__file__).resolve().parent
UA_SUFFIX = "share-learn-research (contact@urieljsc.com)"

PROFILES = [
    ("safari18_0", None),    # R8 best-hope profile
    ("chrome131", None),
    ("firefox135", None),
    ("chrome120", None),
    ("safari18_0", "https://www.google.com/"),  # Tier A.2 + Google referer
]


def classify_body(status: int, body: bytes, headers: dict) -> str:
    if status == 403:
        if b"Access Denied" in body and len(body) < 1000:
            return "edge_deny_akamai"
        return f"403_other_{len(body)}"
    if status != 200:
        return f"status_{status}"
    text = body[:8000].decode("utf-8", errors="replace")
    # Product markers
    if "__NEXT_DATA__" in text or "productTile" in text or "itemCardContainer" in text:
        return "products_present"
    # Sensor / challenge markers
    if "_abck" in text or "sensor_data" in text or "bm-verify" in text or "bot_detection" in text:
        return "sensor_page"
    if "Access Denied" in text:
        return "soft_deny_200"
    if len(body) < 3000:
        return f"small_body_{len(body)}"
    return "unknown_200"


def run() -> list[dict]:
    results = []
    for idx, (profile, referer) in enumerate(PROFILES):
        if idx > 0:
            time.sleep(12)  # polite spacing, ≥ 10 s between retries
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none" if not referer else "cross-site",
            "Sec-Fetch-User": "?1",
            "X-Research-Contact": UA_SUFFIX,
        }
        if referer:
            headers["Referer"] = referer
            headers["Sec-Fetch-Site"] = "cross-site"
        try:
            resp = cffi_requests.get(
                URL,
                impersonate=profile,
                headers=headers,
                timeout=25,
                allow_redirects=True,
            )
            status = resp.status_code
            body = resp.content or b""
            verdict = classify_body(status, body, dict(resp.headers))
            results.append({
                "attempt": idx + 1,
                "profile": profile,
                "referer": referer,
                "status": status,
                "bytes": len(body),
                "verdict": verdict,
                "akamai_grn": resp.headers.get("akamai-grn"),
                "server_timing": resp.headers.get("server-timing"),
            })
            # Save last body for inspection
            (OUT / f"page_attempt_{idx+1}_{profile}.html").write_bytes(body[:200_000])
            print(f"  [{idx+1}] {profile:12s} referer={bool(referer)} -> {status} ({len(body)} B) :: {verdict}")
            if verdict == "products_present":
                print("    ==> BREAKTHROUGH, stopping ladder")
                break
        except Exception as e:  # noqa: BLE001
            results.append({
                "attempt": idx + 1,
                "profile": profile,
                "referer": referer,
                "error": repr(e),
            })
            print(f"  [{idx+1}] {profile:12s} ERROR: {e!r}")
    return results


def extract_products(body: bytes) -> list[dict]:
    """Attempt to extract products from a 200 body.

    For R10 we never reach this; it's here for completeness so the script
    documents the intended extraction path.
    """
    text = body.decode("utf-8", errors="replace")
    m = re.search(r"<script[^>]+id=\"__NEXT_DATA__\"[^>]*>(.*?)</script>", text, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except Exception:  # noqa: BLE001
        return []
    # Shape is Next.js-dependent; best-effort walk.
    products = []
    def walk(obj):
        if isinstance(obj, dict):
            if "productDetailUrl" in obj or "itemNumber" in obj:
                products.append({
                    "product_name": obj.get("productTitle") or obj.get("title") or obj.get("name", ""),
                    "price": (obj.get("price") or {}).get("finalPrice") if isinstance(obj.get("price"), dict) else obj.get("price"),
                    "image_url": obj.get("imageUrl") or obj.get("image"),
                    "product_url": obj.get("productDetailUrl") or obj.get("url"),
                })
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(data)
    return products


if __name__ == "__main__":
    print(f"Target: {URL}")
    print(f"Profiles ladder: {[p for p, _ in PROFILES]}")
    print()

    attempts = run()

    summary = {
        "target": URL,
        "protection_class": "akamai_bot_manager",
        "attempts": attempts,
        "winner": next((a for a in attempts if a.get("verdict") == "products_present"), None),
    }
    (OUT / "xhr_log.json").write_text(json.dumps(summary, indent=2))

    # result.json / result.csv — empty per honest failure
    products: list[dict] = []
    # if any attempt returned products, try to extract
    for a in attempts:
        if a.get("verdict") == "products_present":
            path = OUT / f"page_attempt_{a['attempt']}_{a['profile']}.html"
            products = extract_products(path.read_bytes())
            break

    (OUT / "result.json").write_text(json.dumps(products, indent=2))
    csv_header = "product_name,price,image_url,product_url\n"
    csv_rows = "".join(
        f"{p.get('product_name','')},{p.get('price','')},{p.get('image_url','')},{p.get('product_url','')}\n"
        for p in products
    )
    (OUT / "result.csv").write_text(csv_header + csv_rows)

    print()
    print(f"Products extracted: {len(products)}")
    print(f"Outputs in: {OUT}")
