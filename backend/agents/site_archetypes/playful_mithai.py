"""Playful mithai archetype — sweets, mithai, farsan, halwai, bakery.
Yeseva One display + Quicksand body. Warm cream bg, tangerine/pista/berry accents.
Signature: hand-drawn paisley SVG orbs floating, marquee strip."""

PALETTE_POOL = [
    {"bg": "#fff3e0", "ink": "#2b1a0f", "accent": "#e8623e", "accent2": "#d4a548", "accent3": "#7fb069"},  # tangerine
    {"bg": "#fff8e7", "ink": "#1f2b16", "accent": "#7fb069", "accent2": "#d4a548", "accent3": "#e8623e"},  # pista
    {"bg": "#fff1f3", "ink": "#2b1320", "accent": "#c14c69", "accent2": "#d4a548", "accent3": "#e8623e"},  # berry
]

HEADLINE_POOL = [
    "Made fresh, made by hand, made today.",
    "The sweet shop your dadi sent you to.",
    "Boxes that travel; flavours that stay.",
    "A counter, a cousin, a kilo of memory.",
    "We close when the trays are empty.",
]

LEDE_POOL = [
    "A kitchen that opens before the sun and closes when the trays are empty — same recipe, same hands, same temperature, every single day.",
    "Three generations behind the counter and not a single shortcut taken. The ghee is real, the syrup is slow, and the trays empty by 7.",
    "From the first ladoo at dawn to the last barfi at dusk — every box leaves __BIZ_CITY__ the way it was made: honestly.",
    "We don't sell sweets. We sell the small ritual of arriving with a box, untying the string, and watching the room get quiet.",
    "If your grandmother had opinions about mithai, she would have had opinions about ours. We hope they would have been kind.",
]

# SVG paisley orb — reused 3 times with different position + delay.
TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="description" content="__BIZ_NAME__ — __BIZ_CATEGORY__ in __BIZ_CITY__. Made by hand, made fresh, made today." />
<title>__BIZ_NAME__ · __BIZ_CATEGORY__ · __BIZ_CITY__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Yeseva+One&family=Quicksand:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:__BG__;--ink:__INK__;--accent:__ACCENT__;--gold:__ACCENT2__;--accent3:__ACCENT3__;--muted:#7a6957;--cream:#fff8ec;}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:'Quicksand',sans-serif;font-weight:400;line-height:1.65;overflow-x:hidden}
::selection{background:var(--accent);color:#fff}

/* ═══ Page bg with radial warm gradient ═══ */
body::before{content:'';position:fixed;inset:0;z-index:-2;background:radial-gradient(900px 700px at 70% 20%,color-mix(in srgb,var(--accent) 18%, transparent),transparent 70%),radial-gradient(700px 500px at 10% 80%,color-mix(in srgb,var(--accent3) 15%, transparent),transparent 60%);pointer-events:none}

/* ═══ Floating paisley orbs ═══ */
.paisley{position:fixed;width:160px;height:160px;opacity:.22;pointer-events:none;z-index:-1;animation:float 14s ease-in-out infinite}
.paisley.p1{top:8%;left:6%;animation-delay:0s;color:var(--accent)}
.paisley.p2{top:55%;right:5%;animation-delay:-4s;color:var(--gold);width:110px;height:110px}
.paisley.p3{bottom:10%;left:30%;animation-delay:-8s;color:var(--accent3);width:130px;height:130px}
@keyframes float{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-32px) rotate(8deg)}}

.shell{max-width:1280px;margin:0 auto;padding:2rem 2.4rem;position:relative;z-index:1}

.topbar{display:flex;justify-content:space-between;align-items:center;padding:1.4rem 0;font-family:'Quicksand',sans-serif;font-weight:500;font-size:.85rem}
.topbar .mark{font-family:'Yeseva One',serif;font-size:1.4rem;color:var(--accent)}
.topbar nav{display:flex;gap:1.6rem}
.topbar a{color:var(--ink);text-decoration:none;letter-spacing:.04em;border-bottom:2px solid transparent;padding-bottom:.15rem;transition:border-color .25s}
.topbar a:hover{border-color:var(--accent)}

/* ═══ Hero ═══ */
.hero{padding:5rem 0 3rem;text-align:center;position:relative}
.eyebrow{display:inline-flex;align-items:center;gap:.6rem;font-family:'Quicksand',sans-serif;font-weight:600;font-size:.78rem;letter-spacing:.28em;text-transform:uppercase;color:var(--accent);background:#fff;padding:.5rem 1.1rem;border-radius:50px;border:1px solid color-mix(in srgb,var(--accent) 30%, transparent);margin-bottom:1.8rem;box-shadow:0 4px 14px color-mix(in srgb,var(--accent) 12%, transparent)}
.eyebrow .dot{width:6px;height:6px;background:var(--accent);border-radius:50%;animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.5);opacity:.5}}

