#!/usr/bin/env python3
"""Generic scorer for thesis runs. Configure with a checklist.yml.

Usage:
    python score_template.py <checklist.yml> <output_dir>

Produces score.json alongside result.json.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def is_numeric_or_parseable_price(v) -> bool:
    if isinstance(v, (int, float)) and math.isfinite(v) and v > 0:
        return True
    if isinstance(v, str):
        m = re.search(r"\d+[\d,\.]*", v)
        if m:
            try:
                return float(m.group(0).replace(",", "")) > 0
            except ValueError:
                return False
    return False


def score_correctness(rows: list, mech: str, checklist: dict) -> dict:
    out = {}
    criteria = checklist.get("correctness", [])
    target_n = None
    required_fields = None
    primary_key = None

    # Parse from checklist
    for c in criteria:
        if c.get("name") == "required_fields_present":
            required_fields = c.get("fields") or []
        if c.get("name") == "unique_keys":
            m = re.search(r"duplicate (\w+)", c.get("check", ""))
            if m:
                primary_key = m.group(1)

    expected_n = None
    for c in criteria:
        if c.get("name") == "row_count":
            m = re.search(r"exactly (\d+)", c.get("check", ""))
            if m:
                expected_n = int(m.group(1))

    # Score each id
    for c in criteria:
        cid = c["id"]
        name = c.get("name")
        check = c.get("check", "")

        if name == "row_count":
            out[cid] = (expected_n is None or len(rows) == expected_n, f"got {len(rows)} rows (expected {expected_n})")
        elif name == "required_fields_present":
            bad = []
            for i, r in enumerate(rows):
                for f in required_fields or []:
                    if not r.get(f):
                        bad.append((i, f))
                        break
                if bad:
                    break
            out[cid] = (not bad, f"missing at row {bad[0]}" if bad else "ok")
        elif name == "anchor_sanity":
            m = re.search(r"'([^']+)' appears", check)
            anchor = m.group(1) if m else None
            if anchor:
                hit = any(anchor.lower() in str(r).lower() for r in rows)
                out[cid] = (hit, f"anchor '{anchor}' found" if hit else f"anchor '{anchor}' missing")
            else:
                out[cid] = (True, "anchor not specified")
        elif name == "unique_keys":
            if primary_key and rows:
                keys = [r.get(primary_key) for r in rows]
                dupes = len(keys) - len(set(keys))
                out[cid] = (dupes == 0, f"{dupes} duplicates" if dupes else f"{len(keys)} unique")
            else:
                out[cid] = (True, "no primary key to check")
        elif name == "types_valid":
            m = re.search(r"all (\w+)", check)
            field = m.group(1) if m else None
            if field and rows:
                bad = [i for i, r in enumerate(rows) if not is_numeric_or_parseable_price(r.get(field))]
                out[cid] = (not bad, f"bad at rows {bad[:3]}" if bad else "ok")
            else:
                out[cid] = (True, "no numeric field specified")
        elif name == "urls_canonical":
            m = re.search(r"all (\w+)", check)
            field = m.group(1) if m else None
            dom_m = re.search(r"under the target domain", check)
            domain = checklist.get("entry_url", "").split("//")[-1].split("/")[0] if dom_m else None
            if field and domain and rows:
                bad = [i for i, r in enumerate(rows)
                       if not (isinstance(r.get(field), str) and domain in r[field])]
                out[cid] = (not bad, f"bad at rows {bad[:3]}" if bad else "ok")
            else:
                out[cid] = (True, "no URL check")
        elif name == "mechanism_reported":
            L_present = [lbl for lbl in ("L1", "L2", "L3", "L4", "L5", "L6")
                         if re.search(rf"##\s*{lbl}\b", mech)]
            out[cid] = (len(L_present) >= 4 and len(mech) > 200,
                        f"{len(mech)} chars, L-sections {L_present}")
        elif name == "no_paid_service":
            markers = c.get("negative_markers", [])
            hit = [m for m in markers if m in mech.lower()]
            out[cid] = (not hit, f"markers {hit}" if hit else "clean")
        else:
            out[cid] = (True, "no scorer for this check")

    passed = sum(1 for ok, _ in out.values() if ok)
    scoring = checklist.get("scoring", {})
    # Simple PASS/PARTIAL/FAIL heuristic
    level = "PASS" if passed == len(out) else ("PARTIAL" if out.get("C1", (False, ""))[0] else "FAIL")
    return {"checks": {k: {"pass": ok, "note": msg} for k, (ok, msg) in out.items()},
            "passed": f"{passed}/{len(out)}",
            "level": level}


def score_lifecycle(mech: str) -> dict:
    scores = {}
    for lbl, strong, weak in [
        ("L1", ["robots.txt", "api docs", "documentation"], ["check", "research", "read"]),
        ("L2", ["ssr", "xhr", "__next_data__", "public api", "endpoint"], ["fetch", "request"]),
        ("L3", ["schema", "anchor", "cross-check", "compare"], ["verify", "validate"]),
        ("L4", ["rate limit", "concurrency", "autothrottle", "retry", "pagination"], ["throttle"]),
        ("L5", ["csv", "json", "metadata", "feeds"], ["save", "write"]),
        ("L6", ["escalate", "retry", "fallback", "tier"], ["try", "attempt"]),
    ]:
        m = re.search(rf"##\s*{lbl}[^\n]*\n(.*?)(?=\n##\s|\Z)", mech, re.S)
        text = m.group(1).strip() if m else ""
        tl = text.lower()
        s = sum(1 for k in strong if k in tl)
        w = sum(1 for k in weak if k in tl)
        if not text:
            scores[lbl] = (0, "missing")
        elif len(text) < 40:
            scores[lbl] = (1, "stub")
        elif s >= 2:
            scores[lbl] = (5, f"{s} strong")
        elif s == 1:
            scores[lbl] = (4, f"1 strong+{w} weak")
        elif w >= 2:
            scores[lbl] = (3, f"{w} weak")
        else:
            scores[lbl] = (2, "generic")
    return scores


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: score_template.py <checklist.yml> <output_dir>")
    checklist_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])

    checklist = yaml.safe_load(checklist_path.read_text())
    result_path = out_dir / "result.json"
    mech_path = out_dir / "mechanism.md"

    rows = []
    if result_path.exists():
        try:
            rows = json.loads(result_path.read_text())
            if not isinstance(rows, list):
                rows = []
        except Exception as e:
            print(f"result.json unreadable: {e}")

    mech = mech_path.read_text() if mech_path.exists() else ""

    correctness = score_correctness(rows, mech, checklist)
    lifecycle = score_lifecycle(mech)

    report = {
        "target": checklist.get("benchmark"),
        "correctness": correctness,
        "lifecycle": {k: {"score": s, "note": n} for k, (s, n) in lifecycle.items()},
        "lifecycle_total": sum(s for s, _ in lifecycle.values()),
    }
    (out_dir / "score.json").write_text(json.dumps(report, indent=2, default=str))
    print(f"[{checklist.get('benchmark')}] {correctness['level']} correctness={correctness['passed']} lifecycle={report['lifecycle_total']}/30")
    for cid, d in correctness["checks"].items():
        print(f"  {cid} {'✓' if d['pass'] else '✗'} {d['note']}")
    print("  -- lifecycle --")
    for k, (s, n) in lifecycle.items():
        print(f"  {k} = {s}/5 ({n})")


if __name__ == "__main__":
    main()
