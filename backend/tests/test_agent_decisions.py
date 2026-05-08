"""
Test agent orchestrator decision logic against three mock leads.
Implements the .claude/skills/test-decisions/SKILL.md procedure.

Mocks Anthropic AsyncAnthropic.messages.create AND agents.tools.dispatch
so no real API calls are made and no DB writes happen for the agent loop.

Asserts:
  Lead A (score=0):  generate_site + record_video + compose(build_site) + send_whatsapp
  Lead B (score=35): compose(seo_pitch) + send_whatsapp                    (no generate_site)
  Lead C (score=85): skip event emitted                                    (no tool calls)
"""
import asyncio
import sys
import os
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents import orchestrator as orch  # noqa: E402


# ─── Three test leads ─────────────────────────────────────────────────────────
lead_a = SimpleNamespace(
    id=1, business_name="Bassi Sweets", category="sweet shop",
    city="Jaipur", address="MI Road", phone="+91-9876543210",
    existing_website=None, website_score=0.0, needs_website=True,
    generated_site_path=None, video_path=None, status="discovered", job_id=1,
)
lead_b = SimpleNamespace(
    id=2, business_name="Sharma Dhaba", category="restaurant",
    city="Ahmedabad", address="CG Road", phone="+91-9876543211",
    existing_website="http://sharmadhabaold.wordpress.com", website_score=35.0,
    needs_website=False, generated_site_path=None, video_path=None,
    status="audited", job_id=1,
)
lead_c = SimpleNamespace(
    id=3, business_name="Taj Hotel", category="hotel",
    city="Mumbai", address="Colaba", phone="+91-2222222222",
    existing_website="https://tajhotels.com", website_score=85.0,
    needs_website=False, generated_site_path=None, video_path=None,
    status="audited", job_id=1,
)


# ─── Per-test event log + mock dispatch ───────────────────────────────────────
def make_mock_dispatch(events_list: list):
    async def mock_dispatch(tool_name, tool_input):
        events_list.append({"call": tool_name, "input": tool_input})
        if tool_name == "generate_site":
            return "/data/generated_sites/test.html"
        if tool_name == "record_video":
            return {"success": True, "video_path": "/data/videos/test.webm"}
        if tool_name == "compose_message":
            return "Namaste! Aapki dukaan ke liye..."
        if tool_name == "send_whatsapp":
            return {"sid": "SM_MOCK_00001", "status": "simulated"}
        if tool_name == "audit_website":
            return {"score": float(tool_input.get("score", 50)), "url": ""}
        return {}
    return mock_dispatch


# ─── Mock Anthropic client — scripts the agent's tool sequence per lead ──────
def make_mock_anthropic_client(script):
    """script: list of (text, tool_name, tool_input) per turn.
    The final turn must have tool_name=None and stop_reason='end_turn'."""

    call_idx = {"i": 0}

    async def mock_create(**kwargs):
        i = call_idx["i"]
        call_idx["i"] += 1
        if i >= len(script):
            return MagicMock(content=[], stop_reason="end_turn")
        text, tool_name, tool_input = script[i]
        blocks = []
        if text:
            blocks.append(SimpleNamespace(type="text", text=text))
        if tool_name:
            blocks.append(SimpleNamespace(
                type="tool_use", id=f"tu_{i}",
                name=tool_name, input=tool_input,
            ))
        stop_reason = "tool_use" if tool_name else "end_turn"
        return SimpleNamespace(content=blocks, stop_reason=stop_reason)

    client = MagicMock()
    client.messages = MagicMock()
    client.messages.create = AsyncMock(side_effect=mock_create)
    return client


async def run_one(lead, script):
    """Run run_agent once with mocks, return (sse_events, dispatch_events)."""
    sse_events = []
    dispatch_events = []

    async def broadcast(job_id, event):
        sse_events.append(event)

    mock_client = make_mock_anthropic_client(script)

    with patch.object(orch, "dispatch", make_mock_dispatch(dispatch_events)), \
         patch.object(orch.anthropic, "AsyncAnthropic", lambda: mock_client), \
         patch.object(orch, "AsyncSessionLocal", lambda: _fake_session()):
        await orch.run_agent(lead, job_id=1, broadcast=broadcast)

    return sse_events, dispatch_events


