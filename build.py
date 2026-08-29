#!/usr/bin/env python3
"""Softgrove marketing site generator.

Content pipeline: App Store Connect live descriptions (_asc_descs.json, refreshed
via refresh_descs.py) + apps.json (palette/meta from each app's Theme.swift)
→ static HTML into docs/ (GitHub Pages root).

SEO/GEO decisions (playbook: reference-claude-code-lp-seo-playbook):
- plain fast HTML, inline CSS, one font request, no JS beyond nothing
- JSON-LD on every page (Organization / SoftwareApplication / FAQPage / HowTo)
- sitemap lastmod is per-page content-hash based (never "all pages updated")
- robots.txt explicitly allows AI crawlers (GPTBot, ClaudeBot, PerplexityBot...)
- llms.txt for answer engines; answer-first blocks on template pages
- OG images are PNG (SVG breaks X/Slack unfurls)
"""
import json, re, hashlib, datetime, pathlib, html as htmlmod

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "docs"
DATA = json.loads((ROOT / "apps.json").read_text())
DESCS = json.loads((ROOT / "_asc_descs.json").read_text())
SITE = DATA["site"]
ORIGIN = SITE["origin"]
TODAY = "2026-07-17"  # set per release; hash-gate keeps unchanged pages stable

# ---------------------------------------------------------------- desc parsing
def parse_desc(raw):
    """Extract hook / features / free / premium+prices / disclaimer from a live
    App Store description. Zero invention: everything shown on an LP comes from
    the store copy that already shipped."""
    lines = raw.splitlines()
    paras = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    hook = paras[0].replace("\n", " ")
    feats = []
    grab = False
    for ln in lines:
        s = ln.strip()
        if re.match(r"^WHAT YOU (CAN DO|TRACK)", s, re.I):
            grab = True; continue
        if grab:
            if s.startswith(("•", "-")):
                feats.append(re.sub(r"^[•\-]\s*", "", s))
            elif s and not s.startswith(("•", "-")):
                break
    if not feats:  # ReadLog-style prose sections: use bolded section leads
        for p in paras[1:6]:
            first = p.split("\n")[0].strip()
            if first and len(first) < 60 and not first.isupper():
                feats.append(first)
        feats = feats[:5]
    m = re.search(r"PREMIUM\s*—\s*7-DAY FREE TRIAL, THEN \$([\d.]+)/MONTH OR \$([\d.]+)/YEAR", raw, re.I)
    monthly, yearly = (m.group(1), m.group(2)) if m else (None, None)
    free_m = re.search(r"^FREE[^\n]*\n(.+?)(?:\n\s*\n|\Z)", raw, re.M | re.S | re.I)
    free = free_m.group(1).replace("\n", " ").strip() if free_m else ""
    disc = ""
    for p in reversed(paras):
        if "does not provide" in p or "not a medical device" in p or "is a personal" in p:
            disc = p.split("Terms of Use")[0].replace("\n", " ").strip(); break
    return dict(hook=hook, feats=feats, monthly=monthly, yearly=yearly, free=free, disc=disc)

PARSED = {k: parse_desc(v["desc"]) for k, v in DESCS.items()}

def esc(s): return htmlmod.escape(s, quote=True)

