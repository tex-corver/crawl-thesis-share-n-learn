#!/usr/bin/env python
"""R4-Scrapling — scrapingcourse/ecommerce catalogue.

Extract 188 products across 12 WooCommerce paginated pages using Scrapling's
`Fetcher` (no Cloudflare-managed challenge on this endpoint; HTTP 200 straight
from Phase 0 probe).

Defensive selector logic to avoid the R4 pitfall where naive `.amount` selection
concatenates regular+sale prices into garbage like "32.0024.00":
  - Scope all amount lookups INSIDE each `li.product` card (skips site-header cart).
  - When a card has `<ins>`, read sale price from `ins .amount bdi` and regular
    from `del .amount bdi`; else single `.amount bdi` = regular price, sale=None.
  - Validate with regex `\\d+\\.\\d{2}\\d` to catch any concat garbage post-parse.
"""
from __future__ import annotations

import csv
import json
import re
import time
from decimal import Decimal
from pathlib import Path

from scrapling.fetchers import Fetcher

OUT = Path(__file__).parent
LISTING = "https://www.scrapingcourse.com/ecommerce/"
PAGE_TPL = "https://www.scrapingcourse.com/ecommerce/page/{n}/"
TOTAL_PAGES = 12
UA = "Mozilla/5.0 (R4-Scrapling-research; hainguyen@urieljsc.com)"
POLITE_DELAY_S = 1.2

CONCAT_GUARD = re.compile(r"\d+\.\d{2}\d")  # flags e.g. "32.0024.00"


def _parse_amount(node) -> Decimal | None:
    """Read '$69.00' → Decimal('69.00') from a <span class='amount'> element.

    Uses `.get_all_text()` then strips currency symbol and commas.
    """
    if node is None:
        return None
    raw = node.get_all_text(strip=True)
    cleaned = raw.replace("$", "").replace(",", "").strip()
    if not cleaned:
        return None
    if CONCAT_GUARD.search(cleaned):
        raise ValueError(f"Concatenated price detected: {raw!r}")
    return Decimal(cleaned)


def _first(sel, css: str):
    """Return first matching selector element or None (Scrapling has no css_first)."""
    got = sel.css(css)
    return got[0] if got else None


def extract_page(page, url: str) -> list[dict]:
    """Extract all .woocommerce-loop-product cards from one listing page."""
    cards = page.css("li.product")
    rows: list[dict] = []
    for card in cards:
        # Name
        title_el = _first(card, "h2.woocommerce-loop-product__title")
        if title_el is None:
            continue
        name = title_el.get_all_text(strip=True)

        # Product URL
        link_el = _first(card, "a.woocommerce-loop-product__link")
        product_url = link_el.attrib.get("href") if link_el else None

        # Prices — prefer <ins> for sale, <del> for regular, else single .amount
        ins_amount = _first(card, "ins .woocommerce-Price-amount.amount")
        del_amount = _first(card, "del .woocommerce-Price-amount.amount")

        if ins_amount is not None:
            sale_price = _parse_amount(ins_amount)
            regular_price = _parse_amount(del_amount) if del_amount else None
        else:
            sale_price = None
            # Scope to the price span (not the image area / header cart)
            single_amount = _first(
                card, "span.price .woocommerce-Price-amount.amount"
            )
            regular_price = _parse_amount(single_amount)

        rows.append(
            {
                "name": name,
                "price_usd": str(regular_price) if regular_price is not None else None,
                "sale_price_usd": str(sale_price) if sale_price is not None else None,
                "product_url": product_url,
            }
        )
    return rows


def main() -> None:
    t0 = time.perf_counter()
    all_rows: list[dict] = []
    per_page_counts: list[tuple[int, int, str]] = []

    for n in range(1, TOTAL_PAGES + 1):
        url = LISTING if n == 1 else PAGE_TPL.format(n=n)
        if n > 1:
            time.sleep(POLITE_DELAY_S)
        # Scrapling Fetcher — plain HTTP, no browser needed.
        # follow_redirects=True so `/ecommerce/` is OK; `impersonate` nudges TLS.
        page = Fetcher.get(
            url,
            headers={"User-Agent": UA},
            follow_redirects=True,
            timeout=30,
        )
        status = getattr(page, "status", None)
        rows = extract_page(page, url)
        per_page_counts.append((n, len(rows), f"HTTP:{status}"))
        all_rows.extend(rows)
        print(f"  page {n:>2}: {len(rows):>2} products  (HTTP {status})  {url}")

    wall = time.perf_counter() - t0

    # Validation
    flags: list[str] = []
    if len(all_rows) != 188:
        flags.append(f"row_count != 188 (got {len(all_rows)})")
    null_name = [r for r in all_rows if not r["name"]]
    null_price = [r for r in all_rows if not r["price_usd"]]
    if null_name:
        flags.append(f"{len(null_name)} rows have null name")
    if null_price:
        flags.append(f"{len(null_price)} rows have null price_usd")
    # Concat-guard sweep on serialized form
    for r in all_rows:
        for field in ("price_usd", "sale_price_usd"):
            v = r.get(field)
            if v and CONCAT_GUARD.search(v):
                flags.append(f"concat price suspect in {field}: {r['name']}={v}")
    # Unique product_url
    urls = [r["product_url"] for r in all_rows if r["product_url"]]
    if len(set(urls)) != len(urls):
        flags.append(f"duplicate product_urls: {len(urls)} vs {len(set(urls))}")

    # Persist
    (OUT / "result.json").write_text(json.dumps(all_rows, indent=2))
    with (OUT / "result.csv").open("w", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["name", "price_usd", "sale_price_usd", "product_url"]
        )
        w.writeheader()
        w.writerows(all_rows)

    print()
    print(f"rows: {len(all_rows)} / 188")
    print(f"wall-clock: {wall:.1f} s")
    if flags:
        print("FLAGS:")
        for f in flags:
            print(f"  - {f}")
    else:
        print("FLAGS: (none)")

    # Stash per-page counts for mechanism.md
    (OUT / "_per_page.json").write_text(
        json.dumps(
            {
                "per_page": per_page_counts,
                "total": len(all_rows),
                "wall_seconds": round(wall, 2),
                "flags": flags,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
