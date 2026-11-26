#!/usr/bin/env python3
"""Example: single-group audit JSON builder for cybernetics-framework audits.

This script demonstrates the pattern for writing group audit results:
  1. Define results as a Python list of dicts (avoids JSON encoding issues with Chinese text)
  2. json.dump(data, f, ensure_ascii=False, indent=2) to write the output
  3. Print summary stats

IMPORTANT: After write_file, VERIFY the script has all entries. See pitfall C in SKILL.md
— write_file can silently drop entries from large Python dict lists (~35KB+).
Run: python3 -c "import ast; tree=ast.parse(open('script.py').read()); print(len([n for n in ast.walk(tree) if isinstance(n, ast.Dict)]))"

This file is a complete working example from the 2026-07-08 Group 2 audit (36 skills).
The actual evaluations are preserved as a reference for scoring patterns.
"""
import json

results = [
    # --- TEMPLATE: replace with your own evaluations ---
    # Each entry:
    # {
    #     "name": "skill-name",
    #     "category": "category",
    #     "closure": <1-5>, "closure_note": "...",
    #     "stability": <1-5>, "stability_note": "...",
    #     "observability": <1-5>, "observability_note": "...",
    #     "optimization": <1-5>, "optimization_note": "...",
    #     "cross_domain": <1-5>, "cross_domain_note": "...",
    #     "principles": [<list of applicable principle numbers 1-14>],
    #     "issues": "brief issue summary"
    # },
    # --- END TEMPLATE ---
]

# Write JSON
output_path = "/Users/you/.hermes/skills/reports/cybernetics_groupN.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Written {len(results)} skills to {output_path}")

# Quick stats
total = len(results)
if total > 0:
    closures = [r["closure"] for r in results]
    stabs = [r["stability"] for r in results]
    obss = [r["observability"] for r in results]
    opts = [r["optimization"] for r in results]
    cross = [r["cross_domain"] for r in results]

    print(f"\n=== Group Audit Summary ({total} skills) ===")
    print(f"Closure:       avg={sum(closures)/total:.1f}, max={max(closures)}, min={min(closures)}")
    print(f"Stability:     avg={sum(stabs)/total:.1f}, max={max(stabs)}, min={min(stabs)}")
    print(f"Observability: avg={sum(obss)/total:.1f}, max={max(obss)}, min={min(obss)}")
    print(f"Optimization:  avg={sum(opts)/total:.1f}, max={max(opts)}, min={min(opts)}")
    print(f"Cross-domain:  avg={sum(cross)/total:.1f}, max={max(cross)}, min={min(cross)}")

    # Top and bottom skills
    print("\n=== Top 5 (by total score) ===")
    ranked = sorted(results, key=lambda r: r["closure"]+r["stability"]+r["observability"]+r["optimization"]+r["cross_domain"], reverse=True)
    for r in ranked[:5]:
        ts = r["closure"]+r["stability"]+r["observability"]+r["optimization"]+r["cross_domain"]
        print(f"  {r['name']:40s} total={ts}  C={r['closure']} S={r['stability']} O={r['observability']} P={r['optimization']} X={r['cross_domain']}")

    print("\n=== Bottom 5 (by total score) ===")
    for r in ranked[-5:]:
        ts = r["closure"]+r["stability"]+r["observability"]+r["optimization"]+r["cross_domain"]
        print(f"  {r['name']:40s} total={ts}  C={r['closure']} S={r['stability']} O={r['observability']} P={r['optimization']} X={r['cross_domain']}")
