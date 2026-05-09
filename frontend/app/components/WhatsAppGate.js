'use client'
import { useState, useEffect } from 'react'
import { getWhatsAppStatus } from '../../lib/api'

const SKIP_KEY = 'leadgen_wa_skip_simulate'

/**
 * Hard gate: blocks app until WhatsApp is paired OR user opts into simulate mode.
 *
 * - Polls /whatsapp/status every 2s
 * - Shows full-screen QR when bridge has a QR
 * - Shows full-screen "bridge offline" panel when bridge is down
 * - "Continue in simulate mode" button writes localStorage flag and lets user through
 * - Once status.ready flips true, gate auto-dismisses
 */
export default function WhatsAppGate({ children }) {
  const [status, setStatus] = useState({ ready: false, hasQr: false, bridge_down: false })
  const [loading, setLoading] = useState(true)
  const [skipped, setSkipped] = useState(false)
  const [qrTick, setQrTick] = useState(Date.now())

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setSkipped(localStorage.getItem(SKIP_KEY) === '1')
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const tick = async () => {
      try {
        const s = await getWhatsAppStatus()
        if (!cancelled) {
          setStatus(s)
          setLoading(false)
        }
      } catch (e) {
        if (!cancelled) {
          setStatus({ ready: false, hasQr: false, bridge_down: true, error: e.message })
          setLoading(false)
        }
      }
    }
    tick()
    const i1 = setInterval(tick, 2000)
    const i2 = setInterval(() => setQrTick(Date.now()), 8000)
    return () => { cancelled = true; clearInterval(i1); clearInterval(i2) }
  }, [])

  const handleSkip = () => {
    localStorage.setItem(SKIP_KEY, '1')
    setSkipped(true)
  }

  if (skipped || status.ready) return <>{children}</>

  return (
    <FullScreen>
      {loading
        ? <Loading />
        : status.bridge_down
          ? <BridgeDown error={status.error} onSkip={handleSkip} />
          : status.hasQr
            ? <QrPanel qrTick={qrTick} onSkip={handleSkip} />
            : <Waiting onSkip={handleSkip} />}
    </FullScreen>
  )
}

// ─── Layout ──────────────────────────────────────────────────────────────────

function FullScreen({ children }) {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg, #0b0d10)',
      padding: '2rem',
    }}>
      <div style={{ maxWidth: 480, width: '100%', textAlign: 'center' }}>
        {children}
      </div>
    </div>
  )
}

function Brand() {
  return (
    <div style={{
      fontSize: '0.78rem',
      letterSpacing: '0.18em',
      textTransform: 'uppercase',
      color: 'var(--text-muted, #94a3b8)',
      marginBottom: '0.75rem',
    }}>
      LeadGen 2.0
    </div>
  )
}

// ─── States ──────────────────────────────────────────────────────────────────

function Loading() {
  return (
    <>
      <Brand />
      <div className="spinner spinner-lg" style={{ margin: '1rem auto' }} />
      <div style={{ color: 'var(--text-muted, #94a3b8)', fontSize: '0.9rem' }}>
        Checking WhatsApp bridge…
      </div>
    </>
  )
}

function Waiting({ onSkip }) {
  return (
    <>
      <Brand />
      <h1 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        Connecting WhatsApp…
      </h1>
      <p style={{ color: 'var(--text-muted, #94a3b8)', fontSize: '0.92rem', marginBottom: '1.5rem' }}>
        Bridge is starting. QR will appear shortly.
      </p>
      <div className="spinner spinner-lg" style={{ margin: '1rem auto 2rem' }} />
      <SkipButton onSkip={onSkip} />
    </>
  )
}

function QrPanel({ qrTick, onSkip }) {
  return (
    <>
      <Brand />
      <h1 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        Pair your WhatsApp
      </h1>
      <p style={{ color: 'var(--text-muted, #94a3b8)', fontSize: '0.92rem', marginBottom: '1.5rem' }}>
        Open WhatsApp → Settings → Linked Devices → Link a Device. Scan to send
        outreach from your number.
      </p>
      <div style={{
        display: 'inline-block',
        padding: '1rem',
        background: '#fff',
        borderRadius: 'var(--radius, 12px)',
        border: '1px solid var(--surface-border, #1f2937)',
        marginBottom: '1.25rem',
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
      <div style={{ color: 'var(--text-muted, #94a3b8)', fontSize: '0.78rem', marginBottom: '1.5rem' }}>
        QR refreshes every 8s · Auto-detects when paired
      </div>
      <SkipButton onSkip={onSkip} />
    </>
  )
}

function BridgeDown({ error, onSkip }) {
  return (
    <>
      <Brand />
      <h1 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '0.5rem' }}>
        WhatsApp bridge offline
      </h1>
      <p style={{ color: 'var(--text-muted, #94a3b8)', fontSize: '0.92rem', marginBottom: '1.25rem' }}>
        Start the Node sidecar in a terminal, then refresh.
      </p>
      <pre style={{
        background: 'var(--surface, #111418)',
        border: '1px solid var(--surface-border, #1f2937)',
        padding: '0.85rem 1rem',
        borderRadius: 'var(--radius, 12px)',
        fontSize: '0.82rem',
        textAlign: 'left',
        marginBottom: '1.5rem',
        color: 'var(--text-secondary, #cbd5e1)',
      }}>{`cd whatsapp-bridge
npm install   # first time only
npm start`}</pre>
      {error && (
        <div style={{
          fontSize: '0.74rem',
          color: 'var(--danger, #ef4444)',
          fontFamily: 'monospace',
          marginBottom: '1.5rem',
          opacity: 0.8,
        }}>
          {error}
        </div>
      )}
      <SkipButton onSkip={onSkip} />
    </>
  )
}

function SkipButton({ onSkip }) {
  return (
    <div style={{ borderTop: '1px solid var(--surface-border, #1f2937)', paddingTop: '1.25rem' }}>
      <button
        onClick={onSkip}
        style={{
          background: 'transparent',
          border: '1px solid var(--surface-border, #1f2937)',
          color: 'var(--text-secondary, #cbd5e1)',
          padding: '0.55rem 1.1rem',
          borderRadius: 'var(--radius-sm, 8px)',
          fontSize: '0.85rem',
          cursor: 'pointer',
          transition: 'all 0.15s',
        }}
        onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--primary, #f97316)' }}
        onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--surface-border, #1f2937)' }}
      >
        Continue in simulate mode →
      </button>
      <div style={{ marginTop: '0.6rem', fontSize: '0.72rem', color: 'var(--text-muted, #94a3b8)' }}>
        Dev/demo only. Messages will NOT be sent — agent runs end-to-end and logs the simulated send.
      </div>
    </div>
  )
}
