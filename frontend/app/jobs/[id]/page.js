'use client'
import { useState, useEffect, useRef } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import Sidebar from '../../../components/Sidebar'
import { getJob, getLeads, watchJob, stopJob } from '../../../lib/api'

// ─── Agent Thoughts panel ────────────────────────────────────────────────────

const TYPE_STYLE = {
  thought: { bg: 'rgba(234,179,8,0.08)',  border: 'rgba(234,179,8,0.25)',  color: '#fde68a', label: '💭', italic: true  },
  action:  { bg: 'rgba(59,130,246,0.10)', border: 'rgba(59,130,246,0.28)', color: '#bfdbfe', label: '⚙️', mono: true   },
  result:  { bg: 'rgba(34,197,94,0.08)',  border: 'rgba(34,197,94,0.25)',  color: '#bbf7d0', label: '✓',  mono: true   },
  error:   { bg: 'rgba(239,68,68,0.10)',  border: 'rgba(239,68,68,0.30)',  color: '#fecaca', label: '⚠',  mono: false  },
  skip:    { bg: 'rgba(148,163,184,0.10)',border: 'rgba(148,163,184,0.25)',color: '#cbd5e1', label: '↷',  italic: true },
  done:    { bg: 'rgba(34,197,94,0.10)',  border: 'rgba(34,197,94,0.30)',  color: '#86efac', label: '🎉', italic: false },
}

function relTime(ts, now) {
  const d = Math.max(0, Math.floor(now - ts))
  if (d < 2)   return 'just now'
  if (d < 60)  return `${d}s ago`
  if (d < 3600) return `${Math.floor(d / 60)}m ago`
  return `${Math.floor(d / 3600)}h ago`
}

function truncate(s, n) {
  if (typeof s !== 'string') return ''
  return s.length > n ? s.slice(0, n) + '…' : s
}

