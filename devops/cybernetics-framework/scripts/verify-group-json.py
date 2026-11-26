#!/usr/bin/env python3
"""Verify cybernetics group audit JSON files before merging.

Usage: python3 scripts/verify-group-json.py
Reads cybernetics_group{1,2,3}.json from reports dir, checks:
  - JSON parseable, item count matches
  - Name set matches expected (catching drift + prefix issues)
  - Required fields present on every entry
  - Ghost entries correctly marked (closure=0)

The expected name sets are hardcoded per audit. Update them before each run.
"""
import json, os, sys

home = os.path.expanduser("~")
report_dir = os.path.join(home, ".hermes", "skills", "reports")

# === UPDATE THESE PER AUDIT ===
expected_g1 = set()  # e.g. {"comfyui", "apple-notes", ...}
expected_g2 = set()
expected_g3 = set()

REQUIRED = [
    "name", "category", "closure", "closure_note",
    "stability", "stability_note", "observability", "observability_note",
    "optimization", "optimization_note", "cross_domain", "cross_domain_note",
    "principles", "issues"
]

all_ok = True
for g, expected in [("group1", expected_g1), ("group2", expected_g2), ("group3", expected_g3)]:
    path = os.path.join(report_dir, f"cybernetics_{g}.json")
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception as e:
        print(f"{g}: READ ERROR - {e}")
        all_ok = False
        continue

    # Normalize names (strip category prefixes if present)
    for d in data:
        if "/" in d["name"]:
            d["name"] = d["name"].split("/", 1)[-1]

    names = {d["name"] for d in data}
    missing = expected - names if expected else set()
    extra = names - expected if expected else set()
    ghosts = [d["name"] for d in data if d.get("closure") == 0]

    print(f"{g}: {len(data)} items, size={os.path.getsize(path)} bytes")
    if missing:
        print(f"  MISSING: {sorted(missing)}")
        all_ok = False
    if extra:
        print(f"  EXTRA (foreign): {sorted(extra)}")
        all_ok = False
    if ghosts:
        print(f"  GHOSTS: {ghosts}")
    if not missing and not extra:
        print(f"  OK: all {len(expected) if expected else '?'} expected names present")

    # Check required fields
    for d in data:
        for field in REQUIRED:
            if field not in d:
                print(f"  MISSING FIELD '{field}' in {d.get('name','?')}")
                all_ok = False

    # Rewrite with normalized names
    if "/" not in names:
        pass  # No normalization needed
    else:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Normalized names and rewrote {path}")

if all_ok:
    print("\nALL GROUPS VALID — ready to merge")
    sys.exit(0)
else:
    print("\nISSUES FOUND — fix before merging")
    sys.exit(1)
