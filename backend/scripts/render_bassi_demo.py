"""Regenerate the demo_preview.html using the archetype path for Bassi Sweets."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.site_archetypes import render_for_lead  # noqa: E402
from agents.archetype_router import route  # noqa: E402

lead = {
    "business_name": "Bassi Sweets",
    "category":      "sweet shop",
    "city":          "Jaipur",
    "address":       "MI Road",
    "phone":         "+91-9876543210",
}

arch = route(lead["category"])
html, palette_idx = render_for_lead(arch, lead)

out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "generated_sites"))
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "demo_preview.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"archetype:   {arch}")
print(f"palette idx: {palette_idx}")
print(f"biz name:    {lead['business_name']!r}")
print(f"output:      {out_path}")
print(f"bytes:       {len(html)}")
