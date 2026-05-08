"""
MCP server wrapping Google Places / SerpAPI business discovery.
Runs as stdio — start with: python -m mcp_servers.serp_mcp
Exposes one tool: search_businesses(city, category).
"""
from mcp.server.fastmcp import FastMCP

from config import settings
from workers.discovery import fetch_google_places, fetch_serpapi, MOCK_BUSINESSES


mcp = FastMCP("leadgen-serp")


@mcp.tool()
async def search_businesses(city: str, category: str) -> list[dict]:
    """Discover local businesses for the given city and category. Uses Google
    Places when configured, then SerpAPI, then a mock dataset as the final fallback."""
    if settings.is_real("google_places_api_key"):
        return await fetch_google_places(city, category)
    if settings.is_real("serpapi_key"):
        return await fetch_serpapi(city, category)
    return [
        {**b, "city": city, "category": category, "email": None}
        for b in MOCK_BUSINESSES
    ]


if __name__ == "__main__":
    mcp.run()
