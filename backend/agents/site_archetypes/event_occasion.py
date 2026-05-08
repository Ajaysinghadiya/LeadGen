"""Event/occasion archetype — mehndi, henna, wedding, academy, courses.
Tenor Sans display + Italiana accent + DM Sans body.
Black/espresso/plum bg, gold/saffron/rose accents.
Signature: radial gold pulse behind name, henna-pattern SVG underline animating in."""

PALETTE_POOL = [
    {"bg": "#0a0a0a", "ink": "#f5e8d3", "accent": "#c9a161", "accent2": "#8b1538"},  # henna
    {"bg": "#1a0f08", "ink": "#f5e8d3", "accent": "#e8a042", "accent2": "#c9a161"},  # saffron
    {"bg": "#1a0a14", "ink": "#f5e8d3", "accent": "#c9a161", "accent2": "#c47a8c"},  # rose
]

HEADLINE_POOL = [
    "Designed for the day you'll remember.",
    "The hands behind the wedding photos.",
    "Where the small details get the long hours.",
    "Booked early, finished beautifully.",
    "Every occasion, given its time.",
]

LEDE_POOL = [
    "We work the slow, careful side of celebration. The piece you'll point at in photographs ten years from now — yes, that one — is the kind of work we make.",
    "Bookings open six weeks out. Sittings are unhurried, conversations are real, and the result is something you'll wear, frame, or remember.",
    "Designed in __BIZ_CITY__, finished by hand, photographed under good light. The day belongs to you; the small things belong to us.",
    "Trusted with weddings, festivals, and quieter occasions in equal measure. We pour tea, we listen, we sketch.",
    "A small studio, full diary, deep patience. If your day matters, it matters to us.",
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="description" content="__BIZ_NAME__ — __BIZ_CATEGORY__ in __BIZ_CITY__. Designed for the day you'll remember." />
<title>__BIZ_NAME__ · __BIZ_CATEGORY__ · __BIZ_CITY__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Tenor+Sans&family=Italiana&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:__BG__;--ink:__INK__;--accent:__ACCENT__;--accent2:__ACCENT2__;--muted:#7a6d57;--rule:#2a2118;}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif;font-weight:300;line-height:1.65;overflow-x:hidden}
::selection{background:var(--accent);color:var(--bg)}

.shell{max-width:1280px;margin:0 auto;padding:2rem 2.5rem;position:relative}

.topbar{display:flex;justify-content:space-between;align-items:center;padding:1.5rem 0;border-bottom:1px solid var(--rule);font-size:.72rem;letter-spacing:.4em;text-transform:uppercase;color:var(--muted)}
.topbar .mark{font-family:'Italiana',serif;font-size:1.5rem;color:var(--accent);letter-spacing:.04em;text-transform:none}

/* ═══ Hero ═══ */
.hero{position:relative;padding:9rem 0 7rem;text-align:center;overflow:hidden}
.hero .pulse{position:absolute;top:50%;left:50%;width:880px;height:880px;transform:translate(-50%,-50%);z-index:0;background:radial-gradient(circle at center,color-mix(in srgb,var(--accent) 25%, transparent) 0%,transparent 55%);animation:pulse 6s ease-in-out infinite;pointer-events:none}
@keyframes pulse{0%,100%{opacity:.7;transform:translate(-50%,-50%) scale(1)}50%{opacity:1;transform:translate(-50%,-50%) scale(1.1)}}

.hero .content{position:relative;z-index:1}
.hero .eyebrow{font-family:'DM Sans',sans-serif;font-weight:400;font-size:.72rem;letter-spacing:.5em;text-transform:uppercase;color:var(--accent);margin-bottom:2.4rem;display:inline-flex;align-items:center;gap:1rem}
.hero .eyebrow::before,.hero .eyebrow::after{content:'';width:36px;height:1px;background:var(--accent)}
.hero h1{font-family:'Tenor Sans',serif;font-weight:400;font-size:clamp(3rem,8.5vw,7rem);line-height:1;letter-spacing:.005em;color:var(--ink)}
.hero h1 em{font-family:'Italiana',serif;font-style:italic;color:var(--accent)}
.hero .tagline{font-family:'Italiana',serif;font-style:italic;font-size:1.5rem;color:var(--accent2);margin-top:1.6rem;letter-spacing:.04em}
.hero .lede{font-size:1.12rem;color:var(--muted);max-width:54ch;margin:2.4rem auto 0;line-height:1.7}

/* Henna underline */
.hennaline{display:block;margin:2rem auto 0;width:280px;height:24px;color:var(--accent)}
.hennaline path{stroke-dasharray:600;stroke-dashoffset:600;animation:draw 2.4s ease-out .8s forwards}
@keyframes draw{to{stroke-dashoffset:0}}

.ctas{display:flex;justify-content:center;gap:1rem;margin-top:2.6rem;flex-wrap:wrap;position:relative;z-index:1}
.btn{font-family:'DM Sans',sans-serif;font-weight:500;font-size:.78rem;letter-spacing:.32em;text-transform:uppercase;text-decoration:none;padding:1.05rem 2rem;border:1px solid var(--accent);color:var(--ink);transition:all .35s;display:inline-block;background:transparent}
.btn.fill{background:var(--accent);color:var(--bg)}
.btn:hover{background:var(--accent2);border-color:var(--accent2);color:var(--ink);transform:translateY(-2px)}

/* ═══ Services ═══ */
.services{padding:6rem 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.services .head{text-align:center;margin-bottom:4rem}
.services .head .label{font-size:.72rem;letter-spacing:.5em;text-transform:uppercase;color:var(--accent);margin-bottom:.8rem}
.services .head h2{font-family:'Italiana',serif;font-style:italic;font-size:clamp(2.2rem,5vw,3.6rem);line-height:1;color:var(--ink)}

.svc-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;margin-top:3rem}
.svc{padding:0 2.4rem;border-right:1px solid var(--rule);text-align:center}
.svc:last-child{border-right:none}
.svc .lbl{font-family:'Italiana',serif;font-style:italic;font-size:1.4rem;color:var(--accent);margin-bottom:1rem}
.svc h3{font-family:'Tenor Sans',serif;font-size:1.3rem;letter-spacing:.04em;margin-bottom:.6rem;color:var(--ink)}
.svc p{color:var(--muted);font-size:.95rem;line-height:1.65}
.svc .price{display:inline-block;margin-top:1.2rem;font-size:.7rem;letter-spacing:.32em;text-transform:uppercase;color:var(--accent2);padding:.4rem .9rem;border:1px solid var(--accent2)}

/* ═══ Quote ═══ */
.quote{padding:6rem 2rem;text-align:center}
.quote q{font-family:'Italiana',serif;font-style:italic;font-size:clamp(1.5rem,3vw,2.2rem);line-height:1.5;color:var(--ink);max-width:780px;margin:0 auto;display:block;quotes:none}
.quote q::before,.quote q::after{content:''}
.quote .sig{font-family:'DM Sans',sans-serif;font-size:.72rem;letter-spacing:.4em;text-transform:uppercase;color:var(--accent);margin-top:2rem;font-weight:500}

/* ═══ Booking ═══ */
.book{padding:5rem 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);display:grid;grid-template-columns:1fr 1.3fr;gap:4rem;align-items:start}
.book h2{font-family:'Tenor Sans',serif;font-size:clamp(2.4rem,5vw,3.6rem);line-height:1;color:var(--ink);letter-spacing:.005em}
.book h2 em{font-family:'Italiana',serif;font-style:italic;color:var(--accent)}
.book .copy{color:var(--muted);font-style:italic;margin-top:1.4rem;font-size:1.05rem;line-height:1.7;max-width:38ch}
.book .lines{display:grid;grid-template-columns:1fr 1fr;gap:1.6rem 2.4rem}
.book b{display:block;font-family:'DM Sans',sans-serif;font-weight:500;font-size:.7rem;letter-spacing:.4em;text-transform:uppercase;color:var(--accent);margin-bottom:.4rem}
.book a,.book span{font-family:'Italiana',serif;color:var(--ink);font-size:1.2rem;text-decoration:none;border-bottom:1px solid var(--rule);padding-bottom:.2rem;transition:all .3s}
.book a:hover{color:var(--accent);border-color:var(--accent)}

