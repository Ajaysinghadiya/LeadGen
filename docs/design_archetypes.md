# Design Archetypes — LeadGen Site Generator v2

Source: 29 reference HTML files in `data/Sample_Webages/` (analyzed 2026-05-08).
Insight: 90% of samples converge on `Cormorant Garamond + Montserrat + gold-on-cream`.
That convergence IS the AI-slop baseline. Each archetype below picks fonts + palette
that **do not appear** in the sample set — so generated sites stand out, not blend in.

## Routing

`backend/agents/archetype_router.py` maps `lead.category` → archetype slug.
Cache key: `data/site_templates/{archetype}__{variation}.html`
where `variation = hash(business_name) % len(palette_pool)`.

| Category keyword | Archetype |
|---|---|
| sweet, mithai, farsan, halwai, bakery | `playful_mithai` |
| silk, saree, sari, textile, handloom, patola | `luxury_textile` |
| salon, parlour, spa, beauty, hair, nails | `modern_salon_boutique` |
| boutique, fashion, tailor, dress, garments | `modern_salon_boutique` |
| jeweller, jewellery, gold, diamond, bridal jewellery | `luxury_jewellery` |
| artist, painting, pattachitra, thanka, craft, handicraft, sculpture | `artisan_craft` |
| mehndi, henna, wedding planner, event, academy, course | `event_occasion` |
| (fallback) | `modern_salon_boutique` |

## 6 Archetypes

### 1. `luxury_textile` (silk, saree, handloom, patola)
- **Display font:** Italiana (ultra-thin elegant didone)
- **Body font:** Spectral 300
- **Palette pools (3):**
  - Garnet — `#6b1029` accent on `#1a0f12` plum-ink, brass `#b89568`
  - Indigo — `#1c2541` accent on `#0d1117` ink, copper `#c08a5c`
  - Forest — `#1f3a2f` accent on `#11150f` ink, gilt `#a78550`
- **Hero pattern:** Full-bleed plum bg, central serif name, vertical numeral ticker `01—02—03—04—05` running down right edge.
- **Signature move:** Slow cross-dissolve (4s) between numerals, hairline gold rule top + bottom.
- **Why beats samples:** Silk samples all use cream-bg + maroon. We invert: ink-bg + garnet pop. Italiana ≠ Cormorant.

### 2. `modern_salon_boutique` (salon, boutique, tailor, fashion)
- **Display font:** Fraunces (variable optical-size axis, characterful soft serif)
- **Body font:** DM Sans 300
- **Palette pools (3):**
  - Terracotta — `#c47a4f` on ivory `#faf6ef`, ink `#1a1a1a`
  - Sage — `#6b7d5a` on bone `#f5f1e8`, ink `#1f1f1d`
  - Plum — `#7d4f5e` on blush `#f7eee8`, ink `#1a1a1a`
- **Hero pattern:** Split layout — text-left (60%) / image-right (40%). Image cropped on diagonal.
- **Signature move:** Gold hairline underline animates left-to-right on link hover. Diagonal `clip-path` on image edge.
- **Why beats samples:** Salon samples lean tan-gold-on-cream + Cormorant-Montserrat. Fraunces opsz pulls in italic flourish on big headline; DM Sans is cleaner than Montserrat.

### 3. `playful_mithai` (sweets, mithai, farsan, halwai, bakery)
- **Display font:** Yeseva One (warm chunky serif)
- **Body font:** Quicksand 400 (rounded sans)
- **Palette pools (3):**
  - Tangerine — `#e8623e` on cream `#fff3e0`, gold `#d4a548`, ink `#2b1a0f`
  - Pista — `#7fb069` on cream `#fff8e7`, gold `#d4a548`, ink `#1f2b16`
  - Berry — `#c14c69` on blush `#fff1f3`, gold `#d4a548`, ink `#2b1320`
- **Hero pattern:** Warm radial gradient bg + 3 floating SVG paisley orbs (slow drift `transform: translate` keyframes). Center-aligned title.
- **Signature move:** Marquee strip "Made fresh daily · Made by hand · Made in {city}" looping. Hand-drawn SVG paisley orbs.
- **Why beats samples:** Sweets samples use Playfair + pastel + generic floating circles. Yeseva One is curvier/warmer; paisley SVG is on-brand for Indian sweets vs abstract orbs.

