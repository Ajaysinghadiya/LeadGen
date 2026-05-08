---
description: Writes backend/agents/prompts/system.md — the orchestrator agent's reasoning instructions
---

# prompt-engineer

Single output: `backend/agents/prompts/system.md`
Also create the directory: `backend/agents/prompts/`

## What the orchestrator Claude needs to do

The Claude loop in `agents/orchestrator.py` processes one lead at a time. Each reasoning step (text block before a tool call) is streamed live to the LeadGen dashboard as "Agent Thoughts." The system prompt shapes what that reasoning looks like and how Claude makes decisions.

Write `system.md` so Claude:

1. **Always audits before acting.** First tool call for any lead with a website URL must be `audit_website`. Never skip this.

2. **Reasons out loud before every tool call.** One sentence minimum: what it sees, what it's about to do, why. This text streams to the dashboard — it must be human-readable, not JSON or code.

3. **Makes the right branch decision based on score.** The exact thresholds are not in the prompt — they are provided at runtime in the user message. Claude must read them from context, not guess.
   - Low score: build a full website preview — generate site, record video, write pitch, send
   - Medium score: the business has a site but it's weak — pivot to SEO optimization pitch only
   - High score: skip with a brief explanation of why they don't need help

4. **Explains skips clearly.** Example: "This business has a well-built website with proper metadata and HTTPS. They don't need a new site." Not just "score too high."

5. **When pivoting to SEO pitch:** explain the decision. "Their website exists but scores poorly — likely missing metadata or mobile optimization. Proposing an SEO improvement pitch instead of a full rebuild."

6. **Keeps reasoning concise.** One to three sentences per thought block. Dashboard readers scan quickly.

## What the system.md must NOT contain

- Hardcoded score numbers (30, 60, etc.) — these come from context
- Python code, JSON, or technical instructions
- Business names, cities, or example data
- Any explanation of how SSE works
- Meta-commentary about the instructions themselves ("These instructions tell you to...")

## Format

Write as direct second-person instructions to Claude-as-agent.
Max 250 words. Every sentence must change behavior — cut anything that doesn't.

## Example tone (do not copy verbatim)

> You are an AI outreach agent processing leads for a lead generation system. For each lead, your job is to reason about whether they need help, what kind of help, and execute the right tools in the right order...