.hero h1{font-family:'Yeseva One',serif;font-weight:400;font-size:clamp(3.4rem,9vw,7.4rem);line-height:1;letter-spacing:-.01em;color:var(--ink);max-width:14ch;margin:0 auto;position:relative}
.hero h1 .accent{color:var(--accent)}
.hero .lede{font-family:'Quicksand',sans-serif;font-weight:400;font-size:1.2rem;color:var(--muted);max-width:54ch;margin:2rem auto 0;line-height:1.6}
.hero .ctas{display:flex;justify-content:center;gap:.9rem;margin-top:2.4rem;flex-wrap:wrap}

.btn{font-family:'Quicksand',sans-serif;font-weight:600;font-size:.92rem;letter-spacing:.06em;text-decoration:none;padding:1rem 2rem;border-radius:50px;transition:all .3s;display:inline-block}
.btn.fill{background:var(--accent);color:#fff;box-shadow:0 6px 18px color-mix(in srgb,var(--accent) 35%, transparent)}
.btn.fill:hover{transform:translateY(-3px);box-shadow:0 12px 28px color-mix(in srgb,var(--accent) 45%, transparent)}
.btn.ghost{background:#fff;color:var(--ink);border:2px solid var(--ink)}
.btn.ghost:hover{background:var(--ink);color:#fff}

/* ═══ Marquee strip ═══ */
.marquee{margin:4rem 0;background:var(--ink);color:var(--bg);padding:1.2rem 0;overflow:hidden;border-top:3px solid var(--gold);border-bottom:3px solid var(--gold);position:relative}
.marquee .track{display:inline-flex;gap:3rem;white-space:nowrap;animation:scroll 28s linear infinite;font-family:'Yeseva One',serif;font-size:1.6rem;letter-spacing:.04em;padding-right:3rem}
.marquee .track span{display:inline-flex;align-items:center;gap:1.5rem}
.marquee .star{color:var(--gold);font-size:1.2rem}
@keyframes scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}

/* ═══ Sweet cards ═══ */
.shop{padding:4rem 0}
.shop .head{text-align:center;margin-bottom:3rem}
.shop .head h2{font-family:'Yeseva One',serif;font-size:clamp(2.2rem,5vw,3.6rem);color:var(--ink);line-height:1;margin-bottom:.7rem}
.shop .head h2 em{color:var(--accent);font-style:normal}
.shop .head p{color:var(--muted);font-size:1.05rem;max-width:48ch;margin:0 auto}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:1.5rem}
.card{background:#fff;border-radius:24px;padding:2.4rem 1.8rem;text-align:center;transition:all .35s;border:2px solid transparent}
.card:hover{transform:translateY(-6px);border-color:var(--accent);box-shadow:0 24px 50px color-mix(in srgb,var(--accent) 20%, transparent)}
.card .swatch{width:80px;height:80px;margin:0 auto 1.2rem;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'Yeseva One',serif;font-size:2rem;color:#fff;letter-spacing:-.02em}
.card.c1 .swatch{background:linear-gradient(135deg,var(--accent),var(--gold))}
.card.c2 .swatch{background:linear-gradient(135deg,var(--gold),var(--accent3))}
.card.c3 .swatch{background:linear-gradient(135deg,var(--accent3),var(--accent))}
.card h3{font-family:'Yeseva One',serif;font-size:1.4rem;color:var(--ink);margin-bottom:.5rem}
.card p{color:var(--muted);font-size:.95rem;line-height:1.6}

/* ═══ Visit ═══ */
.visit{margin:4rem 0 3rem;background:#fff;border-radius:32px;padding:4rem 3rem;display:grid;grid-template-columns:1fr 1fr;gap:3rem;align-items:center;border:1px solid color-mix(in srgb,var(--accent) 18%, transparent)}
.visit h2{font-family:'Yeseva One',serif;font-size:clamp(2.2rem,5vw,3.4rem);line-height:1;margin-bottom:1.2rem}
.visit h2 em{color:var(--accent);font-style:normal}
.visit .lines{display:grid;grid-template-columns:1fr 1fr;gap:1.6rem 2.4rem}
.visit b{display:block;font-family:'Quicksand',sans-serif;font-weight:600;font-size:.7rem;letter-spacing:.28em;text-transform:uppercase;color:var(--accent);margin-bottom:.4rem}
.visit a,.visit span{color:var(--ink);text-decoration:none;font-family:'Yeseva One',serif;font-size:1.1rem}
.visit a{border-bottom:2px solid transparent;transition:border-color .25s}
.visit a:hover{border-color:var(--accent)}

footer{text-align:center;padding:2rem 0 3rem;color:var(--muted);font-size:.88rem;font-family:'Quicksand',sans-serif;font-weight:500}
footer .accent{color:var(--accent);font-family:'Yeseva One',serif}

@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
.r{opacity:0;animation:rise .9s cubic-bezier(.2,.7,.2,1) forwards}
.d1{animation-delay:.05s}.d2{animation-delay:.18s}.d3{animation-delay:.32s}.d4{animation-delay:.46s}.d5{animation-delay:.6s}

@media(max-width:820px){
  .cards{grid-template-columns:1fr}
  .visit{grid-template-columns:1fr;padding:2.5rem}
  .visit .lines{grid-template-columns:1fr}
  .topbar nav{display:none}
  .paisley{display:none}
}
</style>
</head>
<body>

<svg class="paisley p1" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" fill="currentColor"><path d="M50 10 C 70 20, 80 35, 75 55 C 70 75, 50 85, 35 75 C 20 65, 22 45, 30 35 C 38 25, 45 20, 50 10 Z M 48 30 C 55 35, 58 45, 52 55 C 46 60, 38 55, 40 45 C 42 38, 45 32, 48 30 Z"/></svg>
<svg class="paisley p2" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" fill="currentColor"><path d="M50 10 C 70 20, 80 35, 75 55 C 70 75, 50 85, 35 75 C 20 65, 22 45, 30 35 C 38 25, 45 20, 50 10 Z M 48 30 C 55 35, 58 45, 52 55 C 46 60, 38 55, 40 45 C 42 38, 45 32, 48 30 Z"/></svg>
<svg class="paisley p3" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" fill="currentColor"><path d="M50 10 C 70 20, 80 35, 75 55 C 70 75, 50 85, 35 75 C 20 65, 22 45, 30 35 C 38 25, 45 20, 50 10 Z M 48 30 C 55 35, 58 45, 52 55 C 46 60, 38 55, 40 45 C 42 38, 45 32, 48 30 Z"/></svg>

<div class="shell">

  <header class="topbar r d1">
    <div class="mark">__BIZ_NAME__</div>
    <nav>
      <a href="#shop">Today's Tray</a>
      <a href="#visit">Visit</a>
      <a href="tel:__BIZ_PHONE__">Order</a>
    </nav>
  </header>

  <section class="hero">
    <div class="eyebrow r d1"><span class="dot"></span>OPEN TODAY · __BIZ_CITY__</div>
    <h1 class="r d2">__BIZ_NAME__ <span class="accent">— __HEADLINE__</span></h1>
    <p class="lede r d3">__LEDE__</p>
    <div class="ctas r d4">
      <a class="btn fill" href="tel:__BIZ_PHONE__">Call to order →</a>
      <a class="btn ghost" href="#visit">Find the shop</a>
    </div>
  </section>

</div>

<div class="marquee r d3">
  <div class="track">
    <span>Made fresh daily <span class="star">✦</span></span>
    <span>Made by hand <span class="star">✦</span></span>
    <span>Made in __BIZ_CITY__ <span class="star">✦</span></span>
    <span>Open since dawn <span class="star">✦</span></span>
    <span>Made fresh daily <span class="star">✦</span></span>
    <span>Made by hand <span class="star">✦</span></span>
    <span>Made in __BIZ_CITY__ <span class="star">✦</span></span>
    <span>Open since dawn <span class="star">✦</span></span>
  </div>
</div>

<div class="shell">

  <section class="shop" id="shop">
    <div class="head">
      <h2>From the <em>tray</em>, daily.</h2>
      <p>What we make changes with the season. What does not change is the way we make it.</p>
    </div>
    <div class="cards">
      <div class="card c1 r d2"><div class="swatch">Mi</div><h3>Mithai</h3><p>Slow-cooked ghee, fresh khoya, hand-rolled. Trays come out at dawn — they rarely last till dusk.</p></div>
      <div class="card c2 r d3"><div class="swatch">Fa</div><h3>Farsan</h3><p>Crisp on the outside, never oily. Salted to taste, spiced by feel, bagged the moment you order.</p></div>
      <div class="card c3 r d4"><div class="swatch">Bo</div><h3>Boxes</h3><p>Festival, gifting, weddings. We pack them the way they should be untied — slowly, in front of company.</p></div>
    </div>
  </section>

  <section class="visit" id="visit">
    <div>
      <h2>Come <em>by the counter.</em></h2>
      <p style="color:var(--muted);font-size:1.02rem;line-height:1.65;margin-top:.6rem">Knock on the glass if the door looks closed — it usually isn't. We answer the phone first, second, and third ring.</p>
    </div>
    <div class="lines">
      <div><b>Telephone</b><a href="tel:__BIZ_PHONE__">__BIZ_PHONE__</a></div>
      <div><b>The Shop</b><a href="https://maps.google.com/?q=__BIZ_ADDRESS__, __BIZ_CITY__" target="_blank" rel="noopener">__BIZ_ADDRESS__</a></div>
      <div><b>Hours</b><span>Daily · 7 till empty</span></div>
      <div><b>Bulk &amp; Boxes</b><span>Call ahead · we deliver</span></div>
    </div>
  </section>

</div>

<footer>
  © 2025 · <span class="accent">__BIZ_NAME__</span> · __BIZ_CITY__ · close when the trays are empty
</footer>

</body>
</html>"""
