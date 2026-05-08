import './globals.css'

export const metadata = {
  title: 'LeadGen — Local Business Outreach Automation',
  description: 'Find local businesses without websites, generate AI website previews, record video tours, and send personalized WhatsApp outreach automatically.',
  keywords: 'lead generation, local business, outreach, WhatsApp, AI website',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
