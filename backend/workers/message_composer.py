"""
workers/message_composer.py — Module 5: Message Composer
Generates personalized WhatsApp outreach messages using GPT-4
or a high-quality template fallback.
"""
import logging
from sqlalchemy import select

from config import settings
from models import Lead, Outreach
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)

MOCK_MESSAGES = [
    "Namaste {name}! 🙏\n\nMera naam Ajay hai, aur main aapke business ke liye kuch khaas lekar aaya hoon.\n\nMainne notice kiya ki aapke paas abhi ek professional website nahi hai. Aaj ke digital zamane mein, ek acha website aapke {category} business ko triple kar sakta hai.\n\nMainne aapke liye ek FREE website preview banaya hai — 30 seconds ka ek video dekhen aur batayein kaisa laga! 👇\n\nKoi charge nahi. Sirf ek nazar ✅",
    "Hi {name} 👋\n\nI noticed your {category} business in {city} doesn't have a website yet.\n\nIn today's world, 80% of customers search online before visiting. A website can be the difference between them choosing YOU or going elsewhere.\n\nI've created a FREE sample website specifically for your business. Just 30 seconds — take a look and let me know what you think! 🚀\n\nNo catch, no charge. Just a gift from me. 🤝",
    "Jai Ho {name}! 🌟\n\nAapka {category} business {city} mein mujhe bahut acha laga. Lekin ek cheez miss kar raha hai — ek badiya website!\n\nMaine aapke liye ek special website sampler banaya hai. Bilkul FREE. Aapka phone number, address, sab kuch included.\n\nIs video mein dekhen kaisa dikhega: 👇\n\nAgar pasand aaye toh baat karte hain. Deal? 😊",
]


async def compose_with_openai(lead) -> str:
    """Generate personalized message using GPT-4."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    prompt = (
        f"Write a short, friendly, persuasive WhatsApp outreach message (max 200 words) in a mix of English and Hindi "
        f"for a business owner named '{lead.business_name}' who runs a {lead.category} in {lead.city}. "
        f"Tell them I've noticed they don't have a professional website, and I've made a FREE preview website for them. "
        f"Include a call to action to watch the attached video. Be warm, personal, and not salesy. "
        f"Use 1-2 relevant emojis. Keep it conversational."
    )

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=400,
    )
    return response.choices[0].message.content


def compose_mock(lead) -> str:
    """Select a template message for the lead."""
    import random
    template = random.choice(MOCK_MESSAGES)
    return template.format(
        name=lead.business_name,
        category=lead.category,
        city=lead.city,
    )


async def run_message_composition(job_id: int) -> int:
    """
    Step 5: Compose personalized messages for video-recorded leads.
    Returns number of messages composed.
    """
    logger.info(f"[Job {job_id}] Starting message composition")

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Lead).where(
                Lead.job_id == job_id,
                Lead.status == "video_recorded",
            )
        )
        leads = result.scalars().all()
        lead_ids = [l.id for l in leads]

    composed = 0

    for lead_id in lead_ids:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                continue

            try:
                use_openai = (
                    settings.openai_api_key
                    and settings.openai_api_key != "MOCK"
                )
                if use_openai:
                    message_text = await compose_with_openai(lead)
                else:
                    logger.info(f"[Job {job_id}] Using template message for lead {lead_id}")
                    message_text = compose_mock(lead)

                # Create outreach record
                outreach = Outreach(
                    lead_id=lead.id,
                    message_text=message_text,
                    whatsapp_status="pending",
                )
                db.add(outreach)
                composed += 1

            except Exception as e:
                logger.error(f"[Job {job_id}] Message composition failed for lead {lead_id}: {e}")
                lead.error_message = f"Message composition error: {str(e)}"

            await db.commit()

    logger.info(f"[Job {job_id}] Message composition complete — {composed} messages composed")
    return composed
