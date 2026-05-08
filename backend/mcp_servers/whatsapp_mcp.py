"""
MCP server wrapping Twilio WhatsApp API.
Runs as stdio — start with: python -m mcp_servers.whatsapp_mcp
Exposes one tool: send_whatsapp_message(phone, message, video_url?).
"""
from mcp.server.fastmcp import FastMCP

from config import settings
from workers.whatsapp_sender import send_via_twilio, simulate_send


mcp = FastMCP("leadgen-whatsapp")


@mcp.tool()
async def send_whatsapp_message(
    phone: str,
    message: str,
    video_url: str | None = None,
) -> dict:
    """Send a WhatsApp message via Twilio. Falls back to a simulated send
    when Twilio credentials are not configured."""
    if settings.is_real("twilio_account_sid") and settings.is_real("twilio_auth_token"):
        return await send_via_twilio(phone=phone, message=message, video_url=video_url)
    return await simulate_send(phone=phone, message=message)


if __name__ == "__main__":
    mcp.run()
