/**
 * LeadGen WhatsApp Web Bridge
 * - GET  /status          → { ready, hasQr, me }
 * - GET  /qr              → PNG image of current pairing QR (404 if ready)
 * - POST /send            → { phone, message, mediaPath? } → sends message
 * - POST /logout          → disconnect + wipe session
 *
 * Uses whatsapp-web.js with LocalAuth (session persisted in .wwebjs_auth/).
 */
const express = require('express')
const cors = require('cors')
const QRCode = require('qrcode')
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js')
const fs = require('fs')
const path = require('path')

const PORT = process.env.PORT || 8001

// ─── State ───────────────────────────────────────────────────────────────────
let lastQr = null            // raw QR string from whatsapp-web.js
let isReady = false
let me = null                // { id, name } once ready

// ─── WhatsApp client ─────────────────────────────────────────────────────────
const client = new Client({
  authStrategy: new LocalAuth({ dataPath: path.join(__dirname, '.wwebjs_auth') }),
  puppeteer: {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  },
})

client.on('qr', (qr) => {
  lastQr = qr
  isReady = false
  console.log('[bridge] QR received — open http://localhost:' + PORT + '/qr to scan')
})

client.on('ready', () => {
  isReady = true
  lastQr = null
  me = { id: client.info?.wid?._serialized, name: client.info?.pushname }
  console.log('[bridge] WhatsApp ready as', me?.name, '(' + me?.id + ')')
})

client.on('authenticated', () => {
  console.log('[bridge] authenticated — session saved')
})

client.on('auth_failure', (m) => {
  console.error('[bridge] auth failure:', m)
  isReady = false
})

client.on('disconnected', (reason) => {
  console.warn('[bridge] disconnected:', reason)
  isReady = false
  me = null
})

client.initialize().catch((e) => console.error('[bridge] init error:', e))

// ─── HTTP server ─────────────────────────────────────────────────────────────
const app = express()
app.use(cors())
app.use(express.json({ limit: '2mb' }))

app.get('/status', (req, res) => {
  res.json({ ready: isReady, hasQr: !!lastQr, me })
})

app.get('/qr', async (req, res) => {
  if (isReady) return res.status(404).json({ error: 'already connected' })
  if (!lastQr) return res.status(425).json({ error: 'qr not ready yet — wait a few seconds' })
  try {
    const buf = await QRCode.toBuffer(lastQr, { width: 320, margin: 1 })
    res.set('Content-Type', 'image/png')
    res.set('Cache-Control', 'no-store')
    res.send(buf)
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

// Normalize phone: strip non-digits, drop leading 0/+, ensure WhatsApp jid format
function toJid(phone) {
  const digits = String(phone || '').replace(/\D/g, '').replace(/^0+/, '')
  if (!digits) throw new Error('invalid phone')
  return digits + '@c.us'
}

app.post('/send', async (req, res) => {
  if (!isReady) return res.status(503).json({ error: 'whatsapp not connected' })
  const { phone, message, mediaPath } = req.body || {}
  if (!phone || !message) {
    return res.status(400).json({ error: 'phone and message required' })
  }
  try {
    const jid = toJid(phone)

    // Verify number is registered on WhatsApp
    const numId = await client.getNumberId(jid.replace('@c.us', ''))
    if (!numId) {
      return res.status(404).json({ error: 'number not registered on WhatsApp', phone })
    }
    const target = numId._serialized

    let sent
    if (mediaPath && fs.existsSync(mediaPath)) {
      const media = MessageMedia.fromFilePath(mediaPath)
      sent = await client.sendMessage(target, media, { caption: message })
    } else {
      sent = await client.sendMessage(target, message)
    }
    res.json({ id: sent.id?._serialized, status: 'sent', to: target })
  } catch (e) {
    console.error('[bridge] send error:', e)
    res.status(500).json({ error: e.message })
  }
})

app.post('/logout', async (req, res) => {
  try {
    await client.logout()
    isReady = false
    me = null
    lastQr = null
    res.json({ status: 'logged_out' })
  } catch (e) {
    res.status(500).json({ error: e.message })
  }
})

app.listen(PORT, () => {
  console.log('[bridge] listening on http://localhost:' + PORT)
})
