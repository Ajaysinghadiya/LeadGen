"""Modern salon/boutique archetype — salon, boutique, tailor, fashion.
Fraunces (var opsz) display + DM Sans body. Ivory bg, terracotta/sage/plum accents.
Signature: split layout text-left/image-right, diagonal clip on image edge,
gold underline animation on hover."""

PALETTE_POOL = [
    {"bg": "#faf6ef", "ink": "#1a1a1a", "accent": "#c47a4f", "accent2": "#c9a961"},  # terracotta
    {"bg": "#f5f1e8", "ink": "#1f1f1d", "accent": "#6b7d5a", "accent2": "#a78550"},  # sage
    {"bg": "#f7eee8", "ink": "#1a1a1a", "accent": "#7d4f5e", "accent2": "#c9a961"},  # plum
]

HEADLINE_POOL = [
    "made for the every-day, finished for the occasion.",
    "where the fitting takes longer than the alteration.",
    "small batch, hand cut, properly finished.",
    "we keep the customers, not the queues.",
    "an old idea: take your time, get it right.",
]

LEDE_POOL = [
    "A studio that still believes the right cut and the right finish are worth waiting one extra day for.",
    "We work appointment-first. The room is quiet, the chai is hot, and the measuring tape has been around longer than most stylists.",
    "Founded on the unfashionable idea that a fitting is a conversation, not a transaction.",
    "Soft hands, sharp scissors. We do the kind of work that makes people ask where you went.",
    "A small room in __BIZ_CITY__, kept tidy, run on referrals — the way it used to be done.",
]

# Inline SVG photo placeholder — abstract textured swatch (per palette).
TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="description" content="__BIZ_NAME__ — __BIZ_CATEGORY__ in __BIZ_CITY__. By appointment, by referral." />
<title>__BIZ_NAME__ — __BIZ_CATEGORY__ · __BIZ_CITY__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;1,9..144,300;1,9..144,500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:__BG__;--ink:__INK__;--accent:__ACCENT__;--accent2:__ACCENT2__;--muted:#6b6b6b;--rule:#dcd4c5;}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif;font-weight:300;line-height:1.6;overflow-x:hidden}
::selection{background:var(--accent);color:var(--bg)}

.shell{max-width:1340px;margin:0 auto;padding:2rem 2.5rem}

.topbar{display:flex;justify-content:space-between;align-items:center;padding:1.5rem 0;border-bottom:1px solid var(--rule);font-size:.8rem;letter-spacing:.04em;color:var(--muted)}
.topbar .mark{font-family:'Fraunces',serif;font-style:italic;font-weight:500;color:var(--ink);font-size:1rem;letter-spacing:0}
.topbar nav{display:flex;gap:1.8rem}
.topbar a{color:var(--muted);text-decoration:none;position:relative;padding-bottom:.2rem;transition:color .25s}
.topbar a::after{content:'';position:absolute;left:0;bottom:0;width:0;height:1px;background:var(--accent);transition:width .35s ease}
.topbar a:hover{color:var(--ink)}
.topbar a:hover::after{width:100%}

.hero{display:grid;grid-template-columns:1.15fr .85fr;gap:0;align-items:stretch;padding:4rem 0 5rem;min-height:75vh}
.hero .text{padding:3rem 4rem 3rem 0;display:flex;flex-direction:column;justify-content:center}
.hero .eyebrow{font-size:.78rem;letter-spacing:.32em;text-transform:uppercase;color:var(--accent);margin-bottom:1.5rem;display:flex;align-items:center;gap:.7rem}
.hero .eyebrow::before{content:'';width:36px;height:1px;background:var(--accent)}
.hero h1{font-family:'Fraunces',serif;font-variation-settings:"opsz" 144;font-weight:500;font-size:clamp(3rem,7.5vw,5.8rem);line-height:1;letter-spacing:-.02em;color:var(--ink)}
.hero h1 em{font-style:italic;font-weight:300;color:var(--accent)}
.hero .lede{font-family:'Fraunces',serif;font-variation-settings:"opsz" 14;font-weight:300;font-size:1.18rem;color:var(--muted);max-width:46ch;margin-top:2rem;line-height:1.55}
.hero .meta{margin-top:2.4rem;display:flex;gap:2rem;font-family:'Fraunces',serif;font-style:italic;color:var(--muted);font-size:.92rem;flex-wrap:wrap}
.hero .meta b{font-style:normal;font-family:'DM Sans',sans-serif;font-weight:500;color:var(--ink);letter-spacing:.18em;text-transform:uppercase;font-size:.7rem;display:block;margin-bottom:.3rem}
.hero .ctas{display:flex;gap:.8rem;margin-top:2.6rem;flex-wrap:wrap}

