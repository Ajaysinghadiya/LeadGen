"""
workers/site_generator.py — Module 3: AI Website Generator
Uses OpenAI GPT-4 to generate a beautiful single-page HTML site
for businesses that need a website.
"""
import logging
import json
from pathlib import Path

from sqlalchemy import select

from config import settings
from models import Lead
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)

MOCK_SITE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="description" content="{name} — a {category} in {city}. Made by hand. Run with intention." />
<title>{name} — {category} · {city}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;0,9..144,700;1,9..144,300;1,9..144,500&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --ink:        #efe7d6;
  --bg:         #15140f;
  --bg-2:       #1c1a14;
  --rule:       #3d362a;
  --gold:       #c8a25b;
  --crimson:    #c8412c;
  --muted:      #a9a08c;
  --serif:      'Fraunces', 'Times New Roman', serif;
  --mono:       'DM Mono', ui-monospace, monospace;
  --sans:       'DM Sans', system-ui, sans-serif;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
  background: var(--bg);
  color: var(--ink);
  font-family: var(--sans);
  font-weight: 300;
  line-height: 1.55;
  overflow-x: hidden;
}}
::selection {{ background: var(--gold); color: var(--bg); }}

/* GRAIN OVERLAY — full-page noise via SVG data URI */
body::before {{
  content: '';
  position: fixed; inset: 0;
  pointer-events: none; z-index: 9999;
  opacity: .16; mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.55'/></svg>");
}}

.shell {{ max-width: 1280px; margin: 0 auto; padding: 2.5rem 2rem; position: relative; }}

/* TOPBAR */
.topbar {{
  display:flex; justify-content:space-between; align-items:baseline;
  padding-bottom:1.5rem; border-bottom:1px solid var(--rule);
  font-family:var(--mono); font-size:.72rem; letter-spacing:.18em;
  text-transform:uppercase; color:var(--muted);
}}
.topbar .mark {{ color: var(--gold); }}
.topbar .right {{ display:flex; gap:1.5rem; }}

/* HERO */
.hero {{
  position:relative;
  padding: 6rem 0 4rem;
  display:grid;
  grid-template-columns:[label] auto [main] 1fr [num] auto;
  gap: 2.5rem;
  align-items:end;
}}
.hero::before {{
  content:''; position:absolute; inset:-10% -20%; z-index:-1;
  background:
    radial-gradient(800px 500px at 80% 30%, rgba(200,162,91,.18), transparent 60%),
    radial-gradient(600px 400px at 10% 70%, rgba(200,65,44,.10), transparent 60%);
  filter: blur(20px);
}}
.vert {{
  writing-mode: vertical-rl; transform: rotate(180deg);
  font-family:var(--mono); font-size:.7rem; letter-spacing:.3em;
  text-transform:uppercase; color:var(--muted);
  align-self:start; padding-top:1rem;
}}
.vert b {{ color: var(--gold); font-weight:500; }}
.headline {{ grid-column: main; }}
.eyebrow {{
  font-family:var(--mono); font-size:.7rem; letter-spacing:.32em;
  text-transform:uppercase; color:var(--gold);
  margin-bottom:1.5rem; display:flex; align-items:center; gap:.7rem;
}}
.eyebrow::before {{ content:''; width:42px; height:1px; background:var(--gold); }}
.headline h1 {{
  font-family:var(--serif);
  font-variation-settings: "opsz" 144;
  font-weight:500;
  font-size: clamp(3.2rem, 9.5vw, 8rem);
  line-height:.92;
  letter-spacing:-.025em;
  color: var(--ink);
}}
.headline h1 em {{ font-style:italic; font-weight:300; color:var(--gold); }}
.lede {{
  font-family:var(--serif);
  font-variation-settings:"opsz" 14;
  font-weight:300; font-style:italic;
  font-size: 1.25rem; color:var(--muted);
  max-width: 46ch; margin-top:2.2rem; line-height:1.55;
}}
.bignum {{
  grid-column: num;
  font-family:var(--serif);
  font-variation-settings:"opsz" 144;
  font-weight:300;
  font-size: clamp(4rem, 8vw, 7rem);
  line-height:1; color:var(--rule);
  letter-spacing:-.04em; align-self:end;
}}

