"""Luxury jewellery archetype — jewellery, gold, diamond, bridal jewellery.
Marcellus display + Outfit body. Cream bg, gold/platinum/emerald accents.
Signature: 16-ray gold sun-burst SVG behind name, custom gold cursor-dot follower."""

PALETTE_POOL = [
    {"bg": "#fff8f0", "ink": "#1a0a0a", "accent": "#d4af37", "accent2": "#c9988a"},  # gold
    {"bg": "#fafafa", "ink": "#0a0a0a", "accent": "#a8a8a8", "accent2": "#dabbb0"},  # platinum
    {"bg": "#fff8f0", "ink": "#0d1410", "accent": "#4a7c59", "accent2": "#d4af37"},  # emerald
]

HEADLINE_POOL = [
    "Heirlooms, made carefully.",
    "Quietly, patiently, in gold.",
    "Pieces meant to outlast their owners.",
    "The kind of work that stays in the family.",
    "Made to be left to someone.",
]

LEDE_POOL = [
    "A small atelier where every piece is sketched in a notebook before it is touched in metal. We don't push trends — we make things meant to last decades.",
    "Hand-finished, hallmark-stamped, made with the slow patience of three generations. We will tell you what your stone can do; we will not oversell what it cannot.",
    "Family jeweller in __BIZ_CITY__, by appointment, by referral. Our quietest customers are our oldest ones.",
    "Designed in-studio, finished by the same hands that drew it. Every piece comes with a note about the maker, the metal, and the days the work took.",
    "A workshop the size of a small room, a clientele the depth of one neighbourhood. We sell to the people we expect to see again.",
]

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="description" content="__BIZ_NAME__ — __BIZ_CATEGORY__ in __BIZ_CITY__. Heirlooms, made carefully." />
<title>__BIZ_NAME__ · __BIZ_CATEGORY__ · __BIZ_CITY__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Outfit:wght@200;300;400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:__BG__;--ink:__INK__;--accent:__ACCENT__;--accent2:__ACCENT2__;--muted:#7a6a52;--rule:#e6d9c2;}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:'Outfit',sans-serif;font-weight:300;line-height:1.65;overflow-x:hidden;cursor:none}
::selection{background:var(--accent);color:#fff}

/* ═══ Custom cursor dot ═══ */
.cursor{position:fixed;width:14px;height:14px;border-radius:50%;background:var(--accent);pointer-events:none;z-index:9999;transform:translate(-50%,-50%);transition:width .2s,height .2s,background .2s;mix-blend-mode:difference}
.cursor-ring{position:fixed;width:42px;height:42px;border-radius:50%;border:1px solid var(--accent);pointer-events:none;z-index:9998;transform:translate(-50%,-50%);transition:transform .2s ease-out;opacity:.5}
@media(hover:none){.cursor,.cursor-ring{display:none}body{cursor:auto}}

.shell{max-width:1240px;margin:0 auto;padding:2.5rem 2.5rem;position:relative}

.topbar{display:flex;justify-content:space-between;align-items:center;padding-bottom:1.5rem;border-bottom:1px solid var(--rule);font-size:.72rem;letter-spacing:.4em;text-transform:uppercase;color:var(--muted);font-weight:400}
.topbar .mark{font-family:'Marcellus',serif;font-size:1.6rem;color:var(--ink);letter-spacing:.04em;text-transform:none}

/* ═══ Hero with sun-burst SVG behind ═══ */
.hero{position:relative;padding:8rem 0 7rem;text-align:center;overflow:hidden}
.sunburst{position:absolute;top:50%;left:50%;width:780px;height:780px;transform:translate(-50%,-50%);z-index:0;color:var(--accent);opacity:.18;animation:sunturn 80s linear infinite}
@keyframes sunturn{from{transform:translate(-50%,-50%) rotate(0)}to{transform:translate(-50%,-50%) rotate(360deg)}}

.hero .content{position:relative;z-index:1}
.hero .eyebrow{font-family:'Outfit',sans-serif;font-weight:400;font-size:.72rem;letter-spacing:.5em;text-transform:uppercase;color:var(--accent);margin-bottom:2.4rem;display:inline-flex;align-items:center;gap:1.4rem}
.hero .eyebrow .mark{width:8px;height:8px;background:var(--accent);transform:rotate(45deg)}
.hero h1{font-family:'Marcellus',serif;font-weight:400;font-size:clamp(3.4rem,9vw,7.4rem);line-height:1;letter-spacing:.005em;color:var(--ink)}
.hero h1 em{color:var(--accent);font-style:italic;font-family:'Marcellus',serif}
.hero .tagline{font-family:'Marcellus',serif;font-style:italic;font-size:1.5rem;color:var(--accent2);margin-top:1.6rem;letter-spacing:.04em}
.hero .lede{font-size:1.12rem;color:var(--muted);max-width:54ch;margin:2.4rem auto 0;line-height:1.7;font-weight:300}

.ctas{display:flex;justify-content:center;gap:1rem;margin-top:2.6rem;flex-wrap:wrap;position:relative;z-index:1}
.btn{font-family:'Outfit',sans-serif;font-weight:400;font-size:.78rem;letter-spacing:.32em;text-transform:uppercase;text-decoration:none;padding:1.05rem 2rem;border:1px solid var(--accent);color:var(--ink);transition:all .35s;display:inline-block;background:transparent;cursor:none}
.btn.fill{background:var(--accent);color:var(--bg)}
.btn:hover{background:var(--ink);border-color:var(--ink);color:var(--bg);transform:translateY(-2px)}

/* ═══ Section divider ═══ */
.divider{display:flex;justify-content:center;align-items:center;gap:1.4rem;padding:4rem 0 2rem;font-size:.72rem;letter-spacing:.5em;text-transform:uppercase;color:var(--muted);font-family:'Outfit',sans-serif}
.divider svg{width:14px;height:14px;color:var(--accent)}

/* ═══ Atelier collections ═══ */
.atelier{padding:2rem 0 6rem}
.atelier-head{text-align:center;max-width:640px;margin:0 auto 4rem}
.atelier-head h2{font-family:'Marcellus',serif;font-size:clamp(2.4rem,5vw,3.8rem);line-height:1;color:var(--ink);margin-bottom:1.2rem}
.atelier-head h2 em{color:var(--accent);font-style:italic}
.atelier-head p{color:var(--muted);font-size:1.05rem;line-height:1.7}

.coll{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.piece{padding:3rem 2.4rem;text-align:center;border-right:1px solid var(--rule);position:relative}
.piece:last-child{border-right:none}
.piece .ornament{margin:0 auto 1.4rem;width:40px;height:40px;color:var(--accent)}
.piece h3{font-family:'Marcellus',serif;font-size:1.4rem;color:var(--ink);margin-bottom:.5rem}
.piece h3 em{color:var(--accent);font-style:italic}
.piece p{color:var(--muted);font-size:.95rem;line-height:1.65}
.piece .meta{font-family:'Marcellus',serif;font-style:italic;font-size:.95rem;color:var(--accent);margin-top:1.3rem;letter-spacing:.04em}

/* ═══ Provenance quote ═══ */
.prov{padding:6rem 2rem;text-align:center;background:linear-gradient(180deg,transparent,color-mix(in srgb,var(--accent) 8%, transparent),transparent)}
.prov q{font-family:'Marcellus',serif;font-style:italic;font-size:clamp(1.5rem,3vw,2.2rem);line-height:1.5;color:var(--ink);max-width:780px;margin:0 auto;display:block;quotes:none}
.prov q::before,.prov q::after{content:''}
.prov .sig{font-family:'Outfit',sans-serif;font-weight:400;font-size:.72rem;letter-spacing:.4em;text-transform:uppercase;color:var(--accent);margin-top:2rem}

/* ═══ Visit ═══ */
.visit{padding:5rem 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);display:grid;grid-template-columns:1fr 1.3fr;gap:4rem;align-items:start}
.visit h2{font-family:'Marcellus',serif;font-size:clamp(2.4rem,5vw,3.6rem);line-height:1;color:var(--ink)}
.visit h2 em{font-style:italic;color:var(--accent)}
.visit .copy{color:var(--muted);margin-top:1.4rem;font-size:1.05rem;line-height:1.7;max-width:38ch;font-style:italic;font-family:'Marcellus',serif}
.visit .lines{display:grid;grid-template-columns:1fr 1fr;gap:1.6rem 2.4rem}
.visit b{display:block;font-family:'Outfit',sans-serif;font-weight:500;font-size:.7rem;letter-spacing:.4em;text-transform:uppercase;color:var(--accent);margin-bottom:.4rem}
.visit a,.visit span{font-family:'Marcellus',serif;color:var(--ink);font-size:1.2rem;text-decoration:none;border-bottom:1px solid var(--rule);padding-bottom:.2rem;transition:all .3s;cursor:none}
.visit a:hover{color:var(--accent);border-color:var(--accent)}

footer{padding:2.5rem 0;text-align:center;font-size:.72rem;letter-spacing:.4em;text-transform:uppercase;color:var(--muted);margin-top:1rem}
footer .accent{color:var(--accent);font-family:'Marcellus',serif;letter-spacing:0;text-transform:none;font-size:1rem}

@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
.r{opacity:0;animation:rise 1s cubic-bezier(.2,.7,.2,1) forwards}
.d1{animation-delay:.1s}.d2{animation-delay:.25s}.d3{animation-delay:.4s}.d4{animation-delay:.55s}.d5{animation-delay:.7s}

@media(max-width:820px){
  .sunburst{width:480px;height:480px}
  .hero{padding:5rem 0 4rem}
  .coll{grid-template-columns:1fr}
  .piece{border-right:none;border-bottom:1px solid var(--rule)}
  .piece:last-child{border-bottom:none}
  .visit{grid-template-columns:1fr;gap:2rem}
  .visit .lines{grid-template-columns:1fr}
}
</style>
</head>
<body>

<div class="cursor"></div>
<div class="cursor-ring"></div>

<div class="shell">

  <header class="topbar r d1">
    <div class="mark">__BIZ_NAME__</div>
    <div>__BIZ_CATEGORY__ · __BIZ_CITY__ · BY APPOINTMENT</div>
  </header>

  <section class="hero">
    <!-- 16-ray sun-burst SVG -->
    <svg class="sunburst" viewBox="0 0 200 200" fill="none" stroke="currentColor" stroke-width="0.4" xmlns="http://www.w3.org/2000/svg">
      <g>
        <line x1="100" y1="0"   x2="100" y2="100"/>
        <line x1="100" y1="200" x2="100" y2="100"/>
        <line x1="0"   y1="100" x2="100" y2="100"/>
        <line x1="200" y1="100" x2="100" y2="100"/>
        <line x1="29.3" y1="29.3"  x2="100" y2="100"/>
        <line x1="170.7" y1="29.3" x2="100" y2="100"/>
        <line x1="29.3" y1="170.7" x2="100" y2="100"/>
        <line x1="170.7" y1="170.7" x2="100" y2="100"/>
        <line x1="100" y1="0"   x2="138.3" y2="7.6"/>
        <line x1="100" y1="0"   x2="61.7"  y2="7.6"/>
        <line x1="200" y1="100" x2="192.4" y2="138.3"/>
        <line x1="200" y1="100" x2="192.4" y2="61.7"/>
        <line x1="100" y1="200" x2="138.3" y2="192.4"/>
        <line x1="100" y1="200" x2="61.7"  y2="192.4"/>
        <line x1="0"   y1="100" x2="7.6"   y2="138.3"/>
        <line x1="0"   y1="100" x2="7.6"   y2="61.7"/>
        <circle cx="100" cy="100" r="62" stroke-width="0.5"/>
        <circle cx="100" cy="100" r="40" stroke-width="0.5"/>
        <circle cx="100" cy="100" r="22" stroke-width="0.7"/>
      </g>
    </svg>

    <div class="content">
      <div class="eyebrow r d1"><span class="mark"></span>VOL. 01 — __BIZ_CATEGORY__<span class="mark"></span></div>
      <h1 class="r d2">__BIZ_NAME__<br><em>of __BIZ_CITY__</em></h1>
      <div class="tagline r d3">__HEADLINE__</div>
      <p class="lede r d4">__LEDE__</p>
    </div>
    <div class="ctas r d5">
      <a class="btn fill" href="tel:__BIZ_PHONE__">Request a viewing</a>
      <a class="btn" href="#visit">Find the atelier</a>
    </div>
  </section>

  <div class="divider">
    <svg viewBox="0 0 12 12" fill="currentColor"><polygon points="6,0 7,5 12,6 7,7 6,12 5,7 0,6 5,5"/></svg>
    THE ATELIER
    <svg viewBox="0 0 12 12" fill="currentColor"><polygon points="6,0 7,5 12,6 7,7 6,12 5,7 0,6 5,5"/></svg>
  </div>

  <section class="atelier">
    <div class="atelier-head">
      <h2>Three quiet <em>collections.</em></h2>
      <p>Each piece is drawn before it is made and made before it is shown. We keep the cataloguing the way we keep the metal: slowly, and well.</p>
    </div>
    <div class="coll">
      <div class="piece r d2">
        <svg class="ornament" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.2"><circle cx="20" cy="20" r="8"/><circle cx="20" cy="20" r="14" stroke-dasharray="2 3"/></svg>
        <h3>Bridal &amp; <em>Trousseau</em></h3>
        <p>Sets designed across visits, sketched in front of you, made in the room next door. Hallmark-stamped, certificate-issued.</p>
        <div class="meta">— by appointment</div>
      </div>
      <div class="piece r d3">
        <svg class="ornament" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.2"><polygon points="20,4 30,16 26,32 14,32 10,16"/><circle cx="20" cy="20" r="3" fill="currentColor"/></svg>
        <h3>Everyday <em>Heirloom</em></h3>
        <p>Solitaires, signets, pendant chains — small pieces that earn the wear they get and stay in the family quietly.</p>
        <div class="meta">— ready to wear</div>
      </div>
      <div class="piece r d4">
        <svg class="ornament" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M 4 20 Q 20 4, 36 20 Q 20 36, 4 20 Z"/><circle cx="20" cy="20" r="4" fill="currentColor"/></svg>
        <h3>Bespoke &amp; <em>Re-set</em></h3>
        <p>We re-imagine the stones already in the family. Old gold, old stories, fresh setting — all carefully kept.</p>
        <div class="meta">— quotation on viewing</div>
      </div>
    </div>
  </section>

  <section class="prov">
    <q>The pieces we like best are the ones that have left the shop and not come back. Worn quietly, kept long, eventually passed on.</q>
    <div class="sig">— from the studio note</div>
  </section>

  <section class="visit" id="visit">
    <div>
      <h2>Visit the <em>atelier.</em></h2>
      <p class="copy">A short call sets the time. The room is quiet, the chai is hot, the books and certificates are kept where you can see them.</p>
    </div>
    <div class="lines">
      <div><b>Telephone</b><a href="tel:__BIZ_PHONE__">__BIZ_PHONE__</a></div>
      <div><b>The Atelier</b><a href="https://maps.google.com/?q=__BIZ_ADDRESS__, __BIZ_CITY__" target="_blank" rel="noopener">__BIZ_ADDRESS__, __BIZ_CITY__</a></div>
      <div><b>Hours</b><span>Tuesday — Saturday · 11–7</span></div>
      <div><b>Hallmarking</b><span>BIS · KDM · per piece, per certificate</span></div>
    </div>
  </section>

</div>

<footer>
  © 2025 · <span class="accent">__BIZ_NAME__</span> · __BIZ_CITY__ · by appointment
</footer>

<script>
  (function(){
    const dot=document.querySelector('.cursor'),ring=document.querySelector('.cursor-ring');
    if(!dot||!ring)return;
    let mx=0,my=0,rx=0,ry=0;
    document.addEventListener('mousemove',e=>{mx=e.clientX;my=e.clientY;dot.style.left=mx+'px';dot.style.top=my+'px'});
    function loop(){rx+=(mx-rx)*.15;ry+=(my-ry)*.15;ring.style.left=rx+'px';ring.style.top=ry+'px';requestAnimationFrame(loop)}loop();
    document.querySelectorAll('a,button,.btn').forEach(el=>{
      el.addEventListener('mouseenter',()=>{dot.style.width='28px';dot.style.height='28px'});
      el.addEventListener('mouseleave',()=>{dot.style.width='14px';dot.style.height='14px'});
    });
  })();
</script>

</body>
</html>"""
