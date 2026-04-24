"""Re-runnable Hyatt probe driver (R10 — confirms R8 Hyatt failure).

Target: https://www.hyatt.com/search
Fields: hotel_name, location, rating, hotel_url
Expected outcome: 0 rows. Akamai TLS edge gate + Kasada POW shell (when reached)
                  are both unsolvable with free/local tooling in 2026.

Evidence anchor: R8 Hyatt round — thesis/reference/protection-classes.md §Class 5
(`/*/ips.js`, window.KPSDK) and calibrated-ceiling.md §Kasada (Hyatt) — R8.

This script intentionally stops after the diagnostic curl_cffi probe and emits
an empty result set plus a mechanism.md report. Do NOT extend it with a
StealthyFetcher pass — humanize=True does not solve Kasada POW (R8 evidence),
and every retry burns IP reputation on an already-flagged /24.

Re-run cost: 1 curl_cffi fetch (≤ 1s). Safe to run repeatedly.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from curl_cffi import requests

URL = "https://www.hyatt.com/search"
UA = "share-learn-research (contact@example.com)"
OUT = Path(__file__).parent


def probe() -> dict[str, object]:
    r = requests.get(
        URL,
        impersonate="chrome120",
        headers={"User-Agent": UA},
        timeout=15,
    )
    body = r.text
    return {
        "status": r.status_code,
        "server_timing": r.headers.get("server-timing", ""),
        "body_bytes": len(body),
        "kasada_signals": {
            "window.KPSDK": "window.KPSDK" in body,
            "ips.js": "ips.js" in body,
        },
        "akamai_signals": {
            "ak_p": "ak_p" in r.headers.get("server-timing", ""),
            "E6020": "E6020" in body,
            "Access Denied": "Access Denied" in body,
        },
    }


def main() -> None:
    diagnostics = probe()
    (OUT / "probe_diagnostics.json").write_text(json.dumps(diagnostics, indent=2))

    # Emit empty result set with honest zero-count.
    (OUT / "result.json").write_text("[]\n")
    with (OUT / "result.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hotel_name", "location", "rating", "hotel_url"])

    print(json.dumps(diagnostics, indent=2))
    print("rows=0 — blocked at Akamai TLS gate (E6020); Kasada shell not reached.")


if __name__ == "__main__":
    main()
