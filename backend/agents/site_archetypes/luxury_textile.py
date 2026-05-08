"""Luxury textile archetype — silk, saree, handloom, patola.
Italiana display + Spectral body. Plum-ink bg, garnet/brass accents.
Signature: vertical numeral ticker right edge, cross-dissolve."""

PALETTE_POOL = [
    {"bg": "#1a0f12", "ink": "#f3e6d2", "accent": "#6b1029", "accent2": "#b89568"},  # garnet
    {"bg": "#0d1117", "ink": "#ece4d2", "accent": "#1c2541", "accent2": "#c08a5c"},  # indigo
    {"bg": "#11150f", "ink": "#ede4cb", "accent": "#1f3a2f", "accent2": "#a78550"},  # forest
]

HEADLINE_POOL = [
    "An archive of weave.",
    "Threads, kept honest.",
    "Heirlooms in waiting.",
    "Cloth that remembers.",
    "Worn slowly, kept forever.",
]

LEDE_POOL = [
    "A quiet study in textile, drawn from the looms of the subcontinent — handpicked for those who already know the difference.",
    "Six metres at a time. Tied, dyed, and finished by hand. We keep what is rare; we keep it well.",
    "Every weave we carry was chosen for the hand that made it. The price is the patience.",
    "Cloth is older than language. We trade in the kind that lasts longer than both.",
    "Cataloguing the small, careful work of weavers who do not advertise. We do that for them.",
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="description" content="__BIZ_NAME__ — __BIZ_CATEGORY__ in __BIZ_CITY__. An archive of weave." />
<title>__BIZ_NAME__ · __BIZ_CATEGORY__ · __BIZ_CITY__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Italiana&family=Spectral:ital,wght@0,300;0,500;1,300&display=swap" rel="stylesheet">
<style>
:root{--bg:__BG__;--ink:__INK__;--accent:__ACCENT__;--accent2:__ACCENT2__;--rule:#3a2c2f;--muted:#9b8e7c;}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:'Spectral',serif;font-weight:300;line-height:1.65;overflow-x:hidden}
::selection{background:var(--accent2);color:var(--bg)}

.shell{max-width:1320px;margin:0 auto;padding:2rem 2.5rem;position:relative}
.rule-top,.rule-bot{height:1px;background:var(--accent2);opacity:.5;margin:0 2.5rem}

.topbar{display:flex;justify-content:space-between;align-items:center;padding:1rem 0;font-family:'Spectral',serif;font-style:italic;font-size:.85rem;color:var(--muted);letter-spacing:.05em}
.topbar .mark{color:var(--accent2);font-style:normal;letter-spacing:.3em;text-transform:uppercase;font-size:.72rem}

.hero{display:grid;grid-template-columns:1fr auto;gap:3rem;padding:7rem 0 6rem;position:relative;align-items:center}
.hero::before{content:'';position:absolute;inset:-5% -10%;z-index:-1;background:radial-gradient(900px 600px at 30% 50%,color-mix(in srgb,var(--accent) 40%, transparent),transparent 60%);filter:blur(20px)}

.title{max-width:840px}
.title .eyebrow{font-style:italic;font-size:.9rem;color:var(--accent2);letter-spacing:.18em;margin-bottom:1.8rem}
.title h1{font-family:'Italiana',serif;font-weight:400;font-size:clamp(3.2rem,9vw,7.5rem);line-height:.95;letter-spacing:.005em;color:var(--ink)}
.title h1 .accent{color:var(--accent2);font-style:italic}
.title .lede{font-style:italic;font-size:1.18rem;color:var(--muted);max-width:48ch;margin-top:2rem;line-height:1.55}
.title .who{font-family:'Italiana',serif;font-size:1.1rem;letter-spacing:.22em;text-transform:uppercase;color:var(--accent2);margin-top:2.2rem}

/* Vertical numeral ticker — right edge */
.ticker{display:flex;flex-direction:column;align-items:center;gap:1.4rem;border-left:1px solid var(--rule);padding-left:2rem;height:100%;justify-content:center;font-family:'Italiana',serif}
.ticker .num{font-size:1.7rem;color:var(--rule);transition:color .8s ease}
.ticker .num.on{color:var(--accent2)}
.ticker .lbl{writing-mode:vertical-rl;transform:rotate(180deg);font-family:'Spectral',serif;font-style:italic;font-size:.78rem;color:var(--muted);letter-spacing:.3em;text-transform:uppercase;margin-top:1rem}

/* Cross-dissolve via CSS animation */
@keyframes ticker {
  0%,18% { color:var(--accent2); }
  20%,100% { color:var(--rule); }
}
.ticker .num:nth-child(1){animation:ticker 12s infinite;animation-delay:0s}
.ticker .num:nth-child(2){animation:ticker 12s infinite;animation-delay:2.4s}
.ticker .num:nth-child(3){animation:ticker 12s infinite;animation-delay:4.8s}
.ticker .num:nth-child(4){animation:ticker 12s infinite;animation-delay:7.2s}
.ticker .num:nth-child(5){animation:ticker 12s infinite;animation-delay:9.6s}

/* CTA */
.ctas{display:flex;gap:1rem;margin-top:2.5rem;flex-wrap:wrap}
.btn{font-family:'Spectral',serif;font-style:italic;font-size:1rem;text-decoration:none;padding:.9rem 1.8rem;border:1px solid var(--accent2);color:var(--ink);transition:all .3s}
.btn.fill{background:var(--accent2);color:var(--bg);font-style:normal;letter-spacing:.04em}
.btn:hover{background:var(--accent);color:var(--ink);border-color:var(--accent)}

/* Collections — three roman numeral columns */
.cols{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);margin-top:4rem}
.cols .col{padding:3rem 2rem;border-right:1px solid var(--rule)}
.cols .col:last-child{border-right:none}
.cols .roman{font-family:'Italiana',serif;font-size:2.4rem;color:var(--accent2);margin-bottom:1.5rem}
.cols .col h3{font-family:'Italiana',serif;font-size:1.5rem;font-weight:400;margin-bottom:.6rem;color:var(--ink)}
.cols .col p{font-style:italic;color:var(--muted);font-size:.95rem;line-height:1.6}

/* Quote */
.quote{padding:6rem 2rem;text-align:center}
.quote q{font-family:'Italiana',serif;font-size:clamp(1.6rem,3.2vw,2.4rem);line-height:1.4;color:var(--ink);quotes:none;display:block;max-width:860px;margin:0 auto}
.quote q::before,.quote q::after{content:''}
.quote .sig{font-style:italic;font-size:.95rem;color:var(--accent2);margin-top:2rem;letter-spacing:.06em}

/* Visit */
.visit{display:grid;grid-template-columns:1fr 1fr;gap:4rem;padding:5rem 0;border-top:1px solid var(--rule);align-items:start}
.visit h2{font-family:'Italiana',serif;font-weight:400;font-size:clamp(2.2rem,4vw,3.2rem);line-height:1;color:var(--ink)}
.visit h2 em{color:var(--accent2)}
.visit .lines{display:flex;flex-direction:column;gap:1.2rem;font-style:italic}
.visit .lines b{font-family:'Italiana',serif;font-style:normal;color:var(--accent2);letter-spacing:.18em;text-transform:uppercase;font-size:.78rem;display:block;margin-bottom:.3rem}
.visit a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--rule);padding-bottom:.2rem;font-size:1.05rem}
.visit a:hover{color:var(--accent2);border-color:var(--accent2)}

