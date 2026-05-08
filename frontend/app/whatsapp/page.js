'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import Sidebar from '../../components/Sidebar'
import { getWhatsAppStatus, whatsAppQrUrl, whatsAppLogout } from '../../lib/api'

export default function WhatsAppPage() {
  const [status, setStatus] = useState({ ready: false, hasQr: false, me: null, bridge_down: false })
  const [qrTick, setQrTick] = useState(Date.now())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Poll status every 2s; refresh QR image every 8s while pairing
  useEffect(() => {
    let cancelled = false

    const tick = async () => {
      try {
        const s = await getWhatsAppStatus()
        if (cancelled) return
        setStatus(s)
        setLoading(false)
        setError(null)
      } catch (e) {
        if (cancelled) return
        setError(e.message)
        setLoading(false)
      }
    }

    tick()
    const statusInterval = setInterval(tick, 2000)
    const qrInterval = setInterval(() => setQrTick(Date.now()), 8000)
    return () => {
      cancelled = true
      clearInterval(statusInterval)
      clearInterval(qrInterval)
    }
  }, [])

  const handleLogout = async () => {
    if (!confirm('Disconnect WhatsApp? You will need to scan the QR again.')) return
    try {
      await whatsAppLogout()
      setStatus({ ready: false, hasQr: false, me: null })
    } catch (e) {
      alert('Logout failed: ' + e.message)
    }
  }

  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <div className="flex-center gap-2" style={{ marginBottom: '0.5rem' }}>
            <Link href="/" style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Dashboard</Link>
            <span style={{ color: 'var(--text-muted)' }}>›</span>
            <span style={{ fontSize: '0.875rem' }}>WhatsApp</span>
          </div>
          <h1 className="page-title">📱 WhatsApp Connection</h1>
          <p className="page-subtitle">
            Pair your personal WhatsApp via QR. Once connected, the agent will send outreach
            messages and video previews from your number — no Twilio account needed.
          </p>
        </div>

        {loading ? (
          <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
            <div className="spinner spinner-lg" style={{ margin: '0 auto 1rem' }} />
            <div style={{ color: 'var(--text-muted)' }}>Checking bridge…</div>
          </div>
        ) : status.bridge_down ? (
          <BridgeDown error={status.error || error} />
        ) : status.ready ? (
          <Connected me={status.me} onLogout={handleLogout} />
        ) : status.hasQr ? (
          <QrPanel qrTick={qrTick} />
        ) : (
          <Waiting />
        )}

        <div className="card" style={{ marginTop: '1.5rem', padding: '1rem 1.25rem' }}>
          <div className="card-title" style={{ marginBottom: '0.75rem' }}>How it works</div>
          <ol style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.7 }}>
            <li>Start the Node bridge: <code className="inline-code">cd whatsapp-bridge &amp;&amp; npm start</code></li>
            <li>Open WhatsApp on your phone → Settings → Linked Devices → Link a Device</li>
            <li>Scan the QR shown above</li>
            <li>Create a job from the Dashboard — the agent sends from your WhatsApp</li>
          </ol>
        </div>
      </main>
    </div>
  )
}

// ─── States ──────────────────────────────────────────────────────────────────

function BridgeDown({ error }) {
  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      <div style={{
        padding: '1rem',
        background: 'var(--danger-bg)',
        border: '1px solid rgba(239,68,68,0.3)',
        borderRadius: 'var(--radius)',
        color: 'var(--danger)',
        marginBottom: '1rem',
      }}>
        ⚠ <strong>WhatsApp bridge is not running</strong>
        {error && <div style={{ fontSize: '0.8rem', opacity: 0.85, marginTop: '0.4rem', fontFamily: 'monospace' }}>{error}</div>}
      </div>
      <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.7 }}>
        Start the bridge in a terminal:
        <pre style={{
          background: 'var(--surface)',
          border: '1px solid var(--surface-border)',
          padding: '0.75rem',
          borderRadius: 'var(--radius)',
          marginTop: '0.5rem',
          fontSize: '0.82rem',
        }}>cd whatsapp-bridge{'\n'}npm install   # first time only{'\n'}npm start</pre>
      </div>
    </div>
  )
}

function Waiting() {
  return (
    <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
      <div className="spinner spinner-lg" style={{ margin: '0 auto 1rem' }} />
      <div style={{ color: 'var(--text-muted)' }}>
        Bridge is starting up — QR will appear in a few seconds…
      </div>
    </div>
  )
}

function QrPanel({ qrTick }) {
  return (
    <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
      <div className="card-title" style={{ marginBottom: '1rem' }}>Scan this QR with WhatsApp</div>
      <div style={{
        display: 'inline-block',
        padding: '1rem',
        background: '#fff',
        borderRadius: 'var(--radius)',
        border: '1px solid var(--surface-border)',
      }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`/api/whatsapp/qr?t=${qrTick}`}
          alt="WhatsApp pairing QR"
          width={320}
          height={320}
          style={{ display: 'block' }}
        />
      </div>
      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '1rem' }}>
        QR refreshes every 8 seconds · Status auto-detects when paired
      </div>
    </div>
  )
}

function Connected({ me, onLogout }) {
  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <div style={{
          width: 12, height: 12, borderRadius: '50%',
          background: '#22c55e', boxShadow: '0 0 8px rgba(34,197,94,0.6)',
        }} />
        <div className="card-title">WhatsApp Connected</div>
      </div>
      <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.7 }}>
        <div><strong>Account:</strong> {me?.name || 'Unknown'}</div>
        <div><strong>ID:</strong> <code className="inline-code">{me?.id || '—'}</code></div>
      </div>
      <div style={{ marginTop: '1.25rem' }}>
        <button onClick={onLogout} className="btn btn-danger" style={{ fontSize: '0.85rem' }}>
          Disconnect
        </button>
      </div>
    </div>
  )
}
