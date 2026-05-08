'use client'
import { useState, useEffect, useRef } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import Sidebar from '../../../components/Sidebar'
import { getJob, getLeads, watchJob } from '../../../lib/api'

const PIPELINE_STEPS = [
  { key: 'discovery',  label: 'Discover', icon: '🔍' },
  { key: 'audit',      label: 'Audit',    icon: '🌐' },
  { key: 'generation', label: 'Generate', icon: '✨' },
  { key: 'recording',  label: 'Record',   icon: '🎬' },
  { key: 'messaging',  label: 'Compose',  icon: '💬' },
  { key: 'sending',    label: 'Send',     icon: '📤' },
]

const STEP_ORDER = PIPELINE_STEPS.map(s => s.key)

function getStepState(stepKey, currentStep, jobStatus) {
  if (jobStatus === 'completed') return 'done'
  if (!currentStep) return 'pending'
  const currentIdx = STEP_ORDER.indexOf(currentStep)
  const stepIdx = STEP_ORDER.indexOf(stepKey)
  if (stepIdx < currentIdx) return 'done'
  if (stepIdx === currentIdx) return 'active'
  return 'pending'
}

function PipelineProgress({ job }) {
  return (
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <div className="card-header">
        <span className="card-title">Pipeline Progress</span>
        <span className={`badge badge-${job.status}`}>
          {{ pending: '⏳', running: '🔄', completed: '✅', failed: '❌' }[job.status]}
          {' '}{job.status}
        </span>
      </div>
      <div className="steps-container">
        {PIPELINE_STEPS.map((step) => {
          const state = getStepState(step.key, job.current_step, job.status)
          return (
            <div key={step.key} className="step-item">
              <div className={`step-dot ${state}`}>
                {state === 'done' ? '✓' : step.icon}
              </div>
              <div className={`step-label ${state}`}>{step.label}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function LiveLog({ events }) {
  const logRef = useRef(null)
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [events])

  function getLogClass(type) {
    if (type === 'step_done' || type === 'done') return 'success'
    if (type === 'error') return 'error'
    if (type === 'step') return 'info'
    return ''
  }

  function formatTime(ts) {
    try {
      return new Date(ts).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    } catch { return '' }
  }

  return (
    <div className="card" style={{ marginBottom: '1.5rem' }}>
      <div className="card-header">
        <span className="card-title">Live Activity Log</span>
        <div className="flex-center gap-1">
          <div className="pulse-dot" />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Live</span>
        </div>
      </div>
      <div className="live-log" ref={logRef}>
        {events.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
            Waiting for events…
          </div>
        ) : (
          events.map((ev, i) => (
            <div key={i} className="log-entry">
              <span className="log-time">{formatTime(ev.timestamp)}</span>
              <span className={`log-msg ${getLogClass(ev.type)}`}>{ev.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function LeadsTable({ leads, loading }) {
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
        <div className="spinner" style={{ margin: '0 auto 0.5rem' }} /> Loading leads…
      </div>
    )
  }
  if (!leads.length) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">🔍</div>
        <div className="empty-state-title">No leads yet</div>
        <div className="empty-state-desc">Leads will appear here as they are discovered.</div>
      </div>
    )
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Business</th>
            <th>Phone</th>
            <th>Website</th>
            <th>Score</th>
            <th>Status</th>
            <th>Assets</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id}>
              <td className="font-mono text-xs text-muted">{lead.id}</td>
              <td>
                <div className="text-primary font-bold">{lead.business_name}</div>
                <div className="text-xs text-muted">{lead.address}</div>
              </td>
              <td className="font-mono text-xs">{lead.phone || '—'}</td>
              <td className="truncate" style={{ maxWidth: 160 }}>
                {lead.existing_website ? (
                  <a
                    href={lead.existing_website}
                    target="_blank"
                    rel="noopener"
                    style={{ color: 'var(--info)', fontSize: '0.78rem' }}
                    onClick={e => e.stopPropagation()}
                  >
                    {lead.existing_website.replace(/^https?:\/\//, '').slice(0, 30)}…
                  </a>
                ) : (
                  <span className="badge" style={{ background: 'var(--danger-bg)', color: 'var(--danger)', border: '1px solid rgba(239,68,68,0.3)' }}>
                    No website
                  </span>
                )}
              </td>
              <td>
                {lead.website_score != null ? (
                  <div className="score-bar-wrapper">
                    <div className="score-bar" style={{ width: 60 }}>
                      <div
                        className="score-bar-fill"
                        style={{ width: `${lead.website_score}%` }}
                      />
                    </div>
                    <span className="score-val">{Math.round(lead.website_score)}</span>
                  </div>
                ) : '—'}
              </td>
              <td>
                <span className={`badge badge-${lead.status}`}>{lead.status}</span>
              </td>
              <td>
                <div className="flex gap-1">
                  {lead.generated_site_path && (
                    <a
                      href={`/api/leads/${lead.id}/preview`}
                      target="_blank"
                      rel="noopener"
                      className="btn btn-ghost"
                      style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem' }}
                      onClick={e => e.stopPropagation()}
                    >
                      🌐 Site
                    </a>
                  )}
                  {lead.video_path && (
                    <a
                      href={`/api/leads/${lead.id}/video`}
                      target="_blank"
                      rel="noopener"
                      className="btn btn-ghost"
                      style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem' }}
                      onClick={e => e.stopPropagation()}
                    >
                      🎬 Video
                    </a>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function JobMonitorPage() {
  const { id } = useParams()
  const [job, setJob] = useState(null)
  const [events, setEvents] = useState([])
  const [leads, setLeads] = useState([])
  const [leadsLoading, setLeadsLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const jobId = parseInt(id)

  // Fetch job
  useEffect(() => {
    const fetchJob = async () => {
      try {
        const data = await getJob(jobId)
        setJob(data)
        setLoading(false)
      } catch (e) {
        setLoading(false)
      }
    }
    fetchJob()
    const interval = setInterval(fetchJob, 3000)
    return () => clearInterval(interval)
  }, [jobId])

  // Fetch leads
  useEffect(() => {
    const fetchLeads = async () => {
      setLeadsLoading(true)
      try {
        const data = await getLeads({ jobId, pageSize: 100 })
        setLeads(data.items || [])
      } catch {}
      setLeadsLoading(false)
    }
    fetchLeads()
    const interval = setInterval(fetchLeads, 4000)
    return () => clearInterval(interval)
  }, [jobId])

  // SSE stream
  useEffect(() => {
    const cleanup = watchJob(
      jobId,
      (event) => setEvents(prev => [...prev, event].slice(-50)),
      (err) => console.warn('SSE error', err),
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

  if (!job) return (
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
          <h1 className="page-title">
            {job.category} <span style={{ fontWeight: 300, color: 'var(--text-muted)' }}>in</span> {job.city}
          </h1>
          <p className="page-subtitle">
            Started {new Date(job.created_at).toLocaleString('en-IN')}
          </p>
        </div>

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

        {/* Pipeline */}
        <PipelineProgress job={job} />

        {/* Error */}
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

        {/* Live log */}
        <LiveLog events={events} />

        {/* Leads table */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              Leads <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({leads.length})</span>
            </span>
            <Link href="/leads" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              View all →
            </Link>
          </div>
          <LeadsTable leads={leads} loading={leadsLoading} />
        </div>
      </main>
    </div>
  )
}