.btn{font-family:'DM Sans',sans-serif;font-weight:500;font-size:.85rem;letter-spacing:.16em;text-transform:uppercase;text-decoration:none;padding:.95rem 1.8rem;border:1px solid var(--ink);color:var(--ink);transition:all .3s;display:inline-block}
.btn.fill{background:var(--accent);border-color:var(--accent);color:#fff}
.btn:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--accent2)}

/* Image column — diagonal-clip swatch */
.hero .img{position:relative;clip-path:polygon(8% 0,100% 0,100% 100%,0% 100%);background:linear-gradient(135deg,var(--accent) 0%,var(--accent2) 60%,var(--ink) 140%);overflow:hidden;display:flex;align-items:flex-end;justify-content:center;padding:3rem 2rem}
.hero .img::before{content:'';position:absolute;inset:0;background:radial-gradient(600px 400px at 70% 30%,rgba(255,255,255,.18),transparent 60%);pointer-events:none}
.hero .img::after{content:'';position:absolute;inset:0;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.4'/></svg>");opacity:.18;mix-blend-mode:overlay;pointer-events:none}
.hero .img .stamp{font-family:'Fraunces',serif;font-style:italic;font-size:1.3rem;color:rgba(255,255,255,.92);letter-spacing:.1em;text-align:center;padding:1.5rem 2rem;border:1px solid rgba(255,255,255,.45);backdrop-filter:blur(2px);position:relative;z-index:1}
.hero .img .stamp small{display:block;font-style:normal;font-family:'DM Sans',sans-serif;font-weight:500;font-size:.7rem;letter-spacing:.32em;text-transform:uppercase;color:rgba(255,255,255,.72);margin-bottom:.5rem}

/* Services row */
.services{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--rule);border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);margin:3rem 0}
.svc{background:var(--bg);padding:2.4rem 1.6rem;transition:background .3s}
.svc:hover{background:#fff}
.svc .num{font-family:'Fraunces',serif;font-style:italic;font-weight:300;color:var(--accent);font-size:1.2rem;margin-bottom:1rem;letter-spacing:.04em}
.svc h4{font-family:'Fraunces',serif;font-weight:500;font-size:1.15rem;margin-bottom:.4rem}
.svc p{color:var(--muted);font-size:.88rem;line-height:1.6}

/* Pull quote */
.quote{padding:6rem 2rem;text-align:center;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.quote q{font-family:'Fraunces',serif;font-variation-settings:"opsz" 60;font-style:italic;font-weight:300;font-size:clamp(1.4rem,3vw,2.2rem);line-height:1.45;color:var(--ink);max-width:780px;margin:0 auto;display:block;quotes:none}
.quote q::before,.quote q::after{content:''}
.quote .sig{font-size:.78rem;letter-spacing:.28em;text-transform:uppercase;color:var(--accent);margin-top:2rem}

/* Visit */
.visit{display:grid;grid-template-columns:1fr 1.2fr;gap:4rem;padding:5rem 0;align-items:center}
.visit h2{font-family:'Fraunces',serif;font-variation-settings:"opsz" 144;font-weight:500;font-size:clamp(2.2rem,5vw,3.6rem);line-height:1;letter-spacing:-.02em}
.visit h2 em{font-style:italic;color:var(--accent);font-weight:300}
.visit .grid{display:grid;grid-template-columns:1fr 1fr;gap:2rem 3rem}
.visit b{font-size:.7rem;letter-spacing:.28em;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:.4rem;font-weight:500}
.visit a{font-family:'Fraunces',serif;font-style:italic;color:var(--ink);text-decoration:none;font-size:1.1rem;border-bottom:1px solid var(--rule);padding-bottom:.2rem;transition:all .25s}
.visit a:hover{color:var(--accent);border-color:var(--accent)}

footer{display:flex;justify-content:space-between;align-items:center;padding:2rem 0;border-top:1px solid var(--rule);font-size:.78rem;letter-spacing:.18em;text-transform:uppercase;color:var(--muted)}
footer .accent{color:var(--accent);font-family:'Fraunces',serif;font-style:italic;letter-spacing:0;text-transform:none;font-size:.95rem}

@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
.r{opacity:0;animation:rise .9s cubic-bezier(.2,.7,.2,1) forwards}
.d1{animation-delay:.05s}.d2{animation-delay:.18s}.d3{animation-delay:.32s}.d4{animation-delay:.46s}.d5{animation-delay:.6s}

@media(max-width:880px){
  .hero{grid-template-columns:1fr;min-height:auto}
  .hero .text{padding:2rem 0 3rem}
  .hero .img{clip-path:none;min-height:340px}
  .services{grid-template-columns:1fr 1fr}
  .visit{grid-template-columns:1fr;gap:2.5rem}
  .visit .grid{grid-template-columns:1fr}
  .topbar nav{display:none}
}
</style>
</head>
<body>
<div class="shell">

  <header class="topbar r d1">
    <div class="mark">— __BIZ_NAME__</div>
    <nav>
      <a href="#services">Services</a>
      <a href="#visit">Visit</a>
      <a href="tel:__BIZ_PHONE__">Telephone</a>
    </nav>
  </header>

  <section class="hero">
    <div class="text">
      <div class="eyebrow r d2">№ 01 — __BIZ_CATEGORY__ · __BIZ_CITY__</div>
      <h1 class="r d3">__BIZ_NAME__<br><em>— __HEADLINE__</em></h1>
      <p class="lede r d4">__LEDE__</p>
      <div class="meta r d4">
        <div><b>By appointment</b><span>Walk-ins welcomed</span></div>
        <div><b>Quietly run since</b><span>Generations</span></div>
      </div>
      <div class="ctas r d5">
        <a class="btn fill" href="tel:__BIZ_PHONE__">Book a fitting</a>
        <a class="btn" href="#visit">Find the studio</a>
      </div>
    </div>
    <div class="img r d3">
      <div class="stamp"><small>Studio · __BIZ_CITY__</small>__BIZ_NAME__</div>
    </div>
  </section>

  <section class="services" id="services">
    <div class="svc r d2"><div class="num">01 / Consult</div><h4>The first conversation</h4><p>Tea, fabric swatches, a long look at what you already wear. We listen first.</p></div>
    <div class="svc r d3"><div class="num">02 / Cut</div><h4>By the hand that's done it</h4><p>One pair of hands per piece, start to finish. The seam knows the shoulder.</p></div>
    <div class="svc r d4"><div class="num">03 / Finish</div><h4>The slow last hour</h4><p>Every garment leaves the studio pressed, lined, and looked over twice.</p></div>
    <div class="svc r d5"><div class="num">04 / Keep</div><h4>For as long as you wear it</h4><p>Free alteration in the first year. Half-cost forever after. Nothing is disposable.</p></div>
  </section>

  <section class="quote">
    <q>I have not had to explain how something should fit since I started coming here. They simply know.</q>
    <div class="sig">— A regular, since the beginning</div>
  </section>

  <section class="visit" id="visit">
    <div>
      <h2>Come <em>by, slowly.</em></h2>
      <p style="color:var(--muted);font-family:'Fraunces',serif;font-style:italic;margin-top:1.4rem;max-width:34ch;">Tea is poured. Bring a piece you already love and we'll talk from there.</p>
    </div>
    <div class="grid">
      <div><b>Telephone</b><a href="tel:__BIZ_PHONE__">__BIZ_PHONE__</a></div>
      <div><b>The Studio</b><a href="https://maps.google.com/?q=__BIZ_ADDRESS__, __BIZ_CITY__" target="_blank" rel="noopener">__BIZ_ADDRESS__, __BIZ_CITY__</a></div>
      <div><b>Hours</b><span>Tuesday — Sunday · 11–7</span></div>
      <div><b>Appointments</b><span>Always preferred · never required</span></div>
    </div>
  </section>

</div>

<footer class="shell" style="padding-top:0">
  <div>© 2025 · __BIZ_NAME__</div>
  <div class="accent">— a small studio in __BIZ_CITY__</div>
  <div>Vol. 01</div>
</footer>

</body>
</html>"""
