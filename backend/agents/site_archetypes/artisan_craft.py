"""Artisan craft archetype — pattachitra, thanka, sculpture, painting, handicraft.
Cormorant Infant display + Crimson Pro body. Dark ink bg, brass/vermillion accents.
Signature: hand-drawn SVG ornament corners (chevron+lotus), kerned all-caps eyebrow."""

PALETTE_POOL = [
    {"bg": "#0e0e0c", "ink": "#f0e8d4", "accent": "#cf9b3e", "accent2": "#b8392f"},  # vermillion
    {"bg": "#101218", "ink": "#ede4c8", "accent": "#c9a548", "accent2": "#3d4e7d"},  # indigo
    {"bg": "#15110b", "ink": "#f5e8c4", "accent": "#a87830", "accent2": "#d97706"},  # saffron
]

HEADLINE_POOL = [
    "the workshop, kept open.",
    "drawn slowly, finished slower.",
    "where the line still matters.",
    "an old craft, in present tense.",
    "small studio, long hours.",
]

LEDE_POOL = [
    "A workshop kept open by the same hands that learned it. The work is slow because the work is slow; we make no apology for that.",
    "Pigments mixed at dawn. Lines drawn between cups of tea. A small body of work, kept honest, kept on.",
    "Inherited from a teacher; passed to whoever shows up early enough to watch. Studio visits welcomed.",
    "What you can buy here was made in this room, by someone you can meet, on a day you can name.",
    "The cloth is sized, the brush is fine, the patience is the point. Visit the workshop; leave with a piece that knows you.",
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="description" content="__BIZ_NAME__ — __BIZ_CATEGORY__ in __BIZ_CITY__. The workshop, kept open." />
<title>__BIZ_NAME__ · __BIZ_CATEGORY__ · __BIZ_CITY__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Infant:ital,wght@0,300;0,500;1,300;1,500&family=Crimson+Pro:ital,wght@0,300;0,500;1,300&display=swap" rel="stylesheet">
<style>
:root{--bg:__BG__;--ink:__INK__;--accent:__ACCENT__;--accent2:__ACCENT2__;--muted:#7a6a52;--rule:#2a241c;}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:'Crimson Pro',serif;font-weight:300;line-height:1.7;overflow-x:hidden}
::selection{background:var(--accent2);color:var(--bg)}

/* page grain */
body::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;opacity:.14;mix-blend-mode:overlay;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.55'/></svg>")}

.shell{max-width:1200px;margin:0 auto;padding:2.5rem 2.5rem;position:relative}

.topbar{display:flex;justify-content:space-between;align-items:center;padding-bottom:1.5rem;border-bottom:1px solid var(--rule);font-size:.75rem;letter-spacing:.32em;text-transform:uppercase;color:var(--muted);font-weight:400}
.topbar .mark{color:var(--accent);font-family:'Cormorant Infant',serif;font-style:italic;font-size:1.3rem;letter-spacing:0;text-transform:none}

/* ═══ Ornament corners ═══ */
.ornament{position:absolute;width:78px;height:78px;color:var(--accent);opacity:.7;animation:bloom 2.4s cubic-bezier(.2,.7,.2,1) forwards;opacity:0;transform:scale(.7)}
@keyframes bloom{from{opacity:0;transform:scale(.7)}to{opacity:.75;transform:scale(1)}}
.ornament.tl{top:-40px;left:-40px;animation-delay:.4s}
.ornament.tr{top:-40px;right:-40px;transform-origin:right top;transform:scaleX(-1) scale(.7);animation-delay:.55s}
.ornament.tr.bloom-done{transform:scaleX(-1) scale(1)}
.ornament.bl{bottom:-40px;left:-40px;transform-origin:left bottom;transform:scaleY(-1) scale(.7);animation-delay:.7s}
.ornament.br{bottom:-40px;right:-40px;transform-origin:right bottom;transform:scale(-1,-1) scale(.7);animation-delay:.85s}

/* ═══ Hero ═══ */
.hero{position:relative;padding:7rem 4rem 6rem;text-align:center;border:1px solid var(--rule);margin:3rem 0 4rem;background:radial-gradient(800px 500px at 50% 50%,color-mix(in srgb,var(--accent) 12%, transparent),transparent 60%)}
.hero .eyebrow{font-family:'Crimson Pro',serif;font-size:.75rem;letter-spacing:.5em;text-transform:uppercase;color:var(--accent);margin-bottom:2.4rem;font-weight:400}
.hero .eyebrow span{color:var(--muted);margin:0 .8em}
.hero h1{font-family:'Cormorant Infant',serif;font-weight:300;font-size:clamp(3rem,8vw,6.4rem);line-height:1.05;letter-spacing:-.005em;color:var(--ink)}
.hero h1 em{font-style:italic;color:var(--accent);font-weight:300}
.hero .tagline{font-family:'Cormorant Infant',serif;font-style:italic;font-size:1.4rem;color:var(--accent2);margin-top:1.4rem;letter-spacing:.04em}
.hero .lede{font-size:1.15rem;color:var(--muted);max-width:54ch;margin:2.4rem auto 0;line-height:1.7;font-weight:300}
.hero .ctas{display:flex;justify-content:center;gap:1rem;margin-top:2.6rem;flex-wrap:wrap}

.btn{font-family:'Crimson Pro',serif;font-weight:400;font-size:.78rem;letter-spacing:.32em;text-transform:uppercase;text-decoration:none;padding:1rem 1.8rem;border:1px solid var(--accent);color:var(--ink);transition:all .35s;display:inline-block;background:transparent}
.btn.fill{background:var(--accent);color:var(--bg)}
.btn:hover{background:var(--accent2);border-color:var(--accent2);color:var(--ink);letter-spacing:.4em}

/* ═══ Works ═══ */
.works{padding:4rem 0;text-align:center}
.works .head{font-family:'Crimson Pro',serif;font-size:.75rem;letter-spacing:.5em;text-transform:uppercase;color:var(--accent);margin-bottom:.8rem}
.works h2{font-family:'Cormorant Infant',serif;font-style:italic;font-weight:300;font-size:clamp(2rem,4.5vw,3.4rem);color:var(--ink);margin-bottom:3rem;line-height:1}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.tile{padding:3.4rem 2rem 3rem;border-right:1px solid var(--rule);text-align:left;position:relative;transition:background .4s}
.tile:last-child{border-right:none}
.tile:hover{background:color-mix(in srgb,var(--accent) 6%, transparent)}
.tile .roman{font-family:'Cormorant Infant',serif;font-style:italic;font-weight:300;font-size:2.4rem;color:var(--accent);line-height:1;margin-bottom:1.6rem;letter-spacing:.02em}
.tile h3{font-family:'Cormorant Infant',serif;font-weight:500;font-size:1.4rem;margin-bottom:.6rem;color:var(--ink);letter-spacing:.005em}
.tile p{color:var(--muted);font-size:1rem;line-height:1.7}

/* ═══ Quote / philosophy ═══ */
.philos{padding:6rem 2rem;text-align:center;position:relative}
.philos::before{content:'';position:absolute;left:50%;top:1rem;width:90px;height:2px;background:var(--accent);transform:translateX(-50%)}
.philos q{font-family:'Cormorant Infant',serif;font-style:italic;font-weight:300;font-size:clamp(1.5rem,3vw,2.2rem);line-height:1.5;color:var(--ink);max-width:780px;margin:0 auto;display:block;quotes:none}
.philos q::before,.philos q::after{content:''}
.philos .sig{font-size:.78rem;letter-spacing:.4em;text-transform:uppercase;color:var(--accent);margin-top:2rem}

/* ═══ Visit ═══ */
.visit{padding:5rem 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);display:grid;grid-template-columns:1fr 1.3fr;gap:4rem;align-items:start}
.visit h2{font-family:'Cormorant Infant',serif;font-weight:300;font-size:clamp(2.4rem,5vw,3.6rem);line-height:1;color:var(--ink)}
.visit h2 em{font-style:italic;color:var(--accent)}
.visit .copy{color:var(--muted);font-size:1.05rem;margin-top:1.4rem;font-style:italic}
.visit .lines{display:grid;grid-template-columns:1fr 1fr;gap:1.6rem 2.4rem}
.visit b{display:block;font-family:'Crimson Pro',serif;font-weight:400;font-size:.7rem;letter-spacing:.4em;text-transform:uppercase;color:var(--accent);margin-bottom:.4rem}
.visit a,.visit span{font-family:'Cormorant Infant',serif;font-style:italic;color:var(--ink);font-size:1.15rem;text-decoration:none;border-bottom:1px solid var(--rule);padding-bottom:.2rem;transition:all .3s}
.visit a:hover{color:var(--accent);border-color:var(--accent)}

footer{padding:2.4rem 0;text-align:center;font-size:.72rem;letter-spacing:.4em;text-transform:uppercase;color:var(--muted);border-top:1px solid var(--rule);margin-top:2rem}
footer .accent{color:var(--accent);font-family:'Cormorant Infant',serif;font-style:italic;letter-spacing:0;text-transform:none;font-size:1rem}

@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
.r{opacity:0;animation:rise 1.1s cubic-bezier(.2,.7,.2,1) forwards}
.d1{animation-delay:.1s}.d2{animation-delay:.25s}.d3{animation-delay:.4s}.d4{animation-delay:.55s}.d5{animation-delay:.7s}

@media(max-width:820px){
  .hero{padding:4rem 1.5rem}
  .grid{grid-template-columns:1fr}
  .tile{border-right:none;border-bottom:1px solid var(--rule)}
  .tile:last-child{border-bottom:none}
  .visit{grid-template-columns:1fr;gap:2rem}
  .visit .lines{grid-template-columns:1fr}
  .ornament{display:none}
}
</style>
</head>
<body>
<div class="shell">

  <header class="topbar r d1">
    <div class="mark">__BIZ_NAME__</div>
    <div>__BIZ_CITY__ · A WORKSHOP · EST. LOCALLY</div>
  </header>

  <section class="hero r d2">
    <!-- Hand-drawn ornament corners -->
    <svg class="ornament tl" viewBox="0 0 60 60" fill="none" stroke="currentColor" stroke-width="1.2">
      <path d="M 0 30 L 12 30 L 12 18 L 24 18 L 24 6 L 36 6 L 36 0"/>
      <circle cx="30" cy="30" r="3" fill="currentColor"/>
      <path d="M 30 30 Q 42 30, 42 42 Q 42 54, 30 54" fill="none"/>
    </svg>
    <svg class="ornament tr" viewBox="0 0 60 60" fill="none" stroke="currentColor" stroke-width="1.2">
      <path d="M 0 30 L 12 30 L 12 18 L 24 18 L 24 6 L 36 6 L 36 0"/>
      <circle cx="30" cy="30" r="3" fill="currentColor"/>
      <path d="M 30 30 Q 42 30, 42 42 Q 42 54, 30 54" fill="none"/>
    </svg>
    <svg class="ornament bl" viewBox="0 0 60 60" fill="none" stroke="currentColor" stroke-width="1.2">
      <path d="M 0 30 L 12 30 L 12 18 L 24 18 L 24 6 L 36 6 L 36 0"/>
      <circle cx="30" cy="30" r="3" fill="currentColor"/>
      <path d="M 30 30 Q 42 30, 42 42 Q 42 54, 30 54" fill="none"/>
    </svg>
    <svg class="ornament br" viewBox="0 0 60 60" fill="none" stroke="currentColor" stroke-width="1.2">
      <path d="M 0 30 L 12 30 L 12 18 L 24 18 L 24 6 L 36 6 L 36 0"/>
      <circle cx="30" cy="30" r="3" fill="currentColor"/>
      <path d="M 30 30 Q 42 30, 42 42 Q 42 54, 30 54" fill="none"/>
    </svg>

    <div class="eyebrow">THE WORKSHOP <span>—</span> __BIZ_CATEGORY__ <span>—</span> __BIZ_CITY__</div>
    <h1>__BIZ_NAME__<br><em>— of __BIZ_CITY__</em></h1>
    <div class="tagline">__HEADLINE__</div>
    <p class="lede">__LEDE__</p>
    <div class="ctas">
      <a class="btn fill" href="tel:__BIZ_PHONE__">Call the studio</a>
      <a class="btn" href="#visit">Plan a visit</a>
    </div>
  </section>

  <section class="works">
    <div class="head r d2">— THREE NOTES ON THE WORK —</div>
    <h2 class="r d3">how the work is done.</h2>
    <div class="grid">
      <div class="tile r d3">
        <div class="roman">i.</div>
        <h3>The Pigment</h3>
        <p>Stone-ground, hand-mixed, kept in small jars on a small shelf. The colour is the first decision; the rest follows.</p>
      </div>
      <div class="tile r d4">
        <div class="roman">ii.</div>
        <h3>The Line</h3>
        <p>One brush, several years of practice, no shortcut. We charge for hours kept, not pieces moved.</p>
      </div>
      <div class="tile r d5">
        <div class="roman">iii.</div>
        <h3>The Quiet</h3>
        <p>Visitors are welcome by appointment. The studio is calm; the work goes faster when it isn't watched.</p>
      </div>
    </div>
  </section>

  <section class="philos">
    <q>An object made by hand carries a small piece of the maker's afternoon. We try to make objects worthy of an afternoon.</q>
    <div class="sig">— from the studio note</div>
  </section>

  <section class="visit" id="visit">
    <div>
      <h2>Visit the <em>workshop.</em></h2>
      <p class="copy">Studio visits by appointment. Tea is poured; the work is shown; you leave with whatever feels right.</p>
    </div>
    <div class="lines">
      <div><b>Telephone</b><a href="tel:__BIZ_PHONE__">__BIZ_PHONE__</a></div>
      <div><b>Studio</b><a href="https://maps.google.com/?q=__BIZ_ADDRESS__, __BIZ_CITY__" target="_blank" rel="noopener">__BIZ_ADDRESS__, __BIZ_CITY__</a></div>
      <div><b>Hours</b><span>Most days · 10–6 · by arrangement</span></div>
      <div><b>Commissions</b><span>Welcomed · time taken seriously</span></div>
    </div>
  </section>

</div>

<footer>
  © 2025 · <span class="accent">__BIZ_NAME__</span> · __BIZ_CITY__
</footer>

</body>
</html>"""
