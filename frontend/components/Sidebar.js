'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { getWhatsAppStatus } from '../lib/api'

const NAV_ITEMS = [
  { href: '/', icon: '⚡', label: 'Dashboard' },
  { href: '/leads', icon: '📋', label: 'All Leads' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [waStatus, setWaStatus] = useState({ ready: false, hasQr: false, bridge_down: false })

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

  const isActive = (href) => {
    if (href === '/') return pathname === '/'
    return pathname.startsWith(href)
  }

  const waColor = waStatus.bridge_down ? '#94a3b8'
                : waStatus.ready ? '#22c55e'
                : waStatus.hasQr ? '#eab308'
                : '#ef4444'
  const waLabel = waStatus.bridge_down ? 'Bridge offline'
                : waStatus.ready ? 'Connected'
                : waStatus.hasQr ? 'Scan QR'
                : 'Disconnected'

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">⚡</div>
        <div className="sidebar-logo-text">Lead<span>Gen</span></div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`sidebar-nav-item ${isActive(item.href) ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </Link>
        ))}

        <Link
          href="/whatsapp"
          className={`sidebar-nav-item ${isActive('/whatsapp') ? 'active' : ''}`}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
        >
          <span style={{ display: 'flex', alignItems: 'center' }}>
            <span className="nav-icon">📱</span>
            WhatsApp
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{
              width: 8, height: 8, borderRadius: '50%',
              background: waColor,
              boxShadow: waStatus.ready ? '0 0 6px rgba(34,197,94,0.6)' : 'none',
            }} />
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{waLabel}</span>
          </span>
        </Link>

        <div className="section-divider" style={{ margin: '0.75rem 0' }} />
        <div style={{ padding: '0.5rem 0.75rem', fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Quick Links
        </div>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="sidebar-nav-item"
        >
          <span className="nav-icon">📖</span>
          API Docs
        </a>
        <a
          href="http://localhost:8000/health"
          target="_blank"
          rel="noopener noreferrer"
          className="sidebar-nav-item"
        >
          <span className="nav-icon">💚</span>
          API Health
        </a>
      </nav>

      <div className="sidebar-footer">
        LeadGen v2.0<br />
        © 2026
      </div>
    </aside>
  )
}
