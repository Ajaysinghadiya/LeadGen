"""Render one demo HTML per archetype to data/generated_sites/demo_{archetype}.html.

Run: python backend/scripts/render_archetype_demos.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.site_archetypes import render_for_lead  # noqa: E402
from agents.archetype_router import route, EXAMPLES  # noqa: E402

DEMOS = [
    ("luxury_textile",        {"business_name": "Padma Silk Sarees",            "category": "silk saree shop",     "city": "Salem",       "address": "Big Bazaar Street",       "phone": "+91-9876543210"}),
    ("modern_salon_boutique", {"business_name": "Curls 360 Family Salon",       "category": "unisex salon",        "city": "Kochi",       "address": "Panampilly Nagar",        "phone": "+91-9876543211"}),
    ("playful_mithai",        {"business_name": "Bassi Sweets",                  "category": "sweet shop",          "city": "Jaipur",      "address": "MI Road",                 "phone": "+91-9876543212"}),
    ("artisan_craft",         {"business_name": "Bhaskar Mahapatra Pattachitra", "category": "pattachitra artist",  "city": "Raghurajpur", "address": "Heritage Crafts Village", "phone": "+91-9876543213"}),
    ("event_occasion",        {"business_name": "Udaipur Mehndi Club",           "category": "mehndi artist",       "city": "Udaipur",     "address": "Lake Palace Road",        "phone": "+91-9876543214"}),
    ("luxury_jewellery",      {"business_name": "Andavar Jewellery",             "category": "jewellery shop",      "city": "Madurai",     "address": "East Masi Street",        "phone": "+91-9876543215"}),
]

out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "generated_sites")
out_dir = os.path.abspath(out_dir)
os.makedirs(out_dir, exist_ok=True)

print("=" * 78)
print("Rendering archetype demos")
print("=" * 78)
for arch, lead in DEMOS:
    html, palette_idx = render_for_lead(arch, lead)
    fname = f"demo_{arch}.html"
    path = os.path.join(out_dir, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    biz = lead["business_name"]
    print(f"  [{arch:25s}] palette={palette_idx} biz={biz!r:42s} -> {fname} ({len(html)} bytes)")

print()
print("=" * 78)
print("Router sanity")
print("=" * 78)
fail = 0
for cat, expected in EXAMPLES.items():
    got = route(cat)
    ok = got == expected
    mark = "PASS" if ok else "FAIL"
    if not ok:
        fail += 1
    print(f"  [{mark}] {cat!r:35s} -> {got!r:30s} (expected {expected!r})")

print()
print(f"Demos written to: {out_dir}")
print(f"Router: {len(EXAMPLES) - fail}/{len(EXAMPLES)} pass" + (" — ALL GOOD" if fail == 0 else f" — {fail} FAIL"))
sys.exit(1 if fail else 0)