### 4. `artisan_craft` (pattachitra, thanka, sculpture, handicraft, painting)
- **Display font:** Cormorant Infant (variant — softer than Cormorant Garamond)
- **Body font:** Crimson Pro
- **Palette pools (3):**
  - Vermillion — `#b8392f` on dark ink `#0e0e0c`, brass `#cf9b3e`, parchment `#f0e8d4`
  - Indigo — `#3d4e7d` on charcoal `#101218`, gold `#c9a548`, parchment `#ede4c8`
  - Saffron — `#d97706` on espresso `#15110b`, ivory `#f5e8c4`, brass `#a87830`
- **Hero pattern:** Dark bg, hand-drawn SVG ornament border (chevron/lotus motif) framing centered title. Kerned all-caps eyebrow `THE WORKSHOP OF —`.
- **Signature move:** SVG ornament corners at hero + section heads. Slow scale-fade-in on each ornament.
- **Why beats samples:** Artist samples use generic decorative borders. Hand-drawn SVG chevron+lotus is region-rooted (matches pattachitra/thanka motifs).

### 5. `event_occasion` (mehndi, henna, wedding, academy, courses, events)
- **Display font:** Tenor Sans (clean transitional)
- **Body font:** Italiana for accent quotes, body uses DM Sans
- **Palette pools (3):**
  - Henna — gold `#c9a161` on black `#0a0a0a`, maroon `#8b1538` accent
  - Saffron — `#e8a042` on espresso `#1a0f08`, cream text `#f5e8d3`
  - Rose — `#c47a8c` on plum `#1a0a14`, gold `#c9a161`
- **Hero pattern:** Full-bleed black bg, large radial gold gradient pulsing slowly behind centered serif name.
- **Signature move:** Henna-pattern SVG underline animates from 0→100% width on scroll-into-view.
- **Why beats samples:** Devi/Udaipur samples lean ken-burns video bg cliche. Static pulsing radial + henna underline reads more refined.

### 6. `luxury_jewellery` (jeweller, gold, diamond, bridal jewellery)
- **Display font:** Marcellus (display-only ornate serif)
- **Body font:** Outfit (geometric sans, modern counterweight to Marcellus)
- **Palette pools (3):**
  - Gold — `#d4af37` on cream `#fff8f0`, ink `#1a0a0a`, rose `#c9988a`
  - Platinum — `#a8a8a8` on white `#fafafa`, ink `#0a0a0a`, blush `#dabbb0`
  - Emerald — `#4a7c59` on cream `#fff8f0`, gold `#d4af37`, ink `#0d1410`
- **Hero pattern:** Center-aligned, large radial sun-burst SVG (16-ray gold rays) behind name. Custom CSS-only cursor dot follower.
- **Signature move:** Sun-burst rays + cursor-dot. Section dividers are tiny gold sun-burst marks.
- **Why beats samples:** Andavar/Inaayat samples lean rose-gold-cream cliche. Sun-burst SVG behind name + ornate Marcellus ≠ samples' Cormorant.

## Per-lead variation

For each archetype:
- `PALETTE_POOL` — 3 entries
- `HEADLINE_POOL` — 5 tagline alts
- `LEDE_POOL` — 5 lede paragraph alts

Selection: `seed = sum(ord(c) for c in business_name) % pool_size`.
Two leads same archetype → different palette/headline → unique pages.

## File layout

```
backend/agents/site_archetypes/
├── __init__.py            # registry: ARCHETYPES dict + render(archetype_slug, lead_dict) -> html
├── _common.py             # shared CSS reset, grain SVG, base shell
├── luxury_textile.py
├── modern_salon_boutique.py
├── playful_mithai.py
├── artisan_craft.py
├── event_occasion.py
└── luxury_jewellery.py
```

`backend/agents/archetype_router.py` — `route(category: str) -> str` (archetype slug).

`backend/agents/template_cache.py` — patched: cache key includes archetype + variation seed.
