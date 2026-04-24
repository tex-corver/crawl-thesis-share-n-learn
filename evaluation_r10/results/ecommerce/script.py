"""Scrape the full WooCommerce catalogue at scrapingcourse.com/ecommerce/.

Thesis phase 0 (Tier A): data lives in raw HTML (server-rendered WooCommerce
loop). Tool stack: httpx + parsel. 12 pages × 16 items = 188 products
(last page has 12). Pagination via /page/N/.

Politeness:
    - User-Agent identifies the research contact.
    - 1.5 s sleep between page fetches (> 1 fetch/s).
    - No login, no form submission, no auth.

Run:
    /home/hainm/tmp/share_learn_research/.venv-scrapy/bin/python script.py
"""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import httpx
from parsel import Selector

BASE = "https://www.scrapingcourse.com/ecommerce/"
UA = "share_learn_research-crawl/1.0 (research-contact@example.com)"
TOTAL_PAGES = 12
SLEEP_S = 1.5

OUT_DIR = Path(__file__).parent


def page_url(n: int) -> str:
    """Page 1 is the catalogue root; pages 2+ use /page/N/."""
    return BASE if n == 1 else f"{BASE}page/{n}/"


def parse_products(html: str) -> list[dict[str, str]]:
    sel = Selector(text=html)
    rows: list[dict[str, str]] = []
    for product in sel.css("li.product"):
        anchor = product.css("a.woocommerce-LoopProduct-link")
        name = product.css("h2.woocommerce-loop-product__title::text").get(default="").strip()
        # Fallback: name sometimes appears only in img alt or the anchor img wrapper
        if not name:
            name = product.css("a.woocommerce-LoopProduct-link img::attr(alt)").get(default="").strip()
        product_url = anchor.attrib.get("href", "").strip()
        image_url = anchor.css("img::attr(src)").get(default="").strip()
        # Price: <bdi> typically contains the numeric amount (incl. range for variable products)
        price_nodes = product.css("span.woocommerce-Price-amount bdi ::text").getall()
        # Collapse whitespace and join, e.g. ["$", "69.00"] -> "$69.00"
        price = "".join(part.strip() for part in price_nodes if part.strip())
        if not price:
            # Fallback for outofstock / no-price items
            price = product.css("p.price ::text").getall()
            price = "".join(p.strip() for p in price if p.strip())
        rows.append(
            {
                "name": name,
                "price": price,
                "image_url": image_url,
                "product_url": product_url,
            }
        )
    return rows


def main() -> int:
    headers = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    all_rows: list[dict[str, str]] = []
    last_html = ""

    with httpx.Client(headers=headers, timeout=20.0, follow_redirects=True) as client:
        for n in range(1, TOTAL_PAGES + 1):
            url = page_url(n)
            r = client.get(url)
            r.raise_for_status()
            last_html = r.text
            rows = parse_products(r.text)
            print(f"page {n:2d} ({url}) -> {len(rows)} products")
            all_rows.extend(rows)
            if n < TOTAL_PAGES:
                time.sleep(SLEEP_S)

    # Persist final page body for audit (page.html)
    (OUT_DIR / "page.html").write_text(last_html, encoding="utf-8")

    # Write JSON
    (OUT_DIR / "result.json").write_text(
        json.dumps(all_rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Write CSV
    with (OUT_DIR / "result.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "price", "image_url", "product_url"])
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nTOTAL: {len(all_rows)} products written to {OUT_DIR}")
    return 0 if all_rows else 1


if __name__ == "__main__":
    sys.exit(main())
