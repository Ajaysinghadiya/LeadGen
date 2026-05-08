---
description: Writes frontend/app/jobs/[id]/page.js — the job monitor page with Agent Thoughts panel
---

# panel-builder

Single output: `frontend/app/jobs/[id]/page.js`

## Read first

```
frontend/lib/api.js         — use its fetch patterns and BASE_URL for all API calls
frontend/app/page.js        — reference for existing layout/Tailwind patterns
frontend/components/Sidebar.js — reference for nav structure
```

## Layout

Two-column layout, full viewport height minus sidebar.

**Left column (40%):** Job header + lead cards
- Job header: city, category, status badge (`pending/running/completed/failed`), outreach counter (`outreach_sent` leads reached)
- Lead cards list: scrollable
  - Each card: `business_name`, `phone` (or "No phone"), website score badge (color-coded: red <30, yellow 30-60, green >60), outreach status pill

**Right column (60%):** Agent Thoughts panel
- Header: "Agent Thoughts" + live indicator dot (green pulse when streaming, grey when stopped)
- Body: scrollable log of SSE events
- Each event row contains: relative timestamp, lead name badge (or lead_id), event content

**Event row styles (Tailwind only — no external UI libs):**

| type | background | text style |
|---|---|---|
| `thought` | `bg-yellow-50 dark:bg-yellow-900/20` | italic, `text-gray-700 dark:text-gray-300` |
| `action` | `bg-blue-50 dark:bg-blue-900/20` | `font-mono text-sm`, tool name in `font-bold` |
| `result` | `bg-green-50 dark:bg-green-900/20` | `font-mono text-sm text-green-800 dark:text-green-300` |
| `error` | `bg-red-50 dark:bg-red-900/20` | `text-red-700 dark:text-red-400` |
| `skip` | `bg-gray-50 dark:bg-gray-800` | `italic text-gray-500` |

Truncate `result` content at 150 chars with "..." — long tool results flood the panel.

## SSE connection

Use native browser `EventSource` API — not fetch with streaming:
```javascript
const es = new EventSource(`${BASE_URL}/jobs/${jobId}/stream`)
es.onmessage = (e) => {
    const event = JSON.parse(e.data)
    setThoughts(prev => [...prev, event])
}
es.onerror = () => es.close()
```

Connect on mount, close on unmount (`useEffect` cleanup).

## Auto-scroll behavior

- Auto-scroll thoughts panel to bottom on new event
- Stop auto-scrolling when user's mouse is inside the panel
- Resume auto-scroll when mouse leaves panel

```javascript
const isHovering = useRef(false)
// onMouseEnter panel: isHovering.current = true
// onMouseLeave panel: isHovering.current = false
// after setThoughts: if (!isHovering.current) scrollRef.current?.scrollIntoView()
```

## Relative timestamps

Display as "just now", "3s ago", "1m ago" — recompute every second via `useEffect` interval.

## Data fetching

- `GET /jobs/{id}` → job details (poll every 3s while status is not "completed"/"failed")
- `GET /leads?job_id={id}` → lead cards (fetch once, refresh when job completes)
- SSE `/jobs/{id}/stream` → Agent Thoughts (EventSource)

## Requirements

- Next.js 15 App Router — `'use client'` at top (this page uses hooks + EventSource)
- Tailwind only — no shadcn, no MUI, no Radix
- Handle loading state and empty state for both columns
- Handle job not found (404) gracefully
