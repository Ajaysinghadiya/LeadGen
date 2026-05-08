/**
 * lib/api.js — Frontend API client
 */

const API_BASE = '/api'

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `API error ${res.status}`)
  }
  return res.json()
}

// ─── Jobs ─────────────────────────────────────────────────────────────────────

export async function createJob(city, category, opts = {}) {
  const { maxLeads = 25, forceRefresh = false } = opts
  return apiFetch('/jobs/', {
    method: 'POST',
    body: JSON.stringify({
      city,
      category,
      max_leads: maxLeads,
      force_refresh: forceRefresh,
    }),
  })
}

export async function getJobs(page = 1, pageSize = 20) {
  return apiFetch(`/jobs/?page=${page}&page_size=${pageSize}`)
}

export async function getJob(jobId) {
  return apiFetch(`/jobs/${jobId}`)
}

// ─── Leads ────────────────────────────────────────────────────────────────────

export async function getLeads({ page = 1, pageSize = 50, city, category, status, needsWebsite, jobId } = {}) {
  const params = new URLSearchParams({ page, page_size: pageSize })
  if (city) params.set('city', city)
  if (category) params.set('category', category)
  if (status) params.set('status', status)
  if (needsWebsite !== undefined) params.set('needs_website', needsWebsite)
  if (jobId) params.set('job_id', jobId)
  return apiFetch(`/leads/?${params}`)
}

export async function getLead(leadId) {
  return apiFetch(`/leads/${leadId}`)
}

// ─── WhatsApp bridge ──────────────────────────────────────────────────────────

export async function getWhatsAppStatus() {
  return apiFetch('/whatsapp/status')
}

export function whatsAppQrUrl() {
  // Cache-buster so the browser refetches as new QRs arrive
  return `${API_BASE}/whatsapp/qr?t=${Date.now()}`
}

export async function whatsAppLogout() {
  return apiFetch('/whatsapp/logout', { method: 'POST' })
}

// ─── SSE ──────────────────────────────────────────────────────────────────────

export function watchJob(jobId, onEvent, onError) {
  const url = `${API_BASE}/jobs/${jobId}/stream`
  const source = new EventSource(url)

  source.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      onEvent(data)
      if (data.type === 'done' || data.type === 'error') {
        source.close()
      }
    } catch {
      /* ignore parse errors */
    }
  }

  source.onerror = (e) => {
    if (onError) onError(e)
    source.close()
  }

  return () => source.close() // Returns cleanup function
}