/* CTA ROW */
.cta-row {{ grid-column: main; display:flex; gap:.8rem; flex-wrap:wrap; margin-top:2.5rem; }}
.btn {{
  font-family:var(--mono); font-size:.78rem; letter-spacing:.18em;
  text-transform:uppercase; text-decoration:none;
  padding: 1rem 1.7rem; border-radius:0;
  transition: transform .25s, background .25s, color .25s, box-shadow .25s, border-color .25s;
  border:1px solid var(--gold);
  display:inline-block;
}}
.btn-fill  {{ background: var(--gold); color: var(--bg); }}
.btn-fill:hover  {{ background: var(--crimson); border-color: var(--crimson); color: var(--ink); transform: translate(-2px,-2px); box-shadow: 6px 6px 0 var(--rule); }}
.btn-ghost {{ color: var(--ink); background:transparent; }}
.btn-ghost:hover {{ color: var(--gold); transform: translate(-2px,-2px); }}

/* DIVIDER */
.rule {{
  display:flex; align-items:center; gap:1rem;
  margin: 5rem 0 3rem;
  font-family:var(--mono); font-size:.72rem; letter-spacing:.28em;
  text-transform:uppercase; color:var(--muted);
}}
.rule::before, .rule::after {{ content:''; flex:1; height:1px; background:var(--rule); }}

/* OFFER GRID — asymmetric, no rounded cards */
.offer {{ display:grid; grid-template-columns: 1.1fr 1fr 1fr; gap:0; border-top:1px solid var(--rule); }}
.offer .item {{
  padding: 2.5rem 2rem;
  border-right:1px solid var(--rule);
  border-bottom:1px solid var(--rule);
  position:relative;
  transition: background .3s;
}}
.offer .item:last-child {{ border-right:none; }}
.offer .item:hover {{ background: var(--bg-2); }}
.offer .num {{
  font-family:var(--serif);
  font-variation-settings:"opsz" 144;
  font-weight:300; font-style:italic;
  font-size: 2.6rem; color: var(--gold);
  line-height:1; margin-bottom:1.2rem;
}}
.offer h3 {{
  font-family:var(--serif); font-weight:500;
  font-size: 1.3rem; margin-bottom:.6rem; letter-spacing:-.01em;
}}
.offer p {{ color: var(--muted); font-size:.92rem; line-height:1.65; }}

/* QUOTE */
.quote {{ padding: 6rem 0 5rem; text-align:center; position:relative; }}
.quote::before {{
  content:'\\201C';
  position:absolute; top:1rem; left:50%; transform:translateX(-50%);
  font-family:var(--serif); font-size:8rem; color:var(--rule);
  font-style:italic; line-height:1;
}}
.quote q {{
  font-family:var(--serif);
  font-variation-settings:"opsz" 60;
  font-style:italic; font-weight:300;
  font-size: clamp(1.4rem, 3vw, 2.1rem);
  line-height:1.45; color: var(--ink);
  max-width: 820px; margin: 0 auto; display:block;
  quotes: none; position:relative;
}}
.quote q::before, .quote q::after {{ content:''; }}
.quote .sig {{
  font-family:var(--mono); font-size:.72rem; letter-spacing:.24em;
  text-transform:uppercase; color: var(--gold); margin-top: 2rem;
}}