footer{padding:2.5rem 0;text-align:center;font-style:italic;color:var(--muted);font-size:.82rem;letter-spacing:.04em}
footer .accent{color:var(--accent2);font-style:normal;letter-spacing:.3em;text-transform:uppercase;font-size:.7rem}

@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
.r{opacity:0;animation:rise 1s cubic-bezier(.2,.7,.2,1) forwards}
.d1{animation-delay:.05s}.d2{animation-delay:.2s}.d3{animation-delay:.36s}.d4{animation-delay:.52s}.d5{animation-delay:.68s}

@media(max-width:820px){
  .hero{grid-template-columns:1fr;gap:2rem;padding:4rem 0}
  .ticker{flex-direction:row;border-left:none;border-top:1px solid var(--rule);padding-left:0;padding-top:2rem;gap:2rem;justify-content:flex-start}
  .ticker .lbl{writing-mode:horizontal-tb;transform:none}
  .cols{grid-template-columns:1fr}
  .cols .col{border-right:none;border-bottom:1px solid var(--rule)}
  .visit{grid-template-columns:1fr}
}
</style>
</head>
<body>

<div class="rule-top"></div>

<div class="shell">

  <header class="topbar r d1">
    <div class="mark">— __BIZ_NAME__</div>
    <div>An archive · <em>__BIZ_CITY__</em></div>
  </header>

  <section class="hero">
    <div class="title">
      <div class="eyebrow r d2">№ 01 — __BIZ_CATEGORY__ · __BIZ_CITY__</div>
      <h1 class="r d3">__BIZ_NAME__<br><span class="accent">— __HEADLINE__</span></h1>
      <p class="lede r d4">__LEDE__</p>
      <div class="who r d4">Of __BIZ_CITY__</div>
      <div class="ctas r d5">
        <a class="btn fill" href="tel:__BIZ_PHONE__">Speak with us</a>
        <a class="btn" href="#visit">Visit the room</a>
      </div>
    </div>
    <div class="ticker r d4">
      <div class="num">I</div>
      <div class="num">II</div>
      <div class="num">III</div>
      <div class="num">IV</div>
      <div class="num">V</div>
      <div class="lbl">The Archive</div>
    </div>
  </section>

  <section class="cols">
    <div class="col r d2">
      <div class="roman">I.</div>
      <h3>The Looms</h3>
      <p>Each piece comes from a workshop we know by name. We keep small ledgers of who wove what; the cloth has a provenance.</p>
    </div>
    <div class="col r d3">
      <div class="roman">II.</div>
      <h3>The Hand</h3>
      <p>Hand-tied, hand-finished, hand-pressed. Nothing is rushed. The cloth knows when it has been hurried, and so do you.</p>
    </div>
    <div class="col r d4">
      <div class="roman">III.</div>
      <h3>The Keeping</h3>
      <p>We tell you how to fold it, when to air it, where to store it. A garment that lasts forty years is worth twenty minutes of instruction.</p>
    </div>
  </section>

  <section class="quote">
    <q>You are not buying a saree. You are quietly extending the working life of a loom that may not be there next year.</q>
    <div class="sig">— A regular, Volume One</div>
  </section>

  <section class="visit" id="visit">
    <div>
      <h2>Come, <em>see the cloth.</em></h2>
      <p style="font-style:italic;color:var(--muted);margin-top:1.5rem;max-width:38ch;">By appointment is best, though we keep the door open most afternoons. Tea is poured.</p>
    </div>
    <div class="lines">
      <div><b>Telephone</b><a href="tel:__BIZ_PHONE__">__BIZ_PHONE__</a></div>
      <div><b>The Address</b><a href="https://maps.google.com/?q=__BIZ_ADDRESS__, __BIZ_CITY__" target="_blank" rel="noopener">__BIZ_ADDRESS__, __BIZ_CITY__</a></div>
      <div><b>Hours</b><span style="color:var(--ink)">Most days · 11–8 · or by appointment</span></div>
    </div>
  </section>

</div>

<div class="rule-bot"></div>

<footer>
  © 2025 · __BIZ_NAME__ · <span class="accent">__BIZ_CITY__</span> · End of File
</footer>

</body>
</html>"""
