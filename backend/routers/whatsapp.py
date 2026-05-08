"""
routers/whatsapp.py — Proxy endpoints to the Node WhatsApp Web bridge.

Frontend talks to /api/whatsapp/* and we forward to localhost:8001.
Avoids CORS, hides bridge port, and lets us swap the bridge later.
"""
import os
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, JSONResponse

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

BRIDGE_URL = os.environ.get("WHATSAPP_BRIDGE_URL", "http://localhost:8001")


@router.get("/status")
async def status():
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            r = await c.get(f"{BRIDGE_URL}/status")
            return JSONResponse(r.json(), status_code=r.status_code)
    except Exception as e:
        return JSONResponse(
            {"ready": False, "hasQr": False, "me": None, "error": str(e), "bridge_down": True},
            status_code=200,
        )


@router.get("/qr")
async def qr():
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{BRIDGE_URL}/qr")
            if r.status_code == 200:
                return Response(content=r.content, media_type="image/png",
                                headers={"Cache-Control": "no-store"})
            return JSONResponse(r.json(), status_code=r.status_code)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"bridge unavailable: {e}")


@router.post("/logout")
async def logout():
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.post(f"{BRIDGE_URL}/logout")
            return JSONResponse(r.json(), status_code=r.status_code)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"bridge unavailable: {e}")
