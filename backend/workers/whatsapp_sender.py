"""
workers/whatsapp_sender.py — Module 6: WhatsApp Sender
Sends outreach messages via Twilio WhatsApp API.
Falls back to simulation mode when credentials are not configured.
"""
import logging
from datetime import datetime
from sqlalchemy import select

from config import settings
from models import Lead, Outreach, Job
from database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def send_via_twilio(phone: str, message: str, video_url: str | None = None) -> dict:
    """Send a WhatsApp message via Twilio."""
    from twilio.rest import Client
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    body = message
    if video_url:
        body += f"\n\n🎬 Website Preview: {video_url}"

    msg = client.messages.create(
        from_=settings.twilio_whatsapp_from,
        to=f"whatsapp:{phone}",
        body=body,
    )
    return {"sid": msg.sid, "status": msg.status}


async def simulate_send(phone: str, message: str) -> dict:
    """Simulate sending — for development without Twilio credentials."""
    import asyncio
    await asyncio.sleep(0.5)  # Simulate network delay
    fake_sid = f"SM_MOCK_{abs(hash(phone + message[:20])) % 100000:05d}"
    logger.info(f"[SIMULATED] WhatsApp to {phone} — SID: {fake_sid}")
    return {"sid": fake_sid, "status": "sent"}


async def run_whatsapp_sending(job_id: int) -> int:
    """
    Step 6: Send WhatsApp messages for all pending outreach records.
    Returns number of messages sent.
    """
    logger.info(f"[Job {job_id}] Starting WhatsApp sending")

    async with AsyncSessionLocal() as db:
        # Get all pending outreach for leads belonging to this job
        result = await db.execute(
            select(Outreach)
            .join(Lead)
            .where(Lead.job_id == job_id, Outreach.whatsapp_status == "pending")
        )
        outreach_records = result.scalars().all()
        outreach_ids = [o.id for o in outreach_records]

    sent = 0
    use_twilio = (
        settings.is_real("twilio_account_sid")
        and settings.is_real("twilio_auth_token")
    )

    for outreach_id in outreach_ids:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Outreach).where(Outreach.id == outreach_id))
            outreach = result.scalar_one_or_none()
            if not outreach:
                continue

            lead_result = await db.execute(select(Lead).where(Lead.id == outreach.lead_id))
            lead = lead_result.scalar_one_or_none()
            if not lead or not lead.phone:
                outreach.whatsapp_status = "failed"
                outreach.twilio_sid = "NO_PHONE"
                await db.commit()
                continue

            try:
                if use_twilio:
                    result_data = await send_via_twilio(
                        phone=lead.phone,
                        message=outreach.message_text,
                        video_url=outreach.video_url,
                    )
                else:
                    logger.info(f"[Job {job_id}] Simulating WhatsApp for lead {lead.id}")
                    result_data = await simulate_send(lead.phone, outreach.message_text)

                outreach.twilio_sid = result_data["sid"]
                outreach.whatsapp_status = "sent"
                outreach.sent_at = datetime.utcnow()
                lead.status = "message_sent"
                sent += 1

            except Exception as e:
                logger.error(f"[Job {job_id}] WhatsApp send failed for outreach {outreach_id}: {e}")
                outreach.whatsapp_status = "failed"
                lead.error_message = f"WhatsApp send error: {str(e)}"

            await db.commit()

    # Update job outreach_sent count
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one()
        job.outreach_sent = sent
        await db.commit()

    logger.info(f"[Job {job_id}] WhatsApp sending complete — {sent} messages sent")
    return sent
