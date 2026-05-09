'use client'
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Sidebar from '../components/Sidebar'
import { createJob, getJobs } from '../lib/api'

function formatRelativeTime(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function StatusBadge({ status }) {
  const emoji = { pending: '⏳', running: '🔄', completed: '✅', failed: '❌' }
  return (
    <span className={`badge badge-${status}`}>
      {emoji[status] || '•'} {status}
    </span>
  )
}

function jobLabel(category) {
  // Backend stores `auto_boring_sweep` for v2 sweep jobs — render a friendly label.
  if (!category || category === 'auto_boring_sweep') return 'Local SMB sweep'
  return category
}

function JobCard({ job }) {
  return (
    <Link href={`/jobs/${job.id}`} className="job-card">
      <div className="job-card-header">
        <div>
          <div className="job-card-title">
            {jobLabel(job.category)} <span style={{ color: 'var(--text-muted)' }}>in</span> {job.city}
          </div>
          <div className="job-card-meta">
            #{job.id} · {formatRelativeTime(job.created_at)}
            {job.current_step && (
              <> · <span style={{ color: 'var(--primary)' }}>{job.current_step}…</span></>
            )}
          </div>
        </div>
        <StatusBadge status={job.status} />
      </div>

      {job.status === 'running' && (
        <div style={{
          height: '2px',
          background: 'var(--surface-border)',
          borderRadius: 99,
          overflow: 'hidden',
          marginBottom: '0.75rem',
        }}>
          <div style={{
            height: '100%',
            width: '60%',
            background: 'linear-gradient(90deg, var(--primary), var(--primary-light))',
            borderRadius: 99,
            animation: 'shimmer 1.5s ease infinite',
          }} />
        </div>
      )}

      <div className="job-card-stats">
        <div className="job-stat">
          <div className="job-stat-val">{job.total_found || 0}</div>
          <div className="job-stat-lbl">Found</div>
        </div>
        <div className="job-stat">
          <div className="job-stat-val">{job.qualified_leads || 0}</div>
          <div className="job-stat-lbl">Qualified</div>
        </div>
        <div className="job-stat">
          <div className="job-stat-val">{job.outreach_sent || 0}</div>
          <div className="job-stat-lbl">Sent</div>
        </div>
        <div className="job-stat">
          <div className="job-stat-val" style={{ color: 'var(--text-muted)' }}>
            {job.skipped_count || 0}
          </div>
          <div className="job-stat-lbl">Skipped</div>
        </div>
      </div>
      {job.max_leads && (
        <div style={{
          fontSize: '0.68rem',
          color: 'var(--text-muted)',
          marginTop: '0.5rem',
          display: 'flex',
          gap: '0.5rem',
        }}>
          <span>cap: {job.max_leads}</span>
          {job.force_refresh && <span style={{ color: 'var(--primary)' }}>· force-refresh</span>}
        </div>
      )}
    </Link>
  )
}

// Range enforced both in UI (min/max attrs) and on the backend (Pydantic ge/le).
const LEADS_MIN = 5
const LEADS_MAX = 25

export default function DashboardPage() {
  const router = useRouter()
  const [city, setCity] = useState('')
  const [maxLeads, setMaxLeads] = useState(15)
  const [forceRefresh, setForceRefresh] = useState(false)
  const [loading, setLoading] = useState(false)
  const [jobs, setJobs] = useState([])
  const [jobsLoading, setJobsLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadJobs = useCallback(async () => {
    try {
      const data = await getJobs(1, 20)
      setJobs(data.items || [])
    } catch (e) {
      // silently fail — API might not be running
    } finally {
      setJobsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadJobs()
    const interval = setInterval(loadJobs, 5000)
    return () => clearInterval(interval)
  }, [loadJobs])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!city.trim()) return
    const n = Number(maxLeads)
    if (!Number.isFinite(n) || n < LEADS_MIN || n > LEADS_MAX) {
      setError(`Max leads must be between ${LEADS_MIN} and ${LEADS_MAX}.`)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await createJob(city.trim(), { maxLeads: n, forceRefresh })
      router.push(`/jobs/${res.job_id}`)
    } catch (e) {
      setError(e.message)
      setLoading(false)
    }
  }

  // Aggregate stats
  const totalFound = jobs.reduce((s, j) => s + (j.total_found || 0), 0)
  const totalSent = jobs.reduce((s, j) => s + (j.outreach_sent || 0), 0)
  const activeJobs = jobs.filter(j => j.status === 'running').length

  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        {/* Page header */}
        <div className="page-header">
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Find businesses, generate websites, send outreach — all automated.</p>
        </div>

        {/* Stats */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-card-icon">📊</div>
            <div className="stat-card-label">Total Jobs</div>
            <div className="stat-card-value">{jobs.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-icon">🔍</div>
            <div className="stat-card-label">Businesses Found</div>
            <div className="stat-card-value orange">{totalFound}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-icon">📤</div>
            <div className="stat-card-label">Messages Sent</div>
            <div className="stat-card-value">{totalSent}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-icon">🔄</div>
            <div className="stat-card-label">Active Jobs</div>
            <div className="stat-card-value orange">{activeJobs}</div>
          </div>
        </div>

        {/* Search form */}
        <div className="search-form">
          <div className="search-form-title">🎯 Find Under-Served Local Businesses</div>
          <div className="search-form-subtitle">
            Enter a city. We auto-sweep 8 boring SMB categories — sweet shops, dhabas,
            saree shops, jewellers, bakeries, tailors, printing presses, handicrafts —
            and qualify only those that no agency is pitching.
          </div>
          <form onSubmit={handleSubmit}>
            <div className="search-form-row">
              <div className="input-group">
                <label className="input-label">City</label>
                <input
                  className="input"
                  type="text"
                  placeholder="e.g. Jaipur, Pune, Mumbai"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  required
                />
              </div>
              <div className="input-group" style={{ flex: '0 0 140px' }}>
                <label className="input-label">Max Leads ({LEADS_MIN}–{LEADS_MAX})</label>
                <input
                  className="input"
                  type="number"
                  min={LEADS_MIN}
                  max={LEADS_MAX}
                  step={1}
                  value={maxLeads}
                  onChange={(e) => setMaxLeads(e.target.value)}
                  title={`Cap on leads passed to the agent loop. Range ${LEADS_MIN}–${LEADS_MAX}.`}
                  required
                />
              </div>
              <button
                type="submit"
                className="btn btn-primary btn-lg"
                disabled={loading || !city.trim()}
              >
                {loading ? (
                  <><div className="spinner" /> Starting…</>
                ) : (
                  '⚡ Start Job'
                )}
              </button>
            </div>
            <div style={{ marginTop: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <label style={{
                display: 'flex', alignItems: 'center', gap: '0.4rem',
                fontSize: '0.78rem', color: 'var(--text-secondary)', cursor: 'pointer',
              }}>
                <input
                  type="checkbox"
                  checked={forceRefresh}
                  onChange={(e) => setForceRefresh(e.target.checked)}
                />
                Force refresh discovery
              </label>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Bypasses 24h cache. Use only when you need brand-new businesses (costs an API call).
              </span>
            </div>
            {error && (
              <div style={{
                marginTop: '1rem',
                padding: '0.75rem 1rem',
                background: 'var(--danger-bg)',
                border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--danger)',
                fontSize: '0.875rem',
              }}>
                ❌ {error}
              </div>
            )}
          </form>

          {/* Quick city picks */}
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Quick:</span>
            {['Jaipur', 'Pune', 'Delhi', 'Mumbai', 'Ahmedabad', 'Lucknow'].map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setCity(c)}
                style={{
                  background: 'var(--surface)',
                  border: '1px solid var(--surface-border)',
                  borderRadius: 99,
                  padding: '0.25rem 0.75rem',
                  fontSize: '0.75rem',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'var(--transition)',
                }}
                onMouseOver={e => e.target.style.borderColor = 'var(--primary)'}
                onMouseOut={e => e.target.style.borderColor = 'var(--surface-border)'}
              >
                {c}
              </button>
            ))}
          </div>
        </div>

        {/* Recent Jobs */}
        <div style={{ marginTop: '2.5rem' }} className="flex-between">
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Recent Jobs</h2>
          <button
            onClick={loadJobs}
            className="btn btn-ghost"
            style={{ padding: '0.4rem 0.9rem', fontSize: '0.8rem' }}
          >
            ↻ Refresh
          </button>
        </div>

        {jobsLoading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            <div className="spinner spinner-lg" style={{ margin: '0 auto 1rem' }} />
            Loading jobs…
          </div>
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🚀</div>
            <div className="empty-state-title">No jobs yet</div>
            <div className="empty-state-desc">Start your first prospecting job above!</div>
          </div>
        ) : (
          <div className="jobs-grid">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        )}
      </main>

      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(200%); }
        }
      `}</style>
    </div>
  )
}
