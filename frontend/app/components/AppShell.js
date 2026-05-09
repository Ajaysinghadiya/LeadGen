'use client'
import { usePathname } from 'next/navigation'
import WhatsAppGate from './WhatsAppGate'

// Routes that bypass the WhatsApp gate.
// `/whatsapp` is the pairing page itself — gating it would deadlock.
const EXEMPT_PATHS = new Set(['/whatsapp'])

export default function AppShell({ children }) {
  const pathname = usePathname()
  if (EXEMPT_PATHS.has(pathname)) return <>{children}</>
  return <WhatsAppGate>{children}</WhatsAppGate>
}
