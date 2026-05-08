'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const NAV_ITEMS = [
  { href: '/', icon: '⚡', label: 'Dashboard' },
  { href: '/leads', icon: '📋', label: 'All Leads' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const isActive = (href) => {
    if (href === '/') return pathname === '/'
    return pathname.startsWith(href)
  }

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
        LeadGen v1.0<br />
        © 2025
      </div>
    </aside>
  )
}
