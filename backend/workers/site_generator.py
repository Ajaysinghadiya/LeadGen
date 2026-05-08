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
  <meta name="description" content="Welcome to {name} — {category} in {city}." />
  <title>{name} — {category} in {city}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #f97316;
      --primary-dark: #ea580c;
      --bg: #0f0f0f;
      --surface: #1a1a1a;
      --text: #f5f5f5;
      --muted: #888;
      --border: #2a2a2a;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); }}

    /* HERO */
    .hero {{
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      background: linear-gradient(135deg, #0f0f0f 0%, #1a0a00 50%, #0f0f0f 100%);
      position: relative;
      overflow: hidden;
      padding: 2rem;
    }}
    .hero::before {{
      content: '';
      position: absolute;
      width: 600px; height: 600px;
      background: radial-gradient(circle, rgba(249,115,22,0.15) 0%, transparent 70%);
      top: 50%; left: 50%;
      transform: translate(-50%, -50%);
      animation: pulse 4s ease-in-out infinite;
    }}
    @keyframes pulse {{ 0%,100% {{ opacity:0.5; transform:translate(-50%,-50%) scale(1); }} 50% {{ opacity:1; transform:translate(-50%,-50%) scale(1.1); }} }}
    .badge {{
      display: inline-block;
      background: rgba(249,115,22,0.15);
      border: 1px solid rgba(249,115,22,0.4);
      color: var(--primary);
      padding: 0.4rem 1.2rem;
      border-radius: 50px;
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 1.5rem;
      position: relative;
    }}
    .hero h1 {{
      font-size: clamp(2.5rem, 8vw, 5rem);
      font-weight: 900;
      line-height: 1.05;
      position: relative;
      background: linear-gradient(135deg, #fff 30%, var(--primary));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}
    .hero p {{
      font-size: 1.15rem;
      color: var(--muted);
      max-width: 540px;
      line-height: 1.7;
      margin: 1.5rem auto;
      position: relative;
    }}
    .cta-group {{ display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; position: relative; }}
    .btn-primary {{
      background: var(--primary);
      color: white;
      padding: 0.85rem 2.2rem;
      border-radius: 8px;
      font-weight: 700;
      font-size: 1rem;
      text-decoration: none;
      transition: all 0.25s;
    }}
    .btn-primary:hover {{ background: var(--primary-dark); transform: translateY(-2px); box-shadow: 0 12px 30px rgba(249,115,22,0.35); }}
    .btn-outline {{
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.85rem 2.2rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 1rem;
      text-decoration: none;
      transition: all 0.25s;
    }}
    .btn-outline:hover {{ border-color: var(--primary); color: var(--primary); }}

    /* FEATURES */
    .features {{ padding: 6rem 2rem; background: var(--surface); }}
    .features h2 {{ text-align:center; font-size: 2.2rem; font-weight: 800; margin-bottom: 0.75rem; }}
    .features .subtitle {{ text-align: center; color: var(--muted); margin-bottom: 3.5rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.5rem; max-width: 1100px; margin: 0 auto; }}
    .card {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 2rem;
      transition: all 0.3s;
    }}
    .card:hover {{ border-color: var(--primary); transform: translateY(-4px); box-shadow: 0 20px 40px rgba(0,0,0,0.3); }}
    .card-icon {{ font-size: 2rem; margin-bottom: 1rem; }}
    .card h3 {{ font-size: 1.1rem; font-weight: 700; margin-bottom: 0.5rem; }}
    .card p {{ color: var(--muted); font-size: 0.9rem; line-height: 1.6; }}

    /* CONTACT */
    .contact {{ padding: 6rem 2rem; text-align: center; }}
    .contact h2 {{ font-size: 2.2rem; font-weight: 800; margin-bottom: 0.75rem; }}
    .contact p {{ color: var(--muted); margin-bottom: 2.5rem; }}
    .contact-info {{ display: flex; gap: 2rem; justify-content: center; flex-wrap: wrap; }}
    .info-item {{ display: flex; align-items: center; gap: 0.6rem; color: var(--text); font-size: 1rem; }}
    .info-item span {{ color: var(--primary); font-size: 1.3rem; }}

    /* FOOTER */
    footer {{ background: var(--surface); border-top: 1px solid var(--border); padding: 2rem; text-align: center; color: var(--muted); font-size: 0.85rem; }}
  </style>
</head>
<body>

  <section class="hero">
    <div class="badge">✦ {category} · {city}</div>
    <h1>{name}</h1>
    <p>Experience the finest {category} in {city}. Quality, authenticity, and warmth — all in one place.</p>
    <div class="cta-group">
      <a class="btn-primary" href="tel:{phone}">📞 Call Us Now</a>
      <a class="btn-outline" href="#contact">Get Directions</a>
    </div>
  </section>

  <section class="features">
    <h2>Why Choose Us?</h2>
    <p class="subtitle">We bring you the best experience in {city}</p>
    <div class="grid">
      <div class="card"><div class="card-icon">⭐</div><h3>Top Quality</h3><p>We take pride in delivering excellence with every interaction. No compromise on quality.</p></div>
      <div class="card"><div class="card-icon">🤝</div><h3>Trusted Service</h3><p>Serving the community of {city} with dedication and a personal touch since day one.</p></div>
      <div class="card"><div class="card-icon">📍</div><h3>Conveniently Located</h3><p>Easy to find and easy to reach — right in the heart of {city}.</p></div>
      <div class="card"><div class="card-icon">💬</div><h3>Always Available</h3><p>Reach out anytime. We're here to help and answer all your questions.</p></div>
    </div>
  </section>

  <section class="contact" id="contact">
    <h2>Get In Touch</h2>
    <p>Ready to visit or have a question? We'd love to hear from you.</p>
    <div class="contact-info">
      <div class="info-item"><span>📞</span> {phone}</div>
      <div class="info-item"><span>📍</span> {address}, {city}</div>
    </div>
  </section>

  <footer>
    <p>© 2025 {name}. All rights reserved. · {city}</p>
  </footer>

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