/* CONTACT */
.contact {{
  display:grid; grid-template-columns:auto 1fr; gap: 3rem;
  padding: 4rem 0;
  border-top:1px solid var(--rule);
  border-bottom:1px solid var(--rule);
  align-items:center;
}}
.contact .label {{
  writing-mode: vertical-rl; transform: rotate(180deg);
  font-family:var(--mono); font-size:.72rem; letter-spacing:.3em;
  text-transform:uppercase; color: var(--gold);
}}
.contact h2 {{
  font-family:var(--serif); font-weight:500;
  font-size: clamp(2rem, 5vw, 3.4rem);
  line-height:1; letter-spacing:-.02em; margin-bottom:1.5rem;
}}
.contact h2 em {{ font-style:italic; color: var(--gold); font-weight:300; }}
.contact .lines {{
  display:grid; grid-template-columns:1fr 1fr;
  gap: 1.8rem 3rem; margin-top: 2rem;
}}
.contact .lines div {{ display:flex; flex-direction:column; gap:.4rem; }}
.contact .lines span {{
  font-family:var(--mono); font-size:.7rem; letter-spacing:.24em;
  text-transform:uppercase; color: var(--muted);
}}
.contact .lines a {{
  color: var(--ink); text-decoration:none;
  border-bottom:1px solid var(--rule); padding-bottom:.25rem;
  transition: color .25s, border-color .25s;
  font-family: var(--sans); font-weight:400; font-size:1.02rem; letter-spacing:.01em;
  width: fit-content;
}}
.contact .lines a:hover {{ color: var(--gold); border-color: var(--gold); }}

/* FOOTER */
footer {{
  display:flex; justify-content:space-between; align-items:center;
  padding: 2rem 0;
  font-family:var(--mono); font-size:.7rem; letter-spacing:.22em;
  text-transform:uppercase; color: var(--muted);
}}
footer .gold {{ color: var(--gold); }}

/* STAGGERED REVEAL ON LOAD */
.r {{ opacity:0; transform: translateY(28px); animation: rise .9s cubic-bezier(.2,.7,.2,1) forwards; }}
@keyframes rise {{ to {{ opacity:1; transform:none; }} }}
.d1 {{ animation-delay:.05s; }} .d2 {{ animation-delay:.18s; }} .d3 {{ animation-delay:.32s; }}
.d4 {{ animation-delay:.46s; }} .d5 {{ animation-delay:.60s; }} .d6 {{ animation-delay:.74s; }}

/* RESPONSIVE */
@media (max-width: 820px) {{
  .hero {{ grid-template-columns: 1fr; padding: 3.5rem 0 2.5rem; gap:1.5rem; }}
  .vert, .bignum {{ display:none; }}
  .offer {{ grid-template-columns: 1fr; }}
  .offer .item {{ border-right:none; }}
  .contact {{ grid-template-columns: 1fr; }}
  .contact .label {{ writing-mode: horizontal-tb; transform: none; }}
  .contact .lines {{ grid-template-columns: 1fr; }}
  .topbar {{ flex-wrap:wrap; gap:.5rem; }}
}}
</style>
</head>
<body>
<div class="shell">

  <header class="topbar r d1">
    <div class="mark">— {name}</div>
    <div class="right"><span>Est. Locally · {city}</span><span>Vol. 01</span></div>
  </header>

  <section class="hero">
    <div class="vert r d2">FILE · <b>{category}</b> · {city}</div>
    <div class="headline">
      <div class="eyebrow r d2">Index № 01 — {category}</div>
      <h1 class="r d3">{name}<br><em>of {city}.</em></h1>
      <p class="lede r d4">A quiet study of craft, hospitality, and the unhurried pleasures of a {category} run with intention — found at {address}, in the heart of {city}.</p>
      <div class="cta-row r d5">
        <a class="btn btn-fill" href="tel:{phone}">Call the Counter →</a>
        <a class="btn btn-ghost" href="#visit">Plan a Visit</a>
      </div>
    </div>
    <div class="bignum r d2">№01</div>
  </section>

  <div class="rule">The Offering</div>

  <section class="offer">
    <div class="item r d4">
      <div class="num">01</div>
      <h3>Made by hand.</h3>
      <p>Every order leaves the counter the way it came in — measured, unhurried, and made by the same pair of hands every time.</p>
    </div>
    <div class="item r d5">
      <div class="num">02</div>
      <h3>Of {city}, for {city}.</h3>
      <p>A neighbourhood institution before it was a business. Regulars know the order before it's spoken; newcomers leave as regulars.</p>
    </div>
    <div class="item r d6">
      <div class="num">03</div>
      <h3>Open most days.</h3>
      <p>We answer the phone. We're at {address}. Knock on the glass if the door looks closed — it usually isn't.</p>
    </div>
  </section>

  <section class="quote">
    <q>You can taste the difference between something built to scale and something built to last. {name} was built to last.</q>
    <div class="sig">— A regular, since the beginning</div>
  </section>

  <section class="contact" id="visit">
    <div class="label">VISIT</div>
    <div>
      <h2>Stop by, <em>any time.</em></h2>
      <div class="lines">
        <div><span>Telephone</span><a href="tel:{phone}">{phone}</a></div>
        <div><span>The Address</span><a href="https://maps.google.com/?q={address}, {city}" target="_blank" rel="noopener">{address}, {city}</a></div>
      </div>
    </div>
  </section>

  <footer>
    <div>© 2025 · {name}</div>
    <div class="gold">{city} · {category}</div>
    <div>End of File</div>
  </footer>

