"""Tier A.1 probe: curl_cffi with chrome impersonation against Hyatt.

Per protection-classes.md, Kasada-on-Akamai is expected to return 429/403 with
the Kasada shell (`window.KPSDK`, `/{UUID}/*/ips.js`). If Akamai's TLS layer
rejects the request outright, we see an Error E6020 page instead (the R8
finding: TLS gatekeeps Kasada delivery).

This script performs ONE fetch to corroborate the curl probe.
"""

from curl_cffi import requests

URL = "https://www.hyatt.com/search"
UA = "share-learn-research (contact@example.com)"

r = requests.get(URL, impersonate="chrome120", headers={"User-Agent": UA}, timeout=15)
print(f"status={r.status_code}")
print(f"server-timing={r.headers.get('server-timing')}")
print(f"len={len(r.text)}")
body = r.text
for signal in ("window.KPSDK", "ips.js", "E6020", "Access Denied", "Just a moment"):
    if signal in body:
        print(f"signal-hit: {signal}")
