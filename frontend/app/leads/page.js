'use client'
import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import Sidebar from '../../components/Sidebar'
import { getLeads } from '../../lib/api'

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'discovered', label: 'Discovered' },
  { value: 'audited', label: 'Audited' },
  { value: 'site_generated', label: 'Site Generated' },
  { value: 'video_recorded', label: 'Video Recorded' },
  { value: 'message_sent', label: 'Message Sent' },
  { value: 'failed', label: 'Failed' },
]

function ScoreBar({ score }) {
  if (score == null) return <span style={{ color: 'var(--text-muted)' }}>—</span>
  const color = score > 60 ? 'var(--success)' : score > 30 ? 'var(--warning)' : 'var(--danger)'
  return (
    <div className="score-bar-wrapper">
      <div className="score-bar" style={{ width: 50 }}>
        <div className="score-bar-fill" style={{ width: `${score}%` }} />
      </div>
      <span className="score-val" style={{ color }}>{Math.round(score)}</span>
    </div>
  )
}

export default function LeadsPage() {
  const [leads, setLeads] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)

  // Filters
  const [cityFilter, setCityFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [needsWebsite, setNeedsWebsite] = useState('')

  const PAGE_SIZE = 50

  const loadLeads = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getLeads({
        page,
        pageSize: PAGE_SIZE,
        city: cityFilter || undefined,
        category: categoryFilter || undefined,
        status: statusFilter || undefined,
        needsWebsite: needsWebsite === 'true' ? true : needsWebsite === 'false' ? false : undefined,
      })
      setLeads(data.items || [])
      setTotal(data.total || 0)
    } catch {
      setLeads([])
    } finally {
      setLoading(false)
    }
  }, [page, cityFilter, categoryFilter, statusFilter, needsWebsite])

  useEffect(() => {
    loadLeads()
  }, [loadLeads])

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content" style={{ marginLeft: 'var(--sidebar-width)' }}>
        <div className="page-header">
          <h1 className="page-title">All Leads</h1>
          <p className="page-subtitle">{total} total leads across all jobs</p>
        </div>

        {/* Filters */}
        <div className="filters-row">
          <input
            className="input"
            placeholder="Filter by city…"
            value={cityFilter}
            onChange={e => { setCityFilter(e.target.value); setPage(1) }}
            style={{ width: 180, padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}
          />
          <input
            className="input"
            placeholder="Filter by category…"
            value={categoryFilter}
            onChange={e => { setCategoryFilter(e.target.value); setPage(1) }}
            style={{ width: 190, padding: '0.5rem 0.85rem', fontSize: '0.85rem' }}
          />
          <select
            className="filter-select"
            value={statusFilter}
            onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
          >
            {STATUS_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <select
            className="filter-select"
            value={needsWebsite}
            onChange={e => { setNeedsWebsite(e.target.value); setPage(1) }}
          >
            <option value="">All Websites</option>
            <option value="true">Needs Website</option>
            <option value="false">Has Website</option>
          </select>
          <button
            onClick={() => { setCityFilter(''); setCategoryFilter(''); setStatusFilter(''); setNeedsWebsite(''); setPage(1) }}
            className="btn btn-ghost"
            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
          >
            ✕ Clear
          </button>
          <div style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {total} results
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
            <div className="spinner spinner-lg" style={{ margin: '0 auto 1rem' }} />
            Loading leads…
          </div>
        ) : leads.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <div className="empty-state-title">No leads found</div>
            <div className="empty-state-desc">
              {cityFilter || statusFilter ? 'Try clearing your filters.' : 'Start a job on the dashboard to generate leads.'}
            </div>
            <Link href="/" className="btn btn-primary mt-2" style={{ display: 'inline-flex', marginTop: '1rem' }}>
              ← Go to Dashboard
            </Link>
          </div>
        ) : (
          <>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Business</th>
                    <th>City / Category</th>
                    <th>Phone</th>
                    <th>Website</th>
                    <th>Score</th>
                    <th>Needs Site</th>
                    <th>Status</th>
                    <th>Assets</th>
                    <th>Job</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead) => (
                    <tr key={lead.id}>
                      <td className="font-mono text-xs text-muted">{lead.id}</td>
                      <td>
                        <div className="text-primary font-bold" style={{ whiteSpace: 'nowrap' }}>
                          {lead.business_name}
                        </div>
                        {lead.address && (
                          <div className="text-xs text-muted truncate" style={{ maxWidth: 200 }}>
                            {lead.address}
                          </div>
                        )}
                      </td>
                      <td>
                        <div style={{ fontSize: '0.875rem' }}>{lead.city}</div>
                        <div className="text-xs text-muted">{lead.category}</div>
                      </td>
                      <td className="font-mono text-xs">{lead.phone || '—'}</td>
                      <td className="truncate" style={{ maxWidth: 150 }}>
                        {lead.existing_website ? (
                          <a
                            href={lead.existing_website}
                            target="_blank"
                            rel="noopener"
                            style={{ color: 'var(--info)', fontSize: '0.78rem' }}
                            onClick={e => e.stopPropagation()}
                          >
                            {lead.existing_website.replace(/^https?:\/\//, '').slice(0, 28)}
                          </a>
                        ) : (
                          <span className="text-muted text-xs">—</span>
                        )}
                      </td>
                      <td><ScoreBar score={lead.website_score} /></td>
                      <td>
                        {lead.needs_website ? (
                          <span style={{ color: 'var(--primary)', fontSize: '0.8rem', fontWeight: 700 }}>Yes ✓</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>No</span>
                        )}
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
                              style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
                              onClick={e => e.stopPropagation()}
                            >
                              🌐
                            </a>
                          )}
                          {lead.video_path && (
                            <a
                              href={`/api/leads/${lead.id}/video`}
                              target="_blank"
                              rel="noopener"
                              className="btn btn-ghost"
                              style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
                              onClick={e => e.stopPropagation()}
                            >
                              🎬
                            </a>
                          )}
                          {lead.outreach?.message_text && (
                            <abbr
                              title={lead.outreach.message_text}
                              style={{ cursor: 'help', fontSize: '0.9rem' }}
                            >
                              💬
                            </abbr>
                          )}
                        </div>
                      </td>
                      <td>
                        <Link
                          href={`/jobs/${lead.job_id}`}
                          style={{ color: 'var(--primary)', fontSize: '0.78rem', fontWeight: 600 }}
                        >
                          #{lead.job_id}
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex-center gap-2" style={{ justifyContent: 'center', marginTop: '1.5rem' }}>
                <button
                  className="btn btn-ghost"
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                >
                  ← Prev
                </button>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                  Page {page} of {totalPages}
                </span>
                <button
                  className="btn btn-ghost"
                  disabled={page >= totalPages}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