</div>
</body>
</html>"""


OPENAI_SYSTEM_PROMPT = """You are an expert web designer. Generate a complete, beautiful, modern single-page HTML website for a local business.

The website must:
1. Use dark mode with orange accent colors (#f97316)
2. Include: hero section, features/services section, about section, contact section, footer
3. Use Google Fonts (Inter)
4. Include smooth CSS animations
5. Be fully responsive
6. Use only HTML + CSS (no JS frameworks, no external CSS frameworks)
7. Include real business contact info in the design
8. Use emojis sparingly for visual appeal
9. Output ONLY the complete HTML document, nothing else.
"""


async def generate_site_openai(lead) -> str:
    """Generate site using OpenAI GPT-4."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = (
        f"Generate a beautiful website for this business:\n"
        f"Name: {lead.business_name}\n"
        f"Category: {lead.category}\n"
        f"City: {lead.city}\n"
        f"Address: {lead.address or 'Not provided'}\n"
        f"Phone: {lead.phone or 'Not provided'}\n"
    )

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": OPENAI_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def generate_site_mock(lead) -> str:
    """Generate site using the built-in template (no API needed)."""
    return MOCK_SITE_TEMPLATE.format(
        name=lead.business_name,
        category=lead.category,
        city=lead.city,
        address=lead.address or "Local Area",
        phone=lead.phone or "+91-XXXXXXXXXX",
    )


async def run_site_generation(job_id: int) -> int:
    """
    Step 3: Generate AI websites for leads that need them.
    Returns number of sites generated.
    """
    logger.info(f"[Job {job_id}] Starting site generation")

    sites_dir = Path(settings.generated_sites_dir)
    sites_dir.mkdir(parents=True, exist_ok=True)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Lead).where(
                Lead.job_id == job_id,
                Lead.needs_website == True,
                Lead.status == "audited",
            )
        )
        leads = result.scalars().all()
        lead_ids = [l.id for l in leads]

    generated = 0

    for lead_id in lead_ids:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                continue

            try:
                use_openai = settings.is_real("openai_api_key")
                if use_openai:
                    html = await generate_site_openai(lead)
                else:
                    logger.info(f"[Job {job_id}] Using mock site for lead {lead_id}")
                    html = generate_site_mock(lead)

                site_path = sites_dir / f"lead_{lead_id}.html"
                site_path.write_text(html, encoding="utf-8")

                lead.generated_site_path = str(site_path)
                lead.status = "site_generated"
                generated += 1

            except Exception as e:
                logger.error(f"[Job {job_id}] Site generation failed for lead {lead_id}: {e}")
                lead.status = "failed"
                lead.error_message = f"Site generation error: {str(e)}"

            await db.commit()

    logger.info(f"[Job {job_id}] Site generation complete — {generated} sites created")
    return generated