# ------------------------------------------------------------------ shared css
CSS = """
:root{--paper:%(paper)s;--ink:%(ink)s;--muted:%(muted)s;--line:%(hairline)s;--teal:%(house_accent)s}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-text-size-adjust:100%%}
body{background:var(--paper);color:var(--ink);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.serif{font-family:"Newsreader",Georgia,serif}
.mono{font-family:ui-monospace,"SF Mono",Menlo,monospace}
a{color:inherit}
:focus-visible{outline:2px solid var(--teal);outline-offset:3px;border-radius:2px}
.wrap{max-width:1060px;margin:0 auto;padding:0 24px}
header.mast{border-bottom:1px solid var(--line)}
.mast .wrap{display:flex;align-items:baseline;justify-content:space-between;padding-top:22px;padding-bottom:18px}
.wordmark{font-family:"Newsreader",Georgia,serif;font-weight:600;font-size:22px;text-decoration:none;letter-spacing:-.01em}
.wordmark b{color:var(--teal);font-weight:600}
nav.top a{font-size:14px;color:var(--muted);text-decoration:none;margin-left:22px}
nav.top a:hover{color:var(--ink)}
.eyebrow{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1,h2,h3{font-family:"Newsreader",Georgia,serif;font-weight:500;line-height:1.12;letter-spacing:-.015em}
.btn{display:inline-block;background:var(--ink);color:var(--paper);text-decoration:none;font-size:15px;font-weight:600;padding:13px 26px;border-radius:8px}
.btn:hover{opacity:.88}
.badge-store{display:inline-flex;align-items:center;gap:9px;background:#000;color:#fff;text-decoration:none;border-radius:9px;padding:9px 18px 9px 14px;line-height:1.15}
.badge-store svg{width:22px;height:26px;flex:none}
.badge-store small{display:block;font-size:10px;font-weight:400;opacity:.85}
.badge-store span{font-size:17px;font-weight:600;letter-spacing:.01em}
footer{border-top:1px solid var(--line);margin-top:96px}
footer .wrap{padding:34px 24px 46px;display:flex;flex-wrap:wrap;gap:10px 34px;font-size:13.5px;color:var(--muted)}
footer a{color:var(--muted);text-decoration:none}
footer a:hover{color:var(--ink)}
details{border-top:1px solid var(--line);padding:16px 2px}
details:last-of-type{border-bottom:1px solid var(--line)}
summary{cursor:pointer;font-weight:600;font-size:16.5px;list-style:none;display:flex;justify-content:space-between;gap:16px}
summary::after{content:"+";font-family:ui-monospace,monospace;color:var(--muted);font-size:18px}
details[open] summary::after{content:"–"}
details p{margin-top:10px;color:#4d4850;max-width:62ch}
@media(max-width:640px){.mast .wrap{padding-top:16px;padding-bottom:13px}}
""" % SITE

FONT_URL = "https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..600&display=swap"
FONT = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        f'<link href="{FONT_URL}" rel="stylesheet" media="print" onload="this.media=\'all\'">'
        f'<noscript><link href="{FONT_URL}" rel="stylesheet"></noscript>')

APPLE_SVG = '<svg viewBox="0 0 22 26" aria-hidden="true"><path fill="#fff" d="M18.1 13.8c0-3 2.5-4.5 2.6-4.6-1.4-2.1-3.6-2.4-4.4-2.4-1.9-.2-3.7 1.1-4.6 1.1-1 0-2.4-1.1-4-1-2 0-3.9 1.2-5 3-2.1 3.7-.5 9.1 1.5 12.1 1 1.5 2.2 3.1 3.8 3 1.5-.1 2.1-1 3.9-1s2.3 1 4 1c1.6 0 2.7-1.5 3.7-2.9 1.2-1.7 1.6-3.3 1.7-3.4-.1-.1-3.2-1.3-3.2-4.9zM15 4.9c.8-1 1.4-2.4 1.2-3.9-1.2.1-2.7.8-3.5 1.9-.8.9-1.5 2.4-1.3 3.8 1.4.1 2.8-.7 3.6-1.8z"/></svg>'

def store_badge(app_id, name):
    return (f'<a class="badge-store" href="https://apps.apple.com/app/id{app_id}" '
            f'aria-label="Download {esc(name)} on the App Store">{APPLE_SVG}'
            f'<span><small>Download on the</small>App Store</span></a>')

def page(title, desc, path, body, jsonld=None, extra_head=""):
    canon = ORIGIN + path
    is404 = path == "/404.html"
    og_slug = ("home" if is404 else path.strip("/").replace("/", "-")) or "home"
    robots_meta = '<meta name="robots" content="noindex">' if is404 else f'<link rel="canonical" href="{canon}">'
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">%s</script>' % json.dumps(jsonld, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots_meta}
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}">
<meta property="og:type" content="website">
<meta property="og:image" content="{ORIGIN}/og/{og_slug}.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{FONT}{extra_head}
<style>{CSS}</style>
{ld}
</head>
<body>
<header class="mast"><div class="wrap">
<a class="wordmark" href="/">softgrove<b>.</b></a>
<nav class="top"><a href="/#apps">Apps</a><a href="/templates/">Free templates</a></nav>
</div></header>
{body}
<footer><div class="wrap">
<span>© 2026 Softgrove — an independent app studio.</span>
<a href="https://apps.apple.com/developer/id6781130241">App Store developer page</a>
<a href="/llms.txt">llms.txt</a>
</div></footer>
</body></html>"""

# ----------------------------------------------------------------- house page
def spine(key):
    a = DATA["apps"][key]
    bg = a.get("spine_bg", a["accent"])
    tx = a.get("spine_text", "#FFFFFF" if key != "boardcut" else a["deep"])
    if key == "boardcut": bg = a["bg"]
    return (f'<a class="spine" href="/apps/{key}/" style="background:{bg};color:{tx}" '
            f'aria-label="{esc(a["name"])} — {esc(a["catLabel"])}">'
            f'<span class="s-band" style="background:{tx}"></span>'
            f'<span class="s-name serif">{esc(a["name"])}</span>'
            f'<span class="s-cat">{esc(a.get("spineLabel", a["catLabel"]))}</span></a>')

def house():
    shelves = ""
    for sh in DATA["shelves"]:
        spines = "".join(spine(k) for k in sh["apps"])
        shelves += (f'<section class="shelf-row"><p class="eyebrow">{esc(sh["label"])}</p>'
                    f'<p class="shelf-note">{esc(sh["note"])}</p>'
                    f'<div class="shelf">{spines}</div><div class="board"></div></section>')
    tpl_cards = ""
    for slug, t in DATA["templates"].items():
        ap = DATA["apps"][t["app"]]
        tpl_cards += (f'<a class="tpl-card" href="/templates/{slug}/">'
                      f'<span class="chip" style="background:{ap["accent"]}"></span>'
                      f'<strong class="serif">{esc(t["h1"])}</strong>'
                      f'<span>{esc(t["desc"].split(".")[0])}.</span></a>')
    body = f"""
