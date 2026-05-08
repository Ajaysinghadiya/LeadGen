---
description: Writes both MCP server files — whatsapp_mcp.py and serp_mcp.py
---

# mcp-builder

Two outputs:
- `backend/mcp_servers/whatsapp_mcp.py`
- `backend/mcp_servers/serp_mcp.py`

Also create: `backend/mcp_servers/__init__.py` (empty)

## Read first

```
backend/workers/whatsapp_sender.py   — for send_via_twilio + simulate_send
backend/workers/discovery.py         — for fetch_google_places + fetch_serpapi
backend/config.py                    — for Settings and is_real() method
```

## Both files use FastMCP

```python
from mcp.server.fastmcp import FastMCP
```

Both run as stdio transport. Both end with:
```python
if __name__ == "__main__":
    mcp.run()
```

---

## whatsapp_mcp.py

```python
"""
MCP server wrapping Twilio WhatsApp API.
Runs as stdio — start with: python -m backend.mcp_servers.whatsapp_mcp
"""
```

Tool: `send_whatsapp_message`
- Parameters: `phone: str`, `message: str`, `video_url: str | None = None`
- Returns: `dict` with `sid` and `status`
- Logic: `if settings.is_real("twilio_account_sid"): send_via_twilio(...) else: simulate_send(...)`
- Do not reimplement Twilio logic — import and call `send_via_twilio` and `simulate_send`

---

## serp_mcp.py

```python
"""
MCP server wrapping Google Places / SerpAPI business discovery.
Runs as stdio — start with: python -m backend.mcp_servers.serp_mcp
"""
```

Tool: `search_businesses`
- Parameters: `city: str`, `category: str`
- Returns: `list[dict]` — each dict has `business_name, phone, email, address, existing_website`
- Logic:
  ```python
  if settings.is_real("google_places_api_key"):
      return await fetch_google_places(city, category)
  elif settings.is_real("serpapi_key"):
      return await fetch_serpapi(city, category)
  else:
      return await fetch_mock_businesses(city, category)
  ```
- Import `fetch_google_places` and `fetch_serpapi` from `backend.workers.discovery`
- Import `fetch_mock_businesses` from `backend.workers.discovery` (check if it exists — if the function has a different name, use the correct one from the file)

---

## Neither file reimplements API logic

They are thin wrappers. All actual HTTP calls live in the workers.
The MCP layer adds: tool schema, FastMCP decoration, stdio transport, is_real() routing.