footer{padding:2.5rem 0;text-align:center;font-size:.72rem;letter-spacing:.4em;text-transform:uppercase;color:var(--muted);margin-top:2rem}
footer .accent{color:var(--accent);font-family:'Italiana',serif;letter-spacing:0;text-transform:none;font-size:1rem}

@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
.r{opacity:0;animation:rise 1s cubic-bezier(.2,.7,.2,1) forwards}
.d1{animation-delay:.1s}.d2{animation-delay:.25s}.d3{animation-delay:.4s}.d4{animation-delay:.55s}.d5{animation-delay:.7s}

@media(max-width:820px){
  .hero{padding:5rem 0 4rem}
  .svc-grid{grid-template-columns:1fr;gap:2.5rem}
  .svc{border-right:none;border-bottom:1px solid var(--rule);padding-bottom:2rem}
  .svc:last-child{border-bottom:none}
  .book{grid-template-columns:1fr;gap:2rem}
  .book .lines{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div class="shell">

  <header class="topbar r d1">
    <div class="mark">__BIZ_NAME__</div>
    <div>__BIZ_CATEGORY__ · __BIZ_CITY__ · BY APPOINTMENT</div>
  </header>

  <section class="hero">
    <div class="pulse"></div>
    <div class="content">
      <div class="eyebrow r d1">VOL. 01 — __BIZ_CATEGORY__</div>
      <h1 class="r d2">__BIZ_NAME__<br><em>of __BIZ_CITY__</em></h1>
      <div class="tagline r d3">__HEADLINE__</div>

      <!-- Henna SVG underline -->
      <svg class="hennaline r d4" viewBox="0 0 280 24" fill="none" stroke="currentColor" stroke-width="1.2" preserveAspectRatio="none">
        <path d="M 0 12 Q 14 4, 28 12 T 56 12 Q 70 20, 84 12 T 112 12 Q 126 4, 140 12 T 168 12 Q 182 20, 196 12 T 224 12 Q 238 4, 252 12 T 280 12"/>
        <circle cx="14" cy="12" r="1.5" fill="currentColor"/>
        <circle cx="140" cy="12" r="2" fill="currentColor"/>
        <circle cx="266" cy="12" r="1.5" fill="currentColor"/>
      </svg>

      <p class="lede r d4">__LEDE__</p>
    </div>
    <div class="ctas r d5">
      <a class="btn fill" href="tel:__BIZ_PHONE__">Reserve a sitting</a>
      <a class="btn" href="#book">Booking notes</a>
    </div>
  </section>

  <section class="services">
    <div class="head">
      <div class="label">— THREE WAYS TO BOOK —</div>
      <h2>by the occasion.</h2>
    </div>
    <div class="svc-grid">
      <div class="svc r d2">
        <div class="lbl">i.</div>
        <h3>Bridal Sittings</h3>
        <p>Long, unhurried sittings. Consult, sketch, refine. We work to the look you'll be photographed in.</p>
        <div class="price">Half-day · From advance</div>
      </div>
      <div class="svc r d3">
        <div class="lbl">ii.</div>
        <h3>Festival Dates</h3>
        <p>Diwali, Karva Chauth, Eid, Onam — diary opens early; we close it once full. Book six weeks out.</p>
        <div class="price">Hourly · Per design</div>
      </div>
      <div class="svc r d4">
        <div class="lbl">iii.</div>
        <h3>Private Visits</h3>
        <p>For groups, families, or studio guests. We come to you, with kit, with calm, with time.</p>
        <div class="price">By arrangement</div>
      </div>
    </div>
  </section>

  <section class="quote">
    <q>The day belongs to you. We are simply the small, careful work that quietly carries it through every photograph.</q>
    <div class="sig">— from the studio diary</div>
  </section>

  <section class="book" id="book">
    <div>
      <h2>Reserve a <em>sitting.</em></h2>
      <p class="copy">A short call is the best place to begin. Tell us the date, the occasion, and what you have in mind — we'll send notes, references, and a soft hold on the diary.</p>
    </div>
    <div class="lines">
      <div><b>Telephone</b><a href="tel:__BIZ_PHONE__">__BIZ_PHONE__</a></div>
      <div><b>Studio</b><a href="https://maps.google.com/?q=__BIZ_ADDRESS__, __BIZ_CITY__" target="_blank" rel="noopener">__BIZ_ADDRESS__, __BIZ_CITY__</a></div>
      <div><b>Lead Time</b><span>Six weeks for festival · longer for bridal</span></div>
      <div><b>Studio Hours</b><span>By appointment · most afternoons</span></div>
    </div>
  </section>

</div>

<footer>
  © 2025 · <span class="accent">__BIZ_NAME__</span> · __BIZ_CITY__ · diary by appointment
</footer>

</body>
</html>"""