<style>
.hero{{padding:88px 0 64px}}
.hero h1{{font-size:clamp(40px,6.4vw,68px);max-width:15ch}}
.hero h1 em{{font-style:italic;color:var(--teal)}}
.hero p.sub{{margin-top:22px;font-size:19px;color:#54505a;max-width:52ch}}
.hero p.answer{{margin-top:26px;border:1px solid var(--line);border-left:3px solid var(--teal);background:#fff;
 border-radius:0 10px 10px 0;padding:16px 20px;font-size:15px;color:#4d4850;max-width:66ch}}
.shelf-row{{margin-top:64px}}
.shelf-note{{margin:6px 0 20px;color:var(--muted);font-size:15px;max-width:60ch}}
.shelf{{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end}}
.spine{{writing-mode:vertical-rl;display:inline-flex;align-items:center;gap:9px;height:228px;min-width:60px;
 padding:16px 11px;border-radius:5px 9px 9px 5px;text-decoration:none;overflow:hidden;
 box-shadow:inset -3px 0 6px rgba(0,0,0,.18),inset 2px 0 3px rgba(255,255,255,.14),0 1px 2px rgba(0,0,0,.12)}}
.s-band{{width:100%;height:5px;border-radius:3px;opacity:.9;flex:none}}
.s-name{{font-size:20px;font-weight:600;letter-spacing:.01em}}
.s-cat{{font-size:10px;font-family:ui-monospace,monospace;letter-spacing:.09em;text-transform:uppercase;opacity:.95}}
.board{{height:10px;margin-top:14px;border-radius:2px;background:linear-gradient(#E4DED2,#D6CFBF);box-shadow:0 2px 3px rgba(0,0,0,.14)}}
@media(prefers-reduced-motion:no-preference){{
 .spine{{transition:transform .22s cubic-bezier(.2,.7,.3,1.2)}}
 .spine:hover{{transform:translateY(-7px)}}
}}
.tenets{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:26px;margin-top:34px}}
.tenets div{{border-top:2px solid var(--ink);padding-top:14px}}
.tenets strong{{font-family:"Newsreader",Georgia,serif;font-size:20px;font-weight:500;display:block;margin-bottom:6px}}
.tenets p{{font-size:15px;color:#4d4850}}
.tpls{{margin-top:96px}}
.tpl-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;margin-top:24px}}
.tpl-card{{border:1px solid var(--line);background:#fff;border-radius:10px;padding:22px;text-decoration:none;display:flex;flex-direction:column;gap:8px}}
.tpl-card:hover{{border-color:var(--ink)}}
.tpl-card .chip{{width:34px;height:8px;border-radius:4px}}
.tpl-card strong{{font-size:20px;font-weight:500;line-height:1.25}}
.tpl-card span:last-child{{font-size:14px;color:var(--muted)}}
.about{{margin-top:96px}}
h2.sec{{font-size:32px;margin-top:8px}}
@media(max-width:640px){{.spine{{height:176px;min-width:52px}}.s-cat{{display:none}}.s-name{{font-size:18px}}.hero{{padding:56px 0 30px}}}}
</style>
<main class="wrap">
<section class="hero">
<p class="eyebrow">An independent App Studio</p>
<h1>Quiet, private <em>logbooks</em> for the things you live with.</h1>
<p class="sub">{esc(SITE["sub"])} Each app does one job well: track it, show the pattern, and hand you a record worth bringing to whoever needs it.</p>
<p class="answer">Softgrove makes {len(DATA["apps"])} single-purpose tracker apps for iPhone — health journals (eczema, IBS, reflux, gout, neuropathy), life logs (pets, plants, cars, books, reef tanks), and workshop tools. Every app has a free core, needs no account, and keeps all data on the device.</p>
</section>
<section id="apps">{shelves}</section>
<section class="about">
<p class="eyebrow">How these are built</p>
<h2 class="sec">Three rules, every app.</h2>
<div class="tenets">
<div><strong>Private by design</strong><p>Everything you record stays on your device. No accounts, no cloud sync to us, no ads, no data sales — the privacy policy is one page because there's nothing to disclose.</p></div>
<div><strong>One job per app</strong><p>A tracker for your eczema shouldn't also be a social network. Each app covers a single subject completely and skips everything else.</p></div>
<div><strong>Free core, honest premium</strong><p>Logging and browsing your own history is always free — no account needed. Premium adds analysis and reports, with a clear price and a free trial.</p></div>
</div>
</section>
<section class="tpls">
<p class="eyebrow">Free printable templates</p>
<h2 class="sec">Prefer paper? Start there.</h2>
<div class="tpl-grid">{tpl_cards}</div>
</section>
</main>"""
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": ORIGIN + "/#org", "name": "Softgrove",
         "url": ORIGIN + "/", "logo": ORIGIN + "/logo.png",
         "description": "Independent app studio making private, single-purpose tracking apps for iPhone. All data stays on-device.",
         "sameAs": ["https://apps.apple.com/developer/id6781130241"]},
        {"@type": "WebSite", "name": "Softgrove", "url": ORIGIN + "/",
         "publisher": {"@id": ORIGIN + "/#org"}}]}
    return page("Softgrove — private, single-purpose tracker apps for iPhone",
                SITE["thesis"] + " " + SITE["sub"], "/", body, ld)

# ------------------------------------------------------------------- app LPs
def app_page(key):
    a = DATA["apps"][key]; d = DESCS[a["asc"]]; p = PARSED[a["asc"]]
    name, sub = a["name"], d["subtitle"]
    feats = "".join(f'<li><span class="fm" style="background:{a["accent"]}"></span>{esc(f)}</li>' for f in p["feats"])
    if pricing := a.get("pricing"):
        price_html = ('<div class="price"><div><strong>Free — no piece limit</strong>'
                      '<p>Plan any size project free: the optimizer, the cut diagram, the ordered cut steps, and sheet-image sharing. No account, no trial clock.</p></div>'
                      f'<div><strong>Pro — {esc(pricing["weekly"])} or {esc(pricing["lifetime"])} lifetime</strong>'
                      f'<p>{esc(pricing["trial"]).capitalize()} for eligible customers. Pro adds vector PDF and CSV export plus offcut stock. The weekly subscription renews automatically unless canceled.</p></div></div>')
        price_note = f'Free with no piece limit; Pro {pricing["weekly"]} or {pricing["lifetime"]} lifetime, with a {pricing["trial"]} for eligible customers'
    elif p["monthly"]:
        price_html = (f'<div class="price"><div><strong>Free</strong><p>{esc(p["free"])}</p></div>'
                      f'<div><strong>Premium — ${p["monthly"]}/mo or ${p["yearly"]}/yr</strong>'
                      f'<p>7-day free trial. Adds correlation insights and PDF reports. Cancel anytime from your Apple ID settings.</p></div></div>')
        price_note = f"Free core; Premium ${p['monthly']}/month or ${p['yearly']}/year after 7-day trial"
    else:
        price_html = f'<div class="price"><div><strong>Free</strong><p>{esc(p["free"])}</p></div></div>'
        price_note = "Free"
    faqs = [(f"Is {name} free?",
             (f"The core app is free, with no account needed. {p['free'].rstrip('.')}. Premium (${p['monthly']}/month or ${p['yearly']}/year after a 7-day trial) adds the analysis features." if p["monthly"] else
              f'Every project is free to plan, with no piece limit, no account, and no trial clock. Pro adds PDF and CSV export plus offcut stock. Choose {pricing["weekly"]} or a {pricing["lifetime"]} lifetime unlock; eligible customers receive a {pricing["trial"]}.' if pricing else "Yes.")),
            ("Where is my data stored?",
             f"On your iPhone, and nowhere else. {name} never uploads, syncs, shares, or sells your data — there is no account and no cloud backend."),
            (f"Does {name} require an account?",
             "No. You can start logging the moment the app opens — there is no sign-up, no email, and nothing to create.")]
    if a["category"] == "HealthApplication" and p["disc"]:
        faqs.append((f"Does {name} give medical advice?",
                     f"No. {p['disc']}"))
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(ans)}</p></details>" for q, ans in faqs)
    sibs = [k for sh in DATA["shelves"] for k in sh["apps"] if k != key][:20]
    same_shelf = next(sh["apps"] for sh in DATA["shelves"] if key in sh["apps"])
    picks = [k for k in same_shelf if k != key][:3] or sibs[:3]
    sib_html = "".join(
        f'<a class="sib" href="/apps/{k}/"><span class="chip" style="background:{DATA["apps"][k].get("spine_bg", DATA["apps"][k]["accent"])}"></span>'
        f'<strong>{esc(DATA["apps"][k]["name"])}</strong><span>{esc(DATA["apps"][k]["catLabel"])}</span></a>' for k in picks)
    tpl_html = ""
    if a.get("template"):
        t = DATA["templates"][a["template"]]
        tpl_html = (f'<p class="tpl-link">Prefer paper? <a href="/templates/{a["template"]}/">{esc(t["h1"])}</a> — '
                    f'the same log as a free printable sheet.</p>')
    body = f"""
<style>
.band{{background:{a["bg"]};border-bottom:1px solid var(--line)}}
.band .wrap{{padding:72px 24px 150px}}
.shots{{max-width:820px;margin:-110px auto 0;padding:0 24px;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}
.shots img{{width:100%;height:auto;border-radius:18px;border:1px solid rgba(0,0,0,.10);
 box-shadow:0 14px 34px rgba(0,0,0,.13);display:block;background:#fff}}
@media(max-width:640px){{.shots{{grid-template-columns:none;grid-auto-flow:column;grid-auto-columns:62%;
 overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:8px}}
.shots img{{scroll-snap-align:center}}.band .wrap{{padding-bottom:120px}}}}
.band h1{{font-size:clamp(44px,7vw,76px);color:{a["deep"]}}}
.band .sub{{font-size:21px;color:{a["deep"]};opacity:.82;margin-top:8px}}
.band .hook{{font-family:"Newsreader",Georgia,serif;font-style:italic;font-size:clamp(19px,2.6vw,24px);
 color:{a["deep"]};max-width:34ch;margin-top:26px;line-height:1.45}}
.band .cta{{margin-top:30px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}}
.band .eyebrow{{color:{a["deep"]};opacity:.85}}
main.wrap{{max-width:820px}}
h2.sec{{font-size:30px;margin:64px 0 20px}}
ul.feats{{list-style:none;display:grid;gap:14px}}
ul.feats li{{display:flex;gap:13px;align-items:baseline;font-size:16.5px;max-width:64ch}}
.fm{{width:9px;height:9px;border-radius:2px;flex:none;transform:translateY(-1px)}}
.price{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}}
.price>div{{border:1px solid var(--line);background:#fff;border-radius:10px;padding:20px}}
.price strong{{font-family:"Newsreader",Georgia,serif;font-size:20px;font-weight:500}}
.price p{{font-size:14.5px;color:#4d4850;margin-top:8px}}
.privacy{{border-left:3px solid {a["accent"]};background:#fff;border-radius:0 10px 10px 0;padding:20px 22px;font-size:15.5px;max-width:64ch}}
.sibs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}}
.sib{{border:1px solid var(--line);background:#fff;border-radius:10px;padding:16px;text-decoration:none;display:flex;flex-direction:column;gap:4px}}
.sib:hover{{border-color:var(--ink)}}
.sib .chip{{width:26px;height:7px;border-radius:4px;margin-bottom:6px}}
.sib span:last-child{{font-size:13px;color:var(--muted)}}
.tpl-link{{margin-top:26px;font-size:15.5px}}
.tpl-link a{{color:{a["accent"]};font-weight:600}}
</style>
<div class="band"><div class="wrap">
<p class="eyebrow">{esc(a["catLabel"])} · iPhone</p>
<h1 class="serif">{esc(name)}</h1>
<p class="sub">{esc(sub)}</p>
<p class="hook">{esc(p["hook"])}</p>
<div class="cta">{store_badge(a["id"], name)}</div>
</div></div>
<div class="shots">
<img src="/img/{key}/01.jpg" width="520" height="1130" alt="{esc(name)} for iPhone — home screen" fetchpriority="high">
<img src="/img/{key}/02.jpg" width="520" height="1130" alt="{esc(name)} for iPhone — logging" loading="lazy">
<img src="/img/{key}/03.jpg" width="520" height="1130" alt="{esc(name)} for iPhone — insights and reports" loading="lazy">
</div>
<main class="wrap">
<h2 class="sec serif">What you can track</h2>
<ul class="feats">{feats}</ul>
{tpl_html}
<h2 class="sec serif">Pricing, plainly</h2>
{price_html}
<h2 class="sec serif">Private by design</h2>
<div class="privacy">Everything you record stays only on your device. {esc(name)} never uploads, syncs, shares, or sells your data. No account needed — delete the app and the data is gone, because it was only ever yours.</div>
<h2 class="sec serif">Questions</h2>
{faq_html}
<h2 class="sec serif">From the same shelf</h2>
<div class="sibs">{sib_html}</div>
</main>"""
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "SoftwareApplication", "name": name,
         "operatingSystem": "iOS", "applicationCategory": a["category"],
         "description": p["hook"],
         "offers": {"@type": "Offer", "price": "12.99" if a.get("onetime") else "0",
                    "priceCurrency": "USD", "description": price_note},
         "url": f"{ORIGIN}/apps/{key}/",
         "installUrl": f"https://apps.apple.com/app/id{a['id']}",
         "author": {"@type": "Organization", "name": "Softgrove", "url": ORIGIN + "/"}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}}
            for q, ans in faqs]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Softgrove", "item": ORIGIN + "/"},
            {"@type": "ListItem", "position": 2, "name": name}]}]}
    head = f'<meta name="apple-itunes-app" content="app-id={a["id"]}">'
    return page(a["seoTitle"], a["seoDesc"], f"/apps/{key}/", body, ld, head)

# -------------------------------------------------------------- template pages
def tpl_preview_table(t, accent):
    heads = "".join(f'<th style="width:{w}%">{esc(c)}</th>'
                    for c, w in zip(t["columns"], t["col_widths"]))
    rows = "".join("<tr>" + "<td></td>" * len(t["columns"]) + "</tr>" for _ in range(4))
    return (f'<div class="prev" role="img" aria-label="Preview of the printable sheet">'
            f'<div class="prev-head" style="border-color:{accent}"><span class="serif">{esc(t["h1"].replace("Free Printable ", "").replace(" (PDF)", ""))}</span>'
            f'<span class="mono">softgrove.github.io</span></div>'
            f'<table><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table></div>')

def template_page(slug):
    t = DATA["templates"][slug]; a = DATA["apps"][t["app"]]; p = PARSED[a["asc"]]
    steps = "".join(f"<li>{esc(s)}</li>" for s in t["howto"])
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(ans)}</p></details>" for q, ans in t["faq"])
    pdf = f"/templates/{slug}/{slug}.pdf"
    body = f"""
<style>
main.wrap{{max-width:780px}}
.tp-hero{{padding:64px 0 8px}}
.tp-hero h1{{font-size:clamp(34px,5.4vw,52px);max-width:18ch}}
.answer{{border:1px solid var(--line);border-left:3px solid {a["accent"]};background:#fff;border-radius:0 10px 10px 0;
 padding:20px 24px;font-size:16.5px;margin-top:26px;max-width:66ch}}
.dl{{margin:28px 0 10px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}}
.dl .meta{{font-size:13.5px;color:var(--muted)}}
.prev{{border:1px solid var(--line);border-radius:10px;background:#fff;padding:22px;margin-top:40px;box-shadow:0 8px 24px rgba(0,0,0,.05)}}
.prev-head{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:2.5px solid;padding-bottom:10px;margin-bottom:2px}}
.prev-head .serif{{font-size:19px}}
.prev-head .mono{{font-size:10px;color:var(--muted);letter-spacing:.08em}}
.prev table{{width:100%;border-collapse:collapse;table-layout:fixed}}
.prev th{{font-family:ui-monospace,monospace;font-size:9.5px;text-transform:uppercase;letter-spacing:.06em;
 color:var(--muted);text-align:left;padding:9px 6px;border-bottom:1px solid var(--line);font-weight:500}}
.prev td{{height:30px;border-bottom:1px solid var(--line)}}
h2.sec{{font-size:29px;margin:60px 0 18px}}
ol.howto{{padding-left:22px;display:grid;gap:12px;font-size:16.5px;max-width:62ch}}
.app-cta{{margin-top:64px;background:{a["bg"]};border:1px solid var(--line);border-radius:14px;padding:30px;display:flex;flex-wrap:wrap;gap:20px;align-items:center;justify-content:space-between}}
.app-cta h3{{font-size:26px;color:{a["deep"]}}}
.app-cta p{{color:{a["deep"]};opacity:.8;font-size:15.5px;max-width:46ch;margin-top:6px}}
</style>
<main class="wrap">
<div class="tp-hero">
<p class="eyebrow">Free template · PDF · US Letter</p>
<h1 class="serif">{esc(t["h1"])}</h1>
<div class="answer">{esc(t["answer"])}</div>
<div class="dl"><a class="btn" href="{pdf}" download>Download the PDF — free</a>
<span class="meta">No sign-up. No email. Print and go.</span></div>
</div>
{tpl_preview_table(t, a["accent"])}
<h2 class="sec serif">How to use this sheet</h2>
<ol class="howto">{steps}</ol>
<h2 class="sec serif">Questions</h2>
{faq_html}
<div class="app-cta">
<div><h3 class="serif">Want the log to analyze itself?</h3>
<p>{esc(a["name"])} for iPhone tracks the same things in seconds and shows you the patterns — free core, no account, and everything stays on your device.</p></div>
{store_badge(a["id"], a["name"])}
</div>
</main>"""
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "HowTo", "name": t["h1"],
         "description": t["desc"],
         "step": [{"@type": "HowToStep", "name": n, "text": s}
                  for n, s in zip(t["howto_names"], t["howto"])]},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}}
            for q, ans in t["faq"]]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Softgrove", "item": ORIGIN + "/"},
            {"@type": "ListItem", "position": 2, "name": "Free templates", "item": ORIGIN + "/templates/"},
            {"@type": "ListItem", "position": 3, "name": t["h1"]}]}]}
    head = f'<meta name="apple-itunes-app" content="app-id={a["id"]}">'
    return page(t["title"], t["desc"], f"/templates/{slug}/", body, ld, head)

def templates_hub():
    cards = ""
    for slug, t in DATA["templates"].items():
        ap = DATA["apps"][t["app"]]
        cards += (f'<a class="tpl-card" href="/templates/{slug}/">'
                  f'<span class="chip" style="background:{ap["accent"]}"></span>'
                  f'<strong class="serif">{esc(t["h1"])}</strong>'
                  f'<span>{esc(t["desc"])}</span></a>')
    body = f"""
<style>
main.wrap{{max-width:900px}}
.tp-hero{{padding:64px 0 12px}}
.tp-hero h1{{font-size:clamp(36px,5.6vw,54px)}}
.tp-hero p{{margin-top:16px;color:#54505a;max-width:56ch;font-size:17px}}
.tpl-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px;margin-top:38px}}
.tpl-card{{border:1px solid var(--line);background:#fff;border-radius:10px;padding:24px;text-decoration:none;display:flex;flex-direction:column;gap:9px}}
.tpl-card:hover{{border-color:var(--ink)}}
.tpl-card .chip{{width:34px;height:8px;border-radius:4px}}
.tpl-card strong{{font-size:21px;font-weight:500;line-height:1.25}}
.tpl-card span:last-child{{font-size:14px;color:var(--muted)}}
</style>
<main class="wrap">
<div class="tp-hero">
<p class="eyebrow">Free printables</p>
<h1 class="serif">Tracker templates, free to print.</h1>
<p>One-page PDF log sheets — the paper versions of our apps. No sign-up, no email, no watermark nagging you to upgrade. If a sheet earns a place on your fridge, the matching app does the same job with the analysis built in.</p>
</div>
<div class="tpl-grid">{cards}</div>
</main>"""
    ld = {"@context": "https://schema.org", "@type": "CollectionPage",
          "name": "Free printable tracker templates",
          "url": ORIGIN + "/templates/",
          "publisher": {"@type": "Organization", "name": "Softgrove", "url": ORIGIN + "/"}}
    return page("Free Printable Tracker Templates (PDF) | Softgrove",
                "Free one-page printable tracker PDFs: eczema flare log, car maintenance record, gout food diary. No sign-up — print and go.",
                "/templates/", body, ld)

# ------------------------------------------------------------------ site files
def not_found():
    body = """<main class="wrap" style="padding:96px 24px;max-width:640px">
<p class="eyebrow">404</p>
<h1 class="serif" style="font-size:44px;margin-top:8px">That page isn't on the shelf.</h1>
<p style="margin-top:16px;color:#54505a">The address may have changed. Everything we make is one click away:</p>
<p style="margin-top:22px"><a class="btn" href="/">Back to Softgrove</a></p></main>"""
    return page("Page not found | Softgrove", "Page not found.", "/404.html", body)

def robots():
    bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-Web",
            "anthropic-ai", "PerplexityBot", "Google-Extended", "Applebot-Extended",
            "CCBot", "Bytespider", "meta-externalagent"]
    lines = ["# Softgrove — AI crawlers are welcome; cite us.", "User-agent: *", "Allow: /", ""]
    for b in bots:
        lines += [f"User-agent: {b}", "Allow: /", ""]
    lines.append(f"Sitemap: {ORIGIN}/sitemap.xml")
    return "\n".join(lines) + "\n"

def llms_txt(paths):
    lines = ["# Softgrove", "",
             "> Independent app studio making private, single-purpose tracking apps for iPhone.",
             "> Every app: free core, no account, no ads; all data stays on the user's device",
             "> (no cloud backend). Premium tiers add analysis and PDF reports.", "",
             "## Apps"]
    for sh in DATA["shelves"]:
        for k in sh["apps"]:
            a = DATA["apps"][k]; p = PARSED[a["asc"]]; d = DESCS[a["asc"]]
            pricing = a.get("pricing")
            price = f'free with no piece limit; Pro {pricing["weekly"]} or {pricing["lifetime"]} lifetime, with a {pricing["trial"]} for eligible customers' if pricing else (
                f"free core; Premium ${p['monthly']}/mo or ${p['yearly']}/yr" if p["monthly"] else "free")
            lines.append(f"- [{a['name']}]({ORIGIN}/apps/{k}/): {d['subtitle']} — {a['catLabel']}; {price}. App Store id{a['id']}.")
    lines += ["", "## Free printable templates (PDF, no sign-up)"]
    for slug, t in DATA["templates"].items():
        lines.append(f"- [{t['h1']}]({ORIGIN}/templates/{slug}/): {t['desc']}")
    lines += ["", "## Facts",
              "- All apps are iPhone (iOS). Data is stored on-device only; no account exists.",
              "- Health apps are journaling tools, not medical devices; they do not give medical advice.",
              f"- Developer page: https://apps.apple.com/developer/id6781130241"]
    return "\n".join(lines) + "\n"

def sitemap(paths):
    hashes_file = ROOT / "page_hashes.json"
    old = json.loads(hashes_file.read_text()) if hashes_file.exists() else {}
    new = {}
    entries = []
    for path, content in paths.items():
        h = hashlib.sha256(content.encode()).hexdigest()[:16]
        prev = old.get(path, {})
        lastmod = prev.get("lastmod", TODAY) if prev.get("hash") == h else TODAY
        new[path] = {"hash": h, "lastmod": lastmod}
        entries.append(f"<url><loc>{ORIGIN}{path}</loc><lastmod>{lastmod}</lastmod></url>")
    hashes_file.write_text(json.dumps(new, indent=1))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(entries) + "\n</urlset>\n")

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
<rect width="64" height="64" rx="14" fill="#FBFAF7"/>
<rect x="14" y="12" width="10" height="40" rx="2" fill="#3E8E8C"/>
<rect x="27" y="16" width="10" height="36" rx="2" fill="#7A2E33"/>
<rect x="40" y="10" width="10" height="42" rx="2" fill="#E87722"/>
</svg>"""

# --------------------------------------------------------------------- build
def main():
    OUT.mkdir(exist_ok=True)
    pages = {"/": house(), "/templates/": templates_hub(), "/404.html": not_found()}
    for key in DATA["apps"]:
        pages[f"/apps/{key}/"] = app_page(key)
    for slug in DATA["templates"]:
        pages[f"/templates/{slug}/"] = template_page(slug)
    for path, content in pages.items():
        f = OUT / path.lstrip("/")
        if path.endswith("/"): f = f / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
    (OUT / "robots.txt").write_text(robots())
    (OUT / "llms.txt").write_text(llms_txt(pages))
    (OUT / "sitemap.xml").write_text(sitemap({p: c for p, c in pages.items() if p != "/404.html"}))
    (OUT / "favicon.svg").write_text(FAVICON)
    (OUT / ".nojekyll").write_text("")
    # IndexNow key file (L4) — must be live at https://softgrove.github.io/<key>.txt
    (OUT / "8a4b2c6d9e1f3a5b7c8d2e4f6a0b1c3d.txt").write_text("8a4b2c6d9e1f3a5b7c8d2e4f6a0b1c3d")
    print(f"built {len(pages)} pages -> {OUT}")

if __name__ == "__main__":
    main()
