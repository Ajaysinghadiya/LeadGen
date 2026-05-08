'use client'
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Sidebar from '../components/Sidebar'
import { createJob, getJobs, getWhatsAppStatus } from '../lib/api'

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

function JobCard({ job }) {
  return (
    <Link href={`/jobs/${job.id}`} className="job-card">
      <div className="job-card-header">
        <div>
          <div className="job-card-title">
            {job.category} <span style={{ color: 'var(--text-muted)' }}>in</span> {job.city}
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

const LEAD_CAP_OPTIONS = [10, 20, 25, 30, 35, 50]

export default function DashboardPage() {
  const router = useRouter()
  const [city, setCity] = useState('')
  const [category, setCategory] = useState('')
  const [maxLeads, setMaxLeads] = useState(25)
  const [forceRefresh, setForceRefresh] = useState(false)
  const [loading, setLoading] = useState(false)
  const [jobs, setJobs] = useState([])
  const [jobsLoading, setJobsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [waStatus, setWaStatus] = useState({ ready: true, hasQr: false, bridge_down: false })

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

  // Poll WhatsApp bridge so we can show a warning if not paired.
  useEffect(() => {
    let cancelled = false
    const tick = async () => {
      try {
        const s = await getWhatsAppStatus()
        if (!cancelled) setWaStatus(s)
      } catch {
        if (!cancelled) setWaStatus({ ready: false, hasQr: false, bridge_down: true })
      }
    }
    tick()
    const i = setInterval(tick, 5000)
    return () => { cancelled = true; clearInterval(i) }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!city.trim() || !category.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await createJob(city.trim(), category.trim(), {
        maxLeads,
        forceRefresh,
      })
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

        {/* WhatsApp pair warning — soft gate for stage 0 of the pipeline */}
        {!waStatus.ready && (
          <div style={{
            background: waStatus.bridge_down ? 'rgba(148,163,184,0.10)' : 'rgba(234,179,8,0.10)',
            border: `1px solid ${waStatus.bridge_down ? 'rgba(148,163,184,0.30)' : 'rgba(234,179,8,0.35)'}`,
            borderRadius: 'var(--radius)',
            padding: '0.85rem 1rem',
            marginBottom: '1rem',
            color: waStatus.bridge_down ? 'var(--text-secondary)' : '#fde68a',
            fontSize: '0.88rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
          }}>
            <span style={{ fontSize: '1.2rem' }}>{waStatus.bridge_down ? '⚙️' : '⚠️'}</span>
            <div style={{ flex: 1 }}>
              <strong>
                {waStatus.bridge_down
                  ? 'WhatsApp bridge offline'
                  : waStatus.hasQr
                    ? 'WhatsApp not paired yet'
                    : 'WhatsApp not connected'}
              </strong>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                {waStatus.bridge_down
                  ? 'Start the Node sidecar (cd whatsapp-bridge && npm start) before sending real messages. Jobs will fall back to simulation mode.'
                  : 'Pair your phone before starting a job — otherwise outreach will be simulated, not actually sent.'}
              </div>
            </div>
            <Link
              href="/whatsapp"
              className="btn btn-ghost"
              style={{ fontSize: '0.78rem', padding: '0.4rem 0.8rem', whiteSpace: 'nowrap' }}
            >
              {waStatus.hasQr ? 'Scan QR →' : 'Open WhatsApp →'}
            </Link>
          </div>
        )}

        {/* Search form */}
        <div className="search-form">
          <div className="search-form-title">🎯 Start New Prospecting Job</div>
          <div className="search-form-subtitle">
            Enter a city and business category to begin automated lead generation.
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
              <div className="input-group">
                <label className="input-label">Business Category</label>
                <input
                  className="input"
                  type="text"
                  placeholder="e.g. restaurants, gyms, salons"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  required
                />
              </div>
              <div className="input-group" style={{ flex: '0 0 130px' }}>
                <label className="input-label">Max Leads</label>
                <select
                  className="input"
                  value={maxLeads}
                  onChange={(e) => setMaxLeads(parseInt(e.target.value, 10))}
                  title="Cap on leads passed to the agent loop. Lower = less API spend."
                >
                  {LEAD_CAP_OPTIONS.map(n => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
              <button
                type="submit"
                className="btn btn-primary btn-lg"
                disabled={loading || !city.trim() || !category.trim()}
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

          {/* Quick examples */}
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Quick:</span>
            {[
              ['Jaipur', 'restaurants'],
              ['Pune', 'gyms'],
              ['Delhi', 'salons'],
              ['Mumbai', 'cafes'],
            ].map(([c, cat]) => (
              <button
                key={c + cat}
                type="button"
                onClick={() => { setCity(c); setCategory(cat) }}
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
                {cat} in {c}
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