class _FakeAsyncCtxSession:
    """Stub session used by run_agent's status-update queries.
    run_job-level dedup/TTL/cap are NOT exercised here — those are integration concerns;
    this test isolates the per-lead Claude-loop branching logic."""
    async def __aenter__(self): return self
    async def __aexit__(self, *a): return False
    async def execute(self, *a, **k):
        m = MagicMock()
        m.scalar_one_or_none = MagicMock(return_value=SimpleNamespace(status="x"))
        m.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        return m
    async def commit(self): pass


def _fake_session():
    return _FakeAsyncCtxSession()


# ─── Scripts per lead — what the agent "decides" to do ────────────────────────
SCRIPT_A = [
    ("Bassi Sweets has no website. Building a full site for them.",
     "generate_site", {"lead_id": 1, "business_name": "Bassi Sweets", "category": "sweet shop", "city": "Jaipur"}),
    ("Recording a video tour.",
     "record_video", {"lead_id": 1, "html_path": "/data/generated_sites/test.html", "business_name": "Bassi Sweets"}),
    ("Drafting the pitch.",
     "compose_message", {"lead_id": 1, "business_name": "Bassi Sweets", "category": "sweet shop", "city": "Jaipur", "approach": "build_site"}),
    ("Sending the WhatsApp.",
     "send_whatsapp", {"phone": "+91-9876543210", "message": "..."}),
    ("Done.", None, None),
]

SCRIPT_B = [
    ("Sharma Dhaba has a weak website. Pivoting to SEO pitch.",
     "compose_message", {"lead_id": 2, "business_name": "Sharma Dhaba", "category": "restaurant", "city": "Ahmedabad", "approach": "seo_pitch"}),
    ("Sending the WhatsApp.",
     "send_whatsapp", {"phone": "+91-9876543211", "message": "..."}),
    ("Done.", None, None),
]

SCRIPT_C = [
    ("Taj Hotel already has a strong website. Skipping outreach.", None, None),
]


# ─── Verification ─────────────────────────────────────────────────────────────
async def main():
    print("=" * 70)
    print("TEST: agent decision logic against three mock leads")
    print("=" * 70)

    sse_a, dis_a = await run_one(lead_a, SCRIPT_A)
    sse_b, dis_b = await run_one(lead_b, SCRIPT_B)
    sse_c, dis_c = await run_one(lead_c, SCRIPT_C)

    def names(events): return [e["call"] for e in events]
    def has_call(events, name, **expect):
        for e in events:
            if e["call"] == name and all(e["input"].get(k) == v for k, v in expect.items()):
                return True
        return False

    # Lead C — pre-flight skip (score>60) — agent loop never runs, so dispatch is empty
    skip_emitted_c = any(e["type"] == "skip" for e in sse_c)

    checks = [
        ("Lead A — generate_site called",                 has_call(dis_a, "generate_site")),
        ("Lead A — record_video called",                  has_call(dis_a, "record_video")),
        ("Lead A — compose_message(approach=build_site)", has_call(dis_a, "compose_message", approach="build_site")),
        ("Lead A — send_whatsapp called",                 has_call(dis_a, "send_whatsapp")),
        ("Lead B — generate_site NOT called",             not has_call(dis_b, "generate_site")),
        ("Lead B — record_video NOT called",              not has_call(dis_b, "record_video")),
        ("Lead B — compose_message(approach=seo_pitch)",  has_call(dis_b, "compose_message", approach="seo_pitch")),
        ("Lead B — send_whatsapp called",                 has_call(dis_b, "send_whatsapp")),
        ("Lead C — no tool calls",                        names(dis_c) == []),
        ("Lead C — skip event emitted",                   skip_emitted_c),
    ]

    all_pass = True
    for label, ok in checks:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {label}")
        if not ok:
            all_pass = False

    print()
    print(f"Lead A dispatch: {names(dis_a)}")
    print(f"Lead B dispatch: {names(dis_b)}")
    print(f"Lead C dispatch: {names(dis_c)} | sse types: {[e['type'] for e in sse_c]}")
    print()

    if all_pass:
        print("RESULT: ALL CHECKS PASS")
        sys.exit(0)
    else:
        print("RESULT: FAIL")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