function AgentThoughts({ events, leadsById, jobStatus }) {
  const scrollRef = useRef(null)
  const isHovering = useRef(false)
  const [now, setNow] = useState(Date.now() / 1000)

  // Recompute relative timestamps every second
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now() / 1000), 1000)
    return () => clearInterval(t)
  }, [])

  // Auto-scroll on new event unless user is hovering
  useEffect(() => {
    if (!isHovering.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [events])

  const live = jobStatus === 'running' || jobStatus === 'pending'

  return (
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <div className="card-header">
        <span className="card-title">🧠 Agent Thoughts</span>
        <div className="flex-center gap-1">
          <div className={live ? 'pulse-dot' : ''} style={!live ? {
            width: 8, height: 8, borderRadius: '50%', background: 'var(--text-muted)',
          } : undefined} />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {live ? 'streaming' : 'stopped'}
          </span>
        </div>
      </div>
      <div
        ref={scrollRef}
        onMouseEnter={() => { isHovering.current = true }}
        onMouseLeave={() => { isHovering.current = false }}
        style={{
          maxHeight: 460,
          overflowY: 'auto',
          padding: '0.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
        }}
      >
        {events.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontStyle: 'italic', padding: '1rem' }}>
            Waiting for the agent to think…
          </div>
        ) : (
          events.map((ev, i) => {
            const sty = TYPE_STYLE[ev.type] || TYPE_STYLE.thought
            const lead = ev.lead_id ? leadsById[ev.lead_id] : null
            const leadLabel = lead ? lead.business_name : (ev.lead_id ? `lead ${ev.lead_id}` : 'job')
            const content = ev.type === 'result' ? truncate(ev.content, 150) : ev.content

            return (
              <div
                key={i}
                style={{
                  background: sty.bg,
                  border: `1px solid ${sty.border}`,
                  borderRadius: 'var(--radius)',
                  padding: '0.6rem 0.75rem',
                  fontSize: '0.85rem',
                  color: sty.color,
                  fontFamily: sty.mono ? 'var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace)' : undefined,
                  fontStyle: sty.italic ? 'italic' : 'normal',
                  lineHeight: 1.5,
                }}
              >
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '0.5rem',
                  fontSize: '0.72rem', color: 'var(--text-muted)',
                  marginBottom: '0.25rem', fontStyle: 'normal', fontFamily: 'inherit',
                }}>
                  <span style={{ fontSize: '0.9rem' }}>{sty.label}</span>
                  <span style={{
                    background: 'var(--surface)',
                    border: '1px solid var(--surface-border)',
                    padding: '0.05rem 0.45rem',
                    borderRadius: 999,
                    fontSize: '0.68rem',
                    color: 'var(--text-secondary)',
                  }}>
                    {leadLabel}
                  </span>
                  <span style={{ marginLeft: 'auto' }}>{relTime(ev.timestamp, now)}</span>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {content}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

// ─── Lead card list (left column) ────────────────────────────────────────────

function scoreBadge(score) {
  if (score == null) return null
  let bg = 'rgba(239,68,68,0.15)', color = '#fca5a5'
  if (score >= 60)      { bg = 'rgba(34,197,94,0.15)';  color = '#86efac' }
  else if (score >= 30) { bg = 'rgba(234,179,8,0.15)';  color = '#fde68a' }
  return (
    <span style={{
      background: bg, color, padding: '0.1rem 0.45rem',
      borderRadius: 6, fontSize: '0.7rem', fontWeight: 700,
    }}>
      {Math.round(score)}
    </span>
  )
}

function LeadCards({ leads, loading }) {
  if (loading && !leads.length) {
    return (
      <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)' }}>
        <div className="spinner" style={{ margin: '0 auto 0.5rem' }} /> Loading leads…
      </div>
    )
  }
  if (!leads.length) {
    return (
      <div className="empty-state" style={{ padding: '1.5rem' }}>
        <div className="empty-state-icon">🔍</div>
        <div className="empty-state-title">No leads yet</div>
        <div className="empty-state-desc">Leads appear as the agent discovers them.</div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', padding: '0.75rem' }}>
      {leads.map((lead) => (
        <div
          key={lead.id}
          style={{
            background: 'var(--surface)',
            border: '1px solid var(--surface-border)',
            borderRadius: 'var(--radius)',
            padding: '0.65rem 0.75rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem' }}>
            <div style={{ minWidth: 0 }}>
              <div className="text-primary font-bold" style={{ fontSize: '0.88rem', marginBottom: '0.15rem' }}>
                {lead.business_name}
              </div>
              <div className="text-xs text-muted font-mono">{lead.phone || 'No phone'}</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
              {scoreBadge(lead.website_score)}
              <span className={`badge badge-${lead.status}`} style={{ fontSize: '0.65rem' }}>
                {lead.status}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Main page ───────────────────────────────────────────────────────────────

export default function JobMonitorPage() {
  const { id } = useParams()
  const [job, setJob]               = useState(null)
  const [events, setEvents]         = useState([])
  const [leads, setLeads]           = useState([])
  const [leadsLoading, setLeadsLoading] = useState(true)
  const [loading, setLoading]       = useState(true)
  const [notFound, setNotFound]     = useState(false)
  const jobId = parseInt(id)

  // Poll job until completed/failed
  useEffect(() => {
    let cancelled = false
    let interval = null

    const tick = async () => {
      try {
        const data = await getJob(jobId)
        if (cancelled) return
        setJob(data)
        setLoading(false)
        if (data.status === 'completed' || data.status === 'failed') {
          if (interval) clearInterval(interval)
        }
      } catch (e) {
        if (cancelled) return
        setNotFound(true)
        setLoading(false)
        if (interval) clearInterval(interval)
      }
    }

    tick()
    interval = setInterval(tick, 3000)
    return () => { cancelled = true; if (interval) clearInterval(interval) }
  }, [jobId])

  // Fetch leads (initial + on completion)
  useEffect(() => {
    let cancelled = false
    const fetchLeads = async () => {
      try {
        const data = await getLeads({ jobId, pageSize: 200 })
        if (!cancelled) {
          setLeads(data.items || [])
          setLeadsLoading(false)
        }
      } catch {
        if (!cancelled) setLeadsLoading(false)
      }
    }
    fetchLeads()
    const interval = setInterval(fetchLeads, 4000)
    return () => { cancelled = true; clearInterval(interval) }
  }, [jobId])

  // SSE stream — Agent Thoughts
  useEffect(() => {
    const cleanup = watchJob(
      jobId,
      (event) => setEvents(prev => [...prev, event].slice(-200)),
      (err)   => console.warn('SSE error', err),
    )
    return cleanup
  }, [jobId])

  if (loading) return (
    <div className="layout">
      <Sidebar />
      <main className="main-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="spinner spinner-lg" />
      </main>
    </div>
  )

  if (notFound || !job) return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        <div className="empty-state">
          <div className="empty-state-icon">❓</div>
          <div className="empty-state-title">Job not found</div>
          <Link href="/" className="btn btn-primary mt-2">← Back to Dashboard</Link>
        </div>
      </main>
    </div>
  )

  const leadsById = Object.fromEntries(leads.map(l => [String(l.id), l]))

  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        {/* Header */}
        <div className="page-header">
          <div className="flex-center gap-2" style={{ marginBottom: '0.5rem' }}>
            <Link href="/" style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Dashboard</Link>
            <span style={{ color: 'var(--text-muted)' }}>›</span>
            <span style={{ fontSize: '0.875rem' }}>Job #{job.id}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <h1 className="page-title" style={{ margin: 0 }}>
              {job.category === 'auto_boring_sweep' ? 'Local SMB sweep' : job.category}
              {' '}<span style={{ fontWeight: 300, color: 'var(--text-muted)' }}>in</span> {job.city}
            </h1>
            <span className={`badge badge-${job.status}`}>
              {{ pending: '⏳', running: '🔄', completed: '✅', failed: '❌', stopped: '⏹' }[job.status]}{' '}{job.status}
            </span>
            {(job.status === 'running' || job.status === 'pending') && (
              <button
                type="button"
                onClick={async () => {
                  if (!confirm(`Stop job #${job.id}? Current lead will finish; remaining leads skipped.`)) return
                  try { await stopJob(job.id) } catch (e) { alert(`Stop failed: ${e.message}`) }
                }}
                style={{
                  background: 'rgba(234,179,8,0.15)',
                  border: '1px solid rgba(234,179,8,0.4)',
                  color: '#fde68a',
                  padding: '0.3rem 0.7rem',
                  borderRadius: 6,
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                }}
                title="Graceful stop — current lead finishes, remaining leads skipped"
              >⏹ Stop Job</button>
            )}
          </div>
          <p className="page-subtitle">
            Started {new Date(job.created_at).toLocaleString('en-IN')}
            {' · '}
            <strong style={{ color: 'var(--primary)' }}>{job.outreach_sent || 0}</strong> leads reached
          </p>
        </div>

        {/* Error banner */}
        {job.status === 'failed' && job.error_message && (
          <div style={{
            padding: '1rem',
            background: 'var(--danger-bg)',
            border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: 'var(--radius)',
            color: 'var(--danger)',
            marginBottom: '1.5rem',
            fontSize: '0.875rem',
          }}>
            ❌ {job.error_message}
          </div>
        )}

        {/* Stats */}
        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          <div className="stat-card">
            <div className="stat-card-label">Businesses Found</div>
            <div className="stat-card-value orange">{job.total_found || 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Need Website</div>
            <div className="stat-card-value">{job.qualified_leads || 0}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">Messages Sent</div>
            <div className="stat-card-value orange">{job.outreach_sent || 0}</div>
          </div>
        </div>

        {/* Two-column layout: leads (left) + agent thoughts (right) */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(280px, 2fr) 3fr',
          gap: '1.5rem',
          alignItems: 'start',
        }}>
          {/* Left: lead cards */}
          <div className="card" style={{ position: 'sticky', top: '1rem', maxHeight: 'calc(100vh - 2rem)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div className="card-header">
              <span className="card-title">
                Leads <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({leads.length})</span>
              </span>
              <Link href="/leads" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                View all →
              </Link>
            </div>
            <div style={{ overflowY: 'auto', flex: 1 }}>
              <LeadCards leads={leads} loading={leadsLoading} />
            </div>
          </div>

          {/* Right: agent thoughts */}
          <AgentThoughts events={events} leadsById={leadsById} jobStatus={job.status} />
        </div>
      </main>
    </div>
  )
}
