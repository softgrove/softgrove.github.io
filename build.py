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
TODAY = "2026-09-12"  # set per release; hash-gate keeps unchanged pages stable

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
    if not feats:  # Whetlog-style ALL-CAPS section heads: take the store bullets directly
        feats = [re.sub(r"^[•\-]\s*", "", ln.strip()) for ln in lines
                 if ln.strip().startswith(("•", "-"))][:6]
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

def page(title, desc, path, body, jsonld=None, extra_head="", og_image=None):
    canon = ORIGIN + path
    is404 = path == "/404.html"
    og_slug = ("home" if is404 else path.strip("/").replace("/", "-")) or "home"
    robots_meta = '<meta name="robots" content="noindex">' if is404 else f'<link rel="canonical" href="{canon}">'
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">%s</script>' % json.dumps(jsonld, ensure_ascii=False)
    og_image_url = ORIGIN + (og_image or f"/og/{og_slug}.png")
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
<meta property="og:image" content="{og_image_url}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{FONT}{extra_head}
<style>{CSS}</style>
{ld}
</head>
<body>
<header class="mast"><div class="wrap">
<a class="wordmark" href="/">softgrove<b>.</b></a>
<nav class="top"><a href="/#apps">Apps</a><a href="/tools/reciprocity-calculator/">Free tools</a><a href="/templates/">Free templates</a></nav>
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
        # skip apps whose ASC description isn't loaded yet (no /apps/<key>/ page is built for them)
        spines = "".join(spine(k) for k in sh["apps"] if DATA["apps"][k]["asc"] in DESCS)
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
    pricing = a.get("pricing")
    if pricing and "weekly" in pricing:
        price_html = ('<div class="price"><div><strong>Free — no piece limit</strong>'
                      '<p>Plan any size project free: the optimizer, the cut diagram, the ordered cut steps, and sheet-image sharing. No account, no trial clock.</p></div>'
                      f'<div><strong>Pro — {esc(pricing["weekly"])} or {esc(pricing["lifetime"])} lifetime</strong>'
                      f'<p>{esc(pricing["trial"]).capitalize()} for eligible customers. Pro adds vector PDF and CSV export plus offcut stock. The weekly subscription renews automatically unless canceled.</p></div></div>')
        price_note = f'Free with no piece limit; Pro {pricing["weekly"]} or {pricing["lifetime"]} lifetime, with a {pricing["trial"]} for eligible customers'
    elif pricing:  # one-time lifetime unlock only (Whetlog)
        price_html = ('<div class="price"><div><strong>Free — the whole logbook</strong>'
                      '<p>Catalog unlimited stones and blades and log unlimited sharpening sessions. No account, no trial clock.</p></div>'
                      f'<div><strong>Lifetime — {esc(pricing["lifetime"])}, once</strong>'
                      '<p>One purchase unlocks Blade Card sharing and CSV export, forever. No subscription and no renewal.</p></div></div>')
        price_note = f'Free core; a one-time {pricing["lifetime"]} Lifetime unlock adds Blade Card sharing and CSV export'
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
              f'Every project is free to plan, with no piece limit, no account, and no trial clock. Pro adds PDF and CSV export plus offcut stock. Choose {pricing["weekly"]} or a {pricing["lifetime"]} lifetime unlock; eligible customers receive a {pricing["trial"]}.' if pricing and "weekly" in pricing else
              f'Cataloging stones and blades and logging sessions are free, with no account and no trial clock. A one-time {pricing["lifetime"]} Lifetime unlock adds Blade Card sharing and CSV export — there is no subscription and no renewal.' if pricing else "Yes.")),
            ("Where is my data stored?",
             f"On your iPhone. {name} never uploads what you record, and never shares or sells your data — there is no account and no cloud backend. Some apps send anonymous usage counts (no identifiers) so we can see which features get used; each app's privacy policy spells out exactly what, if anything, is sent."),
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
    guide_cards = "".join(
        f'<a class="guide-card" href="/guides/{slug}/"><span class="eyebrow">{esc(g["keyword"])}</span>'
        f'<strong class="serif">{esc(g["h1"])}</strong><span>{esc(g["desc"])}</span></a>'
        for slug, g in DATA.get("guides", {}).items() if g["app"] == key)
    guide_html = (f'<h2 class="sec serif">{esc(a.get("guidesLabel", "Practical cutting guides"))}</h2><div class="guide-grid">{guide_cards}</div>'
                  if guide_cards else "")
    guide_css = (f'''
.guide-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}}
.guide-card{{border:1px solid var(--line);background:#fff;border-radius:10px;padding:19px;text-decoration:none;display:flex;flex-direction:column;gap:7px}}
.guide-card:hover{{border-color:{a["accent"]}}}
.guide-card strong{{font-size:20px;font-weight:500;line-height:1.22}}
.guide-card>span:last-child{{font-size:14px;color:var(--muted)}}
''' if guide_cards else "")
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
{guide_css}</style>
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
<div class="privacy">Everything you record stays on your device. {esc(name)} never uploads what you record, and never shares or sells your data. No account needed — delete the app and your entries are gone. Anything the app does send (some apps report anonymous usage counts, with no identifiers) is listed plainly in its privacy policy.</div>
<h2 class="sec serif">Questions</h2>
{faq_html}
{guide_html}<h2 class="sec serif">From the same shelf</h2>
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

# --------------------------------------------------------------- guide pages
GUIDE_CTA = {
    "boardcut": ("When the layout stops being simple",
                 "Boardcut for iPhone turns a parts list and your available stock into a dimensioned cutting diagram. Planning has no piece limit and includes kerf, grain direction, yield, sheet count, and ordered cut steps."),
    "whetlog": ("When you stop remembering what worked",
                "Whetlog for iPhone keeps your whetstones, blades, and sharpening sessions in one private logbook. Catalog stones by grit, log each session's progression in order, and check what worked last time before you sharpen. No account — everything stays on your device."),
    "kilncost": ("When you need the number before loading the kiln",
                 "KilnCost for iPhone estimates firing cost from your kiln, schedule, and electricity rate. Choose a listed kiln or enter your own, then compare flat and time-of-use rates before you fire."),
}

def guide_page(slug):
    g = DATA["guides"][slug]; a = DATA["apps"][g["app"]]
    pricing = a["pricing"]
    sections = []
    for section in g["sections"]:
        paragraphs = "".join(f"<p>{esc(p)}</p>" for p in section.get("body", []))
        bullets = ("<ul>" + "".join(f"<li>{esc(item)}</li>" for item in section["bullets"]) + "</ul>"
                   if section.get("bullets") else "")
        note = f'<div class="work-note"><strong>{esc(section["note_title"])}</strong><p>{esc(section["note"])}</p></div>' if section.get("note") else ""
        sections.append(f'<section><h2 class="serif">{esc(section["h2"])}</h2>{paragraphs}{bullets}{note}</section>')
    section_html = "".join(sections)
    faq_html = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(ans)}</p></details>" for q, ans in g["faq"])
    related = "".join(
        f'<a href="/guides/{other_slug}/"><strong class="serif">{esc(other["h1"])}</strong><span>{esc(other["keyword"])}</span></a>'
        for other_slug, other in DATA["guides"].items() if other_slug != slug and other["app"] == g["app"])
    source = g.get("source")
    field_note = (f'''<aside class="field-note">
<p class="eyebrow">Why this guide exists</p>
<p>A woodworker described the problem this way: <q>{esc(source["quote"])}</q></p>
<p><cite>Source: <a href="{esc(source["url"])}">{esc(source["title"])}</a> on {esc(source["community"])}</cite>. The quote is evidence of the workflow problem, not an endorsement of {esc(a["name"])}.</p>
</aside>''' if source else "")
    cta_h2, cta_body = GUIDE_CTA[g["app"]]
    if "weekly" in pricing:
        cta_terms = (f'Planning is free. Pro adds vector PDF and CSV export plus saved offcuts: {esc(pricing["weekly"])} or '
                     f'{esc(pricing["lifetime"])} lifetime. Eligible customers receive a {esc(pricing["trial"])}; the weekly subscription renews automatically unless canceled.')
    elif g["app"] == "whetlog":
        cta_terms = (f'The logbook is free. A one-time {esc(pricing["lifetime"])} Lifetime unlock adds Blade Card sharing '
                     'and CSV export — no subscription, no renewal.')
    else:
        cta_terms = (f'The calculator is free. A one-time {esc(pricing["lifetime"])} Pro Lifetime unlock adds cost-card sharing, '
                     'saved presets, and CSV export — no subscription, no renewal.')
    body = f"""
<style>
article.wrap{{width:100%;max-width:780px}}
.guide-hero{{padding:64px 0 20px}}
.guide-hero h1{{font-size:clamp(36px,5.8vw,56px);max-width:18ch}}
.guide-hero .lede{{font-size:19px;color:#4d4850;margin-top:20px;max-width:62ch}}
.answer{{border:1px solid var(--line);border-left:3px solid {a["accent"]};background:#fff;border-radius:0 10px 10px 0;padding:20px 24px;font-size:16.5px;margin-top:28px}}
article section{{margin-top:56px}}
article section h2{{font-size:30px;margin-bottom:18px}}
article section p{{margin-top:14px;max-width:66ch}}
article section ul{{padding-left:22px;margin-top:16px;display:grid;gap:10px;max-width:64ch}}
.work-note{{background:{a["bg"]};border:1px solid var(--line);border-radius:10px;padding:20px 22px;margin-top:22px}}
.work-note strong{{font-size:15px}}
.work-note p{{margin-top:7px;font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:14px;line-height:1.55}}
.field-note{{margin-top:56px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:22px 0}}
.field-note p{{margin-top:8px;color:#4d4850}}
.field-note cite{{font-style:normal}}
.field-note a{{color:{a["accent"]};font-weight:600}}
.app-cta{{margin-top:60px;background:{a["bg"]};border:1px solid var(--line);border-radius:14px;padding:28px}}
.app-cta h2{{font-size:28px}}
.app-cta p{{margin-top:10px;max-width:62ch;color:#4d4850}}
.app-cta .cta-row{{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-top:20px}}
.app-cta .terms{{font-size:13px;color:var(--muted);max-width:44ch}}
.related{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-top:18px}}
.related a{{border:1px solid var(--line);background:#fff;border-radius:9px;padding:16px;text-decoration:none;display:flex;flex-direction:column;gap:6px}}
.related a:hover{{border-color:{a["accent"]}}}
.related strong{{font-size:18px;line-height:1.2}}
.related span{{font-size:12px;color:var(--muted)}}
</style>
<article class="wrap">
<header class="guide-hero">
<p class="eyebrow">Workshop guide · {esc(g["keyword"])}</p>
<h1 class="serif">{esc(g["h1"])}</h1>
<p class="lede">{esc(g["lede"])}</p>
<div class="answer">{esc(g["answer"])}</div>
</header>
{section_html}
{field_note}
<section><h2 class="serif">Questions</h2>{faq_html}</section>
<aside class="app-cta">
<h2 class="serif">{esc(cta_h2)}</h2>
<p>{esc(cta_body)}</p>
<div class="cta-row">{store_badge(a["id"], a["name"])}<p class="terms">{cta_terms}</p></div>
</aside>
<section><h2 class="serif">{esc(a.get("guidesRelatedLabel", "Related cutting guides"))}</h2><div class="related">{related}</div></section>
</article>"""
    faqs = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}}
            for q, ans in g["faq"]]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": g["h1"], "description": g["desc"],
         "mainEntityOfPage": ORIGIN + f"/guides/{slug}/",
         "author": {"@type": "Organization", "name": "Softgrove", "url": ORIGIN + "/"},
         "publisher": {"@type": "Organization", "name": "Softgrove", "url": ORIGIN + "/"}},
        {"@type": "FAQPage", "mainEntity": faqs},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Softgrove", "item": ORIGIN + "/"},
            {"@type": "ListItem", "position": 2, "name": a["name"], "item": ORIGIN + f"/apps/{g['app']}/"},
            {"@type": "ListItem", "position": 3, "name": g["h1"]}]}]}
    head = f'<meta name="apple-itunes-app" content="app-id={a["id"]}">'
    return page(g["title"], g["desc"], f"/guides/{slug}/", body, ld, head,
                og_image=f"/og/apps-{g['app']}.png")

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

# --------------------------------------------------------------- free tools
def tool_shell(app_key, eyebrow, h1, lede, calculator, below):
    a = DATA["apps"][app_key]
    return f"""
<style>
.tool-hero{{padding:64px 0 30px;max-width:820px}}
.tool-hero h1{{font-size:clamp(38px,6vw,60px);max-width:18ch;margin-top:8px}}
.tool-hero .lede{{font-size:19px;color:#4d4850;margin-top:18px;max-width:64ch}}
.calculator{{max-width:820px;background:#fff;border:1px solid var(--line);border-top:5px solid {a["accent"]};border-radius:14px;padding:clamp(18px,4vw,34px);box-shadow:0 10px 30px rgba(44,40,44,.06)}}
.fields{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}
.field{{display:flex;flex-direction:column;gap:6px;min-width:0}}
.field.wide{{grid-column:1/-1}}
label,.label{{font-weight:600;font-size:14px}}
input,select,button{{font:inherit}}
input,select{{width:100%;min-height:46px;border:1px solid #b9b2a6;border-radius:8px;background:#fff;color:var(--ink);padding:9px 11px}}
button{{border:0;border-radius:8px;background:var(--ink);color:var(--paper);font-weight:600;padding:12px 19px;cursor:pointer}}
button.secondary{{background:#fff;color:var(--ink);border:1px solid var(--line)}}
button.danger{{background:transparent;color:#7a2e33;padding:8px}}
.actions{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:20px}}
.hint,.fine{{font-size:13px;color:var(--muted)}}
.result{{margin-top:24px;background:{a["bg"]};border-radius:10px;padding:20px}}
.result strong.big{{display:block;font-family:"Newsreader",Georgia,serif;font-size:clamp(30px,6vw,44px);font-weight:500;line-height:1.1;color:{a["deep"]}}}
.result dl{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:16px}}
.result dt{{font-size:12px;color:var(--muted)}}.result dd{{font-weight:600}}
.error{{color:#9b2c2c;font-size:14px;margin-top:12px;min-height:1.5em}}
.rows{{display:grid;gap:10px;margin-top:10px}}
.entry-row{{display:grid;grid-template-columns:2fr 2fr 1fr auto;gap:8px;align-items:end}}
.tool-copy{{max-width:780px;margin-top:62px}}.tool-copy section{{margin-top:46px}}
.tool-copy h2{{font-size:30px;margin-bottom:14px}}.tool-copy p{{margin-top:12px;max-width:66ch}}
.sources{{padding-left:20px;display:grid;gap:9px;margin-top:14px;font-size:14px}}
.app-cta{{margin-top:56px;background:{a["bg"]};border:1px solid var(--line);border-radius:14px;padding:28px}}
.app-cta h2{{font-size:28px}}.app-cta p{{margin:10px 0 20px;max-width:62ch;color:#4d4850}}
.sheet-output{{display:grid;gap:20px;margin-top:18px}}
.sheet-output figure{{margin:0}}.sheet-output figcaption{{font-size:13px;color:var(--muted);margin-bottom:7px}}
.sheet-output svg{{display:block;width:100%;height:auto;max-height:520px;background:#f8f5ef;border:1px solid var(--line)}}
@media(max-width:640px){{.tool-hero{{padding-top:46px}}.fields,.result dl{{grid-template-columns:1fr}}.entry-row{{grid-template-columns:1fr 1fr auto}}.entry-row .row-name{{grid-column:1/-1}}nav.top a{{margin-left:12px;font-size:12px}}}}
</style>
<main class="wrap">
<header class="tool-hero"><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(h1)}</h1><p class="lede">{esc(lede)}</p></header>
<section class="calculator" aria-label="{esc(h1)}">{calculator}</section>
<article class="tool-copy">{below}
<aside class="app-cta"><h2>Keep it with you</h2><p>Use {esc(a["name"])} on iPhone when you need the full tool away from your desk.</p>{store_badge(a["id"], a["name"])}</aside>
</article></main>"""

def reciprocity_tool():
    a = DATA["apps"]["filmrecip"]
    calculator = r'''
<div class="fields">
<div class="field"><label for="film-stock">Film</label><select id="film-stock"></select></div>
<div class="field"><label for="metered-time">Metered time in seconds</label><input id="metered-time" type="number" min="0.1" max="86400" step="0.1" value="10" inputmode="decimal"></div>
</div>
<div class="actions"><button id="recip-calc" type="button">Calculate exposure</button><span class="hint">Up to 24 hours metered time</span></div>
<p id="recip-error" class="error" role="alert"></p>
<div id="recip-result" class="result" aria-live="polite">
<span class="eyebrow">Corrected exposure</span><strong class="big" id="corrected-time">20.4s</strong>
<dl><div><dt>Time to add</dt><dd id="added-time">10.4s</dd></div><div><dt>Compensation</dt><dd id="stops">+1.0 stops</dd></div><div><dt>Data</dt><dd id="confidence">Official datasheet</dd></div></dl>
<p class="fine" id="film-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const sources={
 ilford:{label:"Official datasheet",url:"https://www.ilfordphoto.com/wp/wp-content/uploads/2024/05/Reciprocity-Failure-Compensation-v2.pdf"},
 tmax100:{label:"Official datasheet",url:"https://www.kodakprofessional.com/sites/default/files/wysiwyg/pro/resources/f4016_TMax_100.pdf"},
 tmax400:{label:"Official datasheet",url:"https://cdn.shopify.com/s/files/1/0339/5113/files/f4043_tmax_400.pdf?v=1621654948"},
 trix:{label:"Official datasheet",url:"https://kodakprofessional.com/sites/default/files/wysiwyg/film/f4017_trix_320400.pdf"},
 portra400:{label:"Estimate beyond 1s",url:"https://kodakprofessional.com/sites/default/files/2025-07/e4050.pdf"},
 acros:{label:"Official datasheet",url:"https://asset.fujifilm.com/www/ca/files/2020-07/fb477bd9803b3c27ab592edcf9f3567c/AF3-0258E_PIB-NEOPAN-100-ACROSII-135-3_data-sheet.pdf"},
 foma100:{label:"Official datasheet",url:"https://www.foma.cz/en/fomapan-100"},
 foma200:{label:"Official datasheet",url:"https://www.foma.cz/en/fomapan-200"},
 foma400:{label:"Official datasheet",url:"https://www.foma.cz/en/fomapan-400"},
 cinestill:{label:"Manufacturer guide",url:"https://help.cinestillfilm.com/hc/en-us/articles/4407453578893-What-are-the-reciprocity-failure-details-for-CineStill-films"}
};
const films=[
 ["Ilford HP5 Plus · ISO 400",1,"power",1.31,null,"ilford",""] ,
 ["Ilford FP4 Plus · ISO 125",1,"power",1.26,null,"ilford",""] ,
 ["Ilford Pan F Plus · ISO 50",1,"power",1.33,null,"ilford",""] ,
 ["Ilford Delta 100 · ISO 100",1,"power",1.26,null,"ilford",""] ,
 ["Ilford Delta 400 · ISO 400",1,"power",1.41,null,"ilford",""] ,
 ["Ilford Delta 3200 · ISO 3200",1,"power",1.33,null,"ilford",""] ,
 ["Ilford SFX 200 · ISO 200",1,"power",1.43,null,"ilford",""] ,
 ["Ilford XP2 Super · ISO 400",1,"power",1.31,null,"ilford",""] ,
 ["Kodak T-Max 100 · ISO 100",0.1,"table",null,[[1,1.26],[10,15],[100,200]],"tmax100",""] ,
 ["Kodak T-Max 400 · ISO 400",1,"table",null,[[10,12.6],[100,300]],"tmax400",""] ,
 ["Kodak Tri-X 400 · ISO 400",0.1,"table",null,[[1,2],[10,50],[100,1200]],"trix","Kodak also advises development cuts: −10% at 1s, −20% at 10s, and −30% at 100s."],
 ["Kodak Portra 400 · ISO 400",1,"estimate",1.3,null,"portra400","Kodak publishes no correction table beyond 1s. Longer results use the app's labeled community estimate, t^1.3."],
 ["Fujifilm Neopan 100 Acros II",119.9,"table",null,[[120,169.7],[1000,1414.2]],"acros",""] ,
 ["Foma Fomapan 100 Classic",0.5,"table",null,[[1,2],[10,80],[100,1600]],"foma100",""] ,
 ["Foma Fomapan 200 Creative",0.5,"table",null,[[1,3],[10,90],[100,1800]],"foma200",""] ,
 ["Foma Fomapan 400 Action",0.5,"table",null,[[1,1.5],[10,60],[100,800]],"foma400",""] ,
 ["CineStill 800T · ISO 800",1,"power",1.3,null,"cinestill","CineStill recommends bracketing a couple of stops on long exposures."]
];
const select=document.querySelector("#film-stock");
films.forEach((f,i)=>{const o=document.createElement("option");o.value=String(i);o.textContent=f[0];select.append(o)});
function interp(a,b,t){const p=(Math.log(t)-Math.log(a[0]))/(Math.log(b[0])-Math.log(a[0]));return Math.exp(Math.log(a[1])+p*(Math.log(b[1])-Math.log(a[1])))}
function compute(f,t){if(t<=f[1])return t;if(f[2]==="power"||f[2]==="estimate")return Math.pow(t,f[3]);const p=f[4];if(t>=p[p.length-1][0])return p.length===1?t*(p[0][1]/p[0][0]):interp(p[p.length-2],p[p.length-1],t);if(t<=p[0][0])return interp([f[1],f[1]],p[0],t);for(let i=1;i<p.length;i++)if(t<=p[i][0])return interp(p[i-1],p[i],t);return t}
function fmt(s){if(s<60){const n=Math.round(s*10)/10;return `${Number.isInteger(n)?n:n.toFixed(1)}s`}const n=Math.round(s);if(n<3600)return `${Math.floor(n/60)}m ${n%60}s`;return `${Math.floor(n/3600)}h ${Math.floor((n%3600)/60)}m`}
function run(){const t=Number(document.querySelector("#metered-time").value),f=films[Number(select.value)],err=document.querySelector("#recip-error");if(!Number.isFinite(t)||t<=0||t>86400){err.textContent="Enter a metered time from 0.1 seconds to 24 hours.";return}err.textContent="";const corrected=compute(f,t),src=sources[f[5]];document.querySelector("#corrected-time").textContent=fmt(corrected);document.querySelector("#added-time").textContent=fmt(Math.max(0,corrected-t));document.querySelector("#stops").textContent=`+${Math.log2(corrected/t).toFixed(1)} stops`;document.querySelector("#confidence").textContent=t<=f[1]&&f[2]!=="estimate"?src.label:(f[2]==="estimate"?"Community estimate":(f[2]==="table"&&t>f[4][f[4].length-1][0]?"Extrapolated":"Official datasheet"));const note=f[6]?`${f[6]} `:"";document.querySelector("#film-note").textContent=`${note}Source: ${src.url}`}
document.querySelector("#recip-calc").addEventListener("click",run);select.addEventListener("change",run);document.querySelector("#metered-time").addEventListener("input",run);run();
})();
</script>'''
    below = '''
<section><h2>How reciprocity correction works</h2><p>Film becomes less efficient during long exposures. Enter the time from your light meter, then use the corrected time as the total shutter time. This calculator uses seconds internally, including for exposures longer than a minute.</p><p>Ilford and CineStill models use <span class="mono">corrected = metered<sup>p</sup></span>. Published point tables from Kodak, Fujifilm, and Foma use the same log-log interpolation as FilmRecip. Results past the last published point are labeled as extrapolated.</p></section>
<section><h2>Sources</h2><p>Coefficients, tables, thresholds, and the 1.3 fallback were copied from FilmRecip's data definitions on September 2, 2026.</p><ul class="sources"><li><a href="https://www.ilfordphoto.com/wp/wp-content/uploads/2024/05/Reciprocity-Failure-Compensation-v2.pdf">Ilford Film Reciprocity Failure Compensation</a></li><li><a href="https://kodakprofessional.com/sites/default/files/wysiwyg/film/f4017_trix_320400.pdf">Kodak F-4017: Tri-X 320 and 400</a></li><li><a href="https://www.kodakprofessional.com/sites/default/files/wysiwyg/pro/resources/f4016_TMax_100.pdf">Kodak F-4016: T-Max 100</a></li><li><a href="https://www.foma.cz/en/fomapan-100">Foma: Fomapan 100 data</a></li></ul></section>
<section><h2>Questions</h2><details><summary>What is the HP5 reciprocity formula?</summary><p>Ilford's published formula is corrected time = metered seconds raised to 1.31. A metered 10-second exposure becomes 20.4 seconds.</p></details><details><summary>Does Portra 400 have an official long-exposure table?</summary><p>No. Kodak says no correction is needed through one second and recommends testing for longer exposures. FilmRecip labels its longer result as a community estimate.</p></details>'''
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebApplication", "name": "Film Reciprocity Failure Calculator", "applicationCategory": "PhotographyApplication", "operatingSystem": "Any", "url": ORIGIN + "/tools/reciprocity-calculator/", "isAccessibleForFree": True, "description": "Calculate reciprocity-corrected long exposures for HP5 Plus, Tri-X, T-Max, Delta, Portra, Fomapan, and other films."},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "What is the HP5 reciprocity formula?", "acceptedAnswer": {"@type": "Answer", "text": "Corrected time equals metered seconds raised to 1.31."}}, {"@type": "Question", "name": "Does Portra 400 have an official long-exposure table?", "acceptedAnswer": {"@type": "Answer", "text": "Kodak publishes no correction table beyond one second and recommends testing."}}]}]}
    body = tool_shell("filmrecip", "Free photography tool", "Film reciprocity failure calculator", "Turn a metered long exposure into the corrected shutter time for the film in your camera.", calculator, below)
    return page("Reciprocity Failure Calculator — HP5, Tri-X & More | Softgrove", "Free long exposure film calculator for HP5 Plus, Tri-X, T-Max, Delta, Portra 400, Fomapan, and more. Uses FilmRecip's sourced correction models.", "/tools/reciprocity-calculator/", body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-reciprocity-calculator.png")

def kiln_cost_tool():
    a = DATA["apps"]["kilncost"]
    calculator = r'''
<div class="fields">
<div class="field wide"><label for="kiln-preset">Kiln</label><select id="kiln-preset"></select></div>
<div class="field" id="custom-kw-field" hidden><label for="custom-kw">Kilowatts (kW)</label><input id="custom-kw" type="number" min="0.1" max="60" step="0.01" value="8"></div>
<div class="field" id="custom-brick-field" hidden><label for="custom-brick">Firebrick thickness</label><select id="custom-brick"><option value="3">3&Prime; brick</option><option value="2.5">2.5&Prime; brick</option></select></div>
<div class="field"><label for="cone">Target cone</label><select id="cone"></select></div>
<div class="field"><label for="ramp">Ramp rate</label><select id="ramp"><option value="15">Slow &middot; 15&deg;C/h</option><option value="60" selected>Medium &middot; 60&deg;C/h</option><option value="150">Fast &middot; 150&deg;C/h</option></select></div>
<div class="field"><label for="firing-type">Firing type</label><select id="firing-type"><option value="bisque">Bisque</option><option value="glaze" selected>Glaze</option></select></div>
<div class="field"><label for="hold-minutes">Hold time (minutes)</label><input id="hold-minutes" type="number" min="0" max="600" step="5" value="0"></div>
<div class="field wide"><label style="display:flex;align-items:center;gap:8px;font-weight:600"><input type="checkbox" id="tou-toggle" style="width:auto;min-height:0"> My utility charges time-of-use rates</label></div>
<div class="field" id="flat-rate-field"><label for="flat-rate">Electricity rate (&cent;/kWh)</label><input id="flat-rate" type="number" min="1" max="150" step="0.1" value="16"></div>
<div class="field" id="peak-rate-field" hidden><label for="peak-rate">Peak rate (&cent;/kWh)</label><input id="peak-rate" type="number" min="1" max="200" step="0.1" value="32"></div>
<div class="field" id="offpeak-rate-field" hidden><label for="offpeak-rate">Off-peak rate (&cent;/kWh)</label><input id="offpeak-rate" type="number" min="1" max="150" step="0.1" value="12"></div>
<div class="field" id="peak-start-field" hidden><label for="peak-start">Peak window start (24h)</label><input id="peak-start" type="number" min="0" max="24" step="1" value="16"></div>
<div class="field" id="peak-end-field" hidden><label for="peak-end">Peak window end (24h)</label><input id="peak-end" type="number" min="0" max="24" step="1" value="21"></div>
<div class="field" id="firing-start-field" hidden><label for="firing-start">Firing start time (24h)</label><input id="firing-start" type="number" min="0" max="24" step="1" value="8"></div>
</div>
<div class="actions"><button id="kiln-calc" type="button">Calculate firing cost</button></div>
<p id="kiln-error" class="error" role="alert"></p>
<div id="kiln-result" class="result" aria-live="polite">
<span class="eyebrow">Estimated firing cost</span><strong class="big" id="total-cost">$0.00</strong>
<dl>
<div><dt>Energy used</dt><dd id="energy-kwh">0 kWh</dd></div>
<div><dt>Total firing time</dt><dd id="total-hours">0 h</dd></div>
<div><dt>Target temperature</dt><dd id="target-temp">&mdash;</dd></div>
</dl>
<p class="fine" id="kiln-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const KILNS=[
["Skutt","KMT-614-3",115,1,2300,"3","6"],
["Skutt","KMT-818",240,1,6400,"2.5",null],
["Skutt","KMT-818",208,1,5550,"2.5",null],
["Skutt","KMT-818-3",240,1,6400,"3",null],
["Skutt","KMT-818-3",208,1,5550,"3",null],
["Skutt","KMT-822",240,1,8000,"2.5",null],
["Skutt","KMT-822",208,1,8000,"2.5",null],
["Skutt","KMT-822-3",240,1,8000,"3",null],
["Skutt","KMT-822-3",208,1,8000,"3",null],
["Skutt","KMT-1018",240,1,9460,"2.5",null],
["Skutt","KMT-1018",208,1,8320,"2.5",null],
["Skutt","KMT-1018-3",240,1,9460,"3",null],
["Skutt","KMT-1018-3",208,1,8320,"3",null],
["Skutt","KMT-1022",240,1,11520,"2.5",null],
["Skutt","KMT-1022",208,1,9984,"2.5",null],
["Skutt","KMT-1022-3",240,1,11520,"3",null],
["Skutt","KMT-1022-3",208,1,9984,"3",null],
["Skutt","KMT-1027",240,1,11520,"2.5",null],
["Skutt","KMT-1027",208,1,9984,"2.5","6"],
["Skutt","KMT-1027",240,3,11520,"2.5",null],
["Skutt","KMT-1027-3",240,1,11520,"3",null],
["Skutt","KMT-1027-3",208,1,9984,"3",null],
["Skutt","KMT-1218",240,1,11520,"2.5",null],
["Skutt","KMT-1218",208,1,9984,"2.5",null],
["Skutt","KMT-1222",240,1,11520,"2.5",null],
["Skutt","KMT-1222",208,1,9984,"2.5",null],
["Skutt","KMT-1227",240,1,11520,"2.5",null],
["Skutt","KMT-1227",208,1,9984,"2.5",null],
["Skutt","KMT-1227PK",240,1,14300,"3",null],
["Skutt","KMT-1227PK",208,1,14300,"3",null],
["Skutt","KMT-1231PK",240,1,17300,"3",null],
["Skutt","KMT-1231PK",208,1,16640,"3",null],
["Skutt","KMT-1627PK",240,3,23600,"3",null],
["Skutt","KMT-1627PK",208,3,23600,"3",null],
["L&L","e14S-3",240,1,3840,"3",null],
["L&L","e18S-3",240,1,5740,"3",null],
["L&L","e18S-3",208,3,4980,"3",null],
["L&L","e18T-3",240,1,8400,"3",null],
["L&L","e18T-3",208,1,8400,"3",null],
["L&L","e23S-3",240,1,9460,"3",null],
["L&L","e23S-3",208,1,8320,"3",null],
["L&L","e23T-3",240,1,11520,"3",null],
["L&L","e23T-3",208,1,9978,"3",null],
["L&L","e23T-3",240,3,11520,"3",null],
["L&L","e28S-3",240,1,11500,"3",null],
["L&L","e28S-3",208,1,9985,"3",null],
["L&L","e28T-3",240,1,11520,"3","8"],
["L&L","e28T-3",208,1,9978,"3",null],
["L&L","e28T-3",240,3,16620,"3",null]
];
const CONES=[
["022",null,586,590],["021",null,600,617],["020",null,626,638],["019",656,678,695],
["018",686,715,734],["017",705,738,763],["016",742,772,796],["015",750,791,818],
["014",757,807,838],["013",807,837,861],["012",843,861,882],["011",857,875,894],
["010",891,903,915],["09",907,920,930],["08",922,942,956],["07",962,976,987],
["06",981,998,1013],["05½",1004,1015,1025],["05",1021,1031,1044],["04",1046,1063,1077],
["03",1071,1086,1104],["02",1078,1102,1122],["01",1093,1119,1138],["1",1109,1137,1154],
["2",1112,1142,1164],["3",1115,1152,1170],["4",1141,1162,1183],["5",1159,1186,1207],
["5½",1167,1203,1225],["6",1185,1222,1243],["7",1201,1239,1257],["8",1211,1249,1271],
["9",1224,1260,1280],["10",1251,1285,1305]
];
const kilnSelect=document.querySelector("#kiln-preset"), coneSelect=document.querySelector("#cone");
let group=null, curMaker=null;
KILNS.forEach((k,i)=>{
 if(k[0]!==curMaker){curMaker=k[0];group=document.createElement("optgroup");group.label=curMaker;kilnSelect.append(group)}
 const o=document.createElement("option");o.value=String(i);
 o.textContent=`${k[1]} · ${k[2]}V ${k[3]}Ph · ${(k[4]/1000).toFixed(2)}kW`;
 group.append(o);
});
const customOpt=document.createElement("option");customOpt.value="-1";customOpt.textContent="Custom — enter kW";kilnSelect.append(customOpt);
kilnSelect.value="17"; // KMT-1027 240V/1Ph, launch sample
CONES.forEach((c,i)=>{const o=document.createElement("option");o.value=String(i);o.textContent=`Cone ${c[0]}`;coneSelect.append(o)});
coneSelect.value="29"; // cone 6
function bulkRate(t){return t==="bisque"?110:160}
function duty(t,b){if(t==="glaze")return b==="3"?0.60:0.65;return b==="3"?0.40:0.45}
function overlapDaily(startHour,dur,ws,we){let overlap=0;const start=startHour,end=startHour+dur;let day=Math.floor(start/24)*24-24;while(day<end){overlap+=Math.max(0,Math.min(end,day+we)-Math.max(start,day+ws));day+=24}return overlap}
function peakOverlap(startHour,dur,ps,pe){if(dur<=0||ps<0||ps>24||pe<0||pe>24||ps===pe)return 0;if(pe<ps)return overlapDaily(startHour,dur,ps,24)+overlapDaily(startHour,dur,0,pe);return overlapDaily(startHour,dur,ps,pe)}
function toggleFields(){
 const custom=kilnSelect.value==="-1";
 document.querySelector("#custom-kw-field").hidden=!custom;
 document.querySelector("#custom-brick-field").hidden=!custom;
 const tou=document.querySelector("#tou-toggle").checked;
 document.querySelector("#flat-rate-field").hidden=tou;
 for(const id of ["peak-rate-field","offpeak-rate-field","peak-start-field","peak-end-field","firing-start-field"]) document.querySelector("#"+id).hidden=!tou;
}
kilnSelect.addEventListener("change",()=>{toggleFields();run()});
document.querySelector("#tou-toggle").addEventListener("change",()=>{toggleFields();run()});
function run(){
 const err=document.querySelector("#kiln-error");err.textContent="";
 let kw,brick,kilnLabel,maxCone=null;
 if(kilnSelect.value==="-1"){
  kw=Number(document.querySelector("#custom-kw").value);
  brick=document.querySelector("#custom-brick").value;
  kilnLabel="Custom kiln";
  if(!Number.isFinite(kw)||kw<=0){err.textContent="Enter a valid kilowatt rating.";return}
 } else {
  const k=KILNS[Number(kilnSelect.value)];kw=k[4]/1000;brick=k[5];maxCone=k[6];
  kilnLabel=`${k[0]} ${k[1]} (${k[2]}V ${k[3]}Ph)`;
 }
 const cone=CONES[Number(coneSelect.value)];
 const ramp=document.querySelector("#ramp").value;
 const targetC=ramp==="15"?cone[1]:ramp==="60"?cone[2]:cone[3];
 if(targetC==null){err.textContent=`Orton doesn't publish a slow (15°C/h) rate for cone ${cone[0]}. Choose Medium or Fast.`;return}
 const type=document.querySelector("#firing-type").value;
 const holdMin=Number(document.querySelector("#hold-minutes").value)||0;
 const ambientC=25,finalSegC=100;
 if(targetC<=ambientC+finalSegC){err.textContent="This cone's target temperature is too low for the duration model.";return}
 const bulkHours=(targetC-finalSegC-ambientC)/bulkRate(type);
 const finalRampHours=finalSegC/Number(ramp);
 const holdHours=Math.max(0,holdMin)/60;
 const totalHours=bulkHours+finalRampHours+holdHours;
 const dutyCycle=duty(type,brick);
 const energyKWh=kw*totalHours*dutyCycle;
 let cost;
 if(document.querySelector("#tou-toggle").checked){
  const peakRate=Number(document.querySelector("#peak-rate").value)/100;
  const offRate=Number(document.querySelector("#offpeak-rate").value)/100;
  const ps=Number(document.querySelector("#peak-start").value), pe=Number(document.querySelector("#peak-end").value);
  const startHour=Number(document.querySelector("#firing-start").value);
  const peakHours=peakOverlap(startHour,totalHours,ps,pe);
  const offHours=totalHours-peakHours;
  const peakKWh=totalHours>0?energyKWh*peakHours/totalHours:0;
  const offKWh=energyKWh-peakKWh;
  cost=peakKWh*peakRate+offKWh*offRate;
 } else {
  const flat=Number(document.querySelector("#flat-rate").value)/100;
  if(!Number.isFinite(flat)||flat<0){err.textContent="Enter a valid electricity rate.";return}
  cost=energyKWh*flat;
 }
 document.querySelector("#total-cost").textContent="$"+cost.toFixed(2);
 document.querySelector("#energy-kwh").textContent=energyKWh.toFixed(2)+" kWh";
 document.querySelector("#total-hours").textContent=totalHours.toFixed(2)+" h";
 const f=targetC*9/5+32;
 document.querySelector("#target-temp").textContent=Math.round(targetC)+"°C · "+Math.round(f)+"°F";
 let note=`Duty cycle ${(dutyCycle*100).toFixed(0)}% (estimate for ${type}, ${brick}″ brick). `;
 if(maxCone){
  const idx=CONES.findIndex(c=>c[0]===cone[0]), maxIdx=CONES.findIndex(c=>c[0]===maxCone);
  if(idx>maxIdx) note+=`Note: ${kilnLabel}'s spec page lists cone ${maxCone} as its maximum — double-check this firing against the manufacturer. `;
 }
 note+="Sources: Orton cone chart, Skutt & L&L kiln specs, Skutt cost FAQ (retrieved Sep 2, 2026).";
 document.querySelector("#kiln-note").textContent=note;
}
document.querySelector("#kiln-calc").addEventListener("click",run);
for(const id of ["cone","ramp","firing-type","hold-minutes","flat-rate","peak-rate","offpeak-rate","peak-start","peak-end","firing-start","custom-kw","custom-brick"]) document.querySelector("#"+id).addEventListener("input",run);
toggleFields();run();
})();
</script>'''
    below = '''
<section><h2>How the cost estimate works</h2><p>KilnCost models a firing as three phases: a bulk climb (110&deg;C/h for bisque, 160&deg;C/h for glaze &mdash; calibrated against Skutt's published FAQ examples), a final 100&deg;C ramp at your chosen Orton speed, and any hold time. Energy is kilowatts &times; hours &times; an estimated duty cycle (how much of the firing the elements are actually drawing power), which mirrors the "adjustment factor" in Skutt's own published cost formula.</p><p>Duty cycle is an estimate (0.60&ndash;0.65 for glaze, 0.40&ndash;0.45 for bisque depending on brick thickness) calibrated to bracket Skutt's own worked examples &mdash; it is not a manufacturer-published constant, and actual duty cycle varies by kiln condition and ambient temperature.</p></section>
<section><h2>Sources</h2><ul class="sources"><li><a href="https://hotkilns.com/sites/default/files/pdf/cone-chart.pdf">Orton Pyrometric Cone temperature chart</a></li><li><a href="https://skutt.com/products-page/ceramic-kilns/">Skutt KilnMaster (KMT) specification tables</a></li><li><a href="https://hotkilns.com/kilns/e23t-3-pottery-kiln">L&amp;L Easy-Fire (e-series) specification tables</a></li><li><a href="https://skutt.com/skutt-resources/resources-just-for-you/studio/faqs/">Skutt FAQ: How much does it cost to fire my kiln?</a></li></ul></section>
<section><h2>Questions</h2><details><summary>What formula does this calculator use?</summary><p>kW &times; total firing hours &times; duty cycle = energy in kWh; energy &times; your electricity rate = cost. Firing hours come from the Orton cone chart's ramp-rate columns plus an estimated bulk-climb rate.</p></details><details><summary>Why is duty cycle an estimate?</summary><p>No manufacturer publishes a duty-cycle table. Skutt's own FAQ gives two different adjustment factors (0.5 and 0.7) for the same kiln and cone, so KilnCost uses the calibrated midpoint and always labels it an estimate.</p></details>'''
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebApplication", "name": "Kiln Firing Cost Calculator", "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any", "url": ORIGIN + "/tools/kiln-firing-cost-calculator/", "isAccessibleForFree": True, "description": "Estimate electric kiln firing cost from kilowatts, Orton cone target, ramp rate, and electricity rate, with flat or time-of-use pricing."},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "What formula does this calculator use?", "acceptedAnswer": {"@type": "Answer", "text": "Kilowatts times total firing hours times duty cycle gives energy in kWh; energy times your electricity rate gives cost."}}, {"@type": "Question", "name": "Why is duty cycle an estimate?", "acceptedAnswer": {"@type": "Answer", "text": "No manufacturer publishes a duty-cycle table; the calculator uses a value calibrated against Skutt's own published FAQ examples and always labels it an estimate."}}]}]}
    body = tool_shell("kilncost", "Free ceramics tool", "Kiln firing cost calculator", "See what a firing will cost before you load the kiln. Pick a Skutt or L&L preset or enter your own kilowatts.", calculator, below)
    return page("Kiln Firing Cost Calculator — Electric Kiln Electricity Cost | Softgrove", "Free electric kiln firing cost calculator. Pick from 49 Skutt and L&L kiln configurations or enter a custom kW, choose an Orton cone and ramp rate, flat or time-of-use electricity rates.", "/tools/kiln-firing-cost-calculator/", body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-kiln-firing-cost-calculator.png")

def cutlist_tool():
    a = DATA["apps"]["boardcut"]
    calculator = r'''
<div class="fields">
<div class="field"><label for="kerf">Blade kerf (inches)</label><input id="kerf" type="number" min="0" max="1" step="0.0625" value="0.125"></div>
</div>
<h3 style="margin-top:24px;font-size:15px;font-weight:600">In-stock boards / sheets</h3>
<div class="rows" id="stock-rows"></div>
<button type="button" class="secondary" id="add-stock" style="margin-top:10px">+ Add stock size</button>
<h3 style="margin-top:28px;font-size:15px;font-weight:600">Parts to cut</h3>
<div class="rows" id="part-rows"></div>
<button type="button" class="secondary" id="add-part" style="margin-top:10px">+ Add part</button>
<div class="actions"><button id="cut-calc" type="button">Generate cutting diagram</button><span class="hint">Free plan: 10 parts total &middot; dimensions in inches</span></div>
<p id="cut-error" class="error" role="alert"></p>
<div id="cut-result" class="result" aria-live="polite" hidden>
<span class="eyebrow">Yield</span><strong class="big" id="yield-pct">0%</strong>
<dl><div><dt>Sheets/boards used</dt><dd id="sheets-used">0</dd></div><div><dt>Parts placed</dt><dd id="parts-placed">0</dd></div><div><dt>Part area</dt><dd id="parts-area">0 sq ft</dd></div></dl>
<div class="sheet-output" id="sheet-output"></div>
</div>
<style>
.stock-row,.part-row{display:grid;grid-template-columns:2fr 1fr 1fr 1fr auto;gap:8px;align-items:end}
.stock-row .rlabel,.part-row .rlabel{font-size:11px;color:var(--muted);margin-bottom:3px;display:block}
@media(max-width:640px){
.stock-row,.part-row{grid-template-columns:1fr 1fr 1fr;row-gap:8px}
.stock-row>div:first-child,.part-row>div:first-child{grid-column:1/-1}
.stock-row>button,.part-row>button{grid-column:1/-1;justify-self:start;padding:4px 10px}
}
</style>
<script>
(()=>{
"use strict";
const EPS=1e-6;
const PALETTE=["#B87333","#3E8E8C","#7A2E33","#2E5E54","#E07A5F","#5B5EA6","#C4572A","#4C6E8C","#8A6D3B","#6B4C7A"];
function rowHTML(cls,ph1,v1,v2,v3,v4){
 return `<div class="${cls}"><div><span class="rlabel">Name</span><input class="c-name" value="${ph1}"></div>`+
 `<div><span class="rlabel">Length (in)</span><input class="c-l" type="number" min="0.1" step="0.0625" value="${v1}"></div>`+
 `<div><span class="rlabel">Width (in)</span><input class="c-w" type="number" min="0.1" step="0.0625" value="${v2}"></div>`+
 `<div><span class="rlabel">Qty${v4!==undefined?' (0=∞)':''}</span><input class="c-qty" type="number" min="${v4!==undefined?0:1}" step="1" value="${v3}"></div>`+
 `<button type="button" class="danger" aria-label="Remove row">&times;</button></div>`;
}
const stockWrap=document.querySelector("#stock-rows"), partWrap=document.querySelector("#part-rows");
function addStock(name,l,w,qty){const d=document.createElement("div");d.innerHTML=rowHTML("stock-row",name,l,w,qty,true);const row=d.firstElementChild;row.querySelector(".danger").addEventListener("click",()=>{if(stockWrap.children.length>1)row.remove()});stockWrap.append(row)}
function addPart(name,l,w,qty){const d=document.createElement("div");d.innerHTML=rowHTML("part-row",name,l,w,qty);const row=d.firstElementChild;row.querySelector(".danger").addEventListener("click",()=>{if(partWrap.children.length>1)row.remove()});partWrap.append(row)}
addStock("Plywood 4×8 sheet",96,48,0);
addPart("Side panel",24,18,2);
addPart("Shelf",30,11.5,3);
addPart("Back panel",46,22,1);
document.querySelector("#add-stock").addEventListener("click",()=>addStock("Stock "+(stockWrap.children.length+1),96,48,0));
document.querySelector("#add-part").addEventListener("click",()=>addPart("Part "+(partWrap.children.length+1),12,12,1));

function footprints(w,h){return Math.abs(w-h)<EPS?[{w,h,rotated:false}]:[{w,h,rotated:false},{w:h,h:w,rotated:true}]}
function fits(w,h,r){return w<=r.w+EPS && h<=r.h+EPS}
function scores(rect,w,h){return [Math.min(rect.w-w,rect.h-h),Math.max(rect.w-w,rect.h-h)]}
function better(a,b){
 if(a.s1!==b.s1) return a.s1<b.s1;
 if(a.s2!==b.s2) return a.s2<b.s2;
 if(a.sheetIdx!==b.sheetIdx) return a.sheetIdx<b.sheetIdx;
 if(a.y!==b.y) return a.y<b.y;
 if(a.x!==b.x) return a.x<b.x;
 return !a.rotated && b.rotated;
}
function commit(c,inst,sheet,kerf){
 const f=sheet.free[c.freeIdx], R=f.rect;
 sheet.free[c.freeIdx]=sheet.free[sheet.free.length-1]; sheet.free.pop();
 sheet.placements.push({name:inst.name,color:inst.color,x:R.x,y:R.y,w:c.w,h:c.h,rotated:c.rotated});
 const leftoverW=R.w-c.w, leftoverH=R.h-c.h;
 const needV=leftoverW>EPS, needH=leftoverH>EPS;
 const addFree=(r,depth)=>{if(r.w>EPS&&r.h>EPS)sheet.free.push({rect:r,depth})};
 const rec=(axis,pos,s,e)=>sheet.cuts.push({axis,pos,s,e});
 if(!needH&&!needV){return}
 if(needH&&!needV){rec("h",R.y+c.h+kerf/2,R.x,R.x+R.w);addFree({x:R.x,y:R.y+c.h+kerf,w:R.w,h:leftoverH-kerf},f.depth+1);return}
 if(!needH&&needV){rec("v",R.x+c.w+kerf/2,R.y,R.y+R.h);addFree({x:R.x+c.w+kerf,y:R.y,w:leftoverW-kerf,h:R.h},f.depth+1);return}
 const horizontalFirst=leftoverH<=leftoverW;
 if(horizontalFirst){
  rec("h",R.y+c.h+kerf/2,R.x,R.x+R.w); addFree({x:R.x,y:R.y+c.h+kerf,w:R.w,h:leftoverH-kerf},f.depth+1);
  rec("v",R.x+c.w+kerf/2,R.y,R.y+c.h); addFree({x:R.x+c.w+kerf,y:R.y,w:leftoverW-kerf,h:c.h},f.depth+2);
 } else {
  rec("v",R.x+c.w+kerf/2,R.y,R.y+R.h); addFree({x:R.x+c.w+kerf,y:R.y,w:leftoverW-kerf,h:R.h},f.depth+1);
  rec("h",R.y+c.h+kerf/2,R.x,R.x+c.w); addFree({x:R.x,y:R.y+c.h+kerf,w:c.w,h:leftoverH-kerf},f.depth+2);
 }
}
function place(inst,sheets,stocks,used,kerf){
 let best=null;
 for(let si=0;si<sheets.length;si++){
  const sheet=sheets[si];
  for(let fi=0;fi<sheet.free.length;fi++){
   const f=sheet.free[fi].rect;
   for(const foot of footprints(inst.l,inst.w)){
    if(fits(foot.w,foot.h,f)){
     const [s1,s2]=scores(f,foot.w,foot.h);
     const cand={sheetIdx:si,freeIdx:fi,w:foot.w,h:foot.h,rotated:foot.rotated,s1,s2,y:f.y,x:f.x};
     if(!best||better(cand,best)) best=cand;
    }
   }
  }
 }
 if(best){commit(best,inst,sheets[best.sheetIdx],kerf);return true}
 let chosen=-1;
 for(let i=0;i<stocks.length;i++){
  const st=stocks[i];
  if(!(st.qty===0||used[i]<st.qty)) continue;
  const usable={x:0,y:0,w:st.l,h:st.w};
  if(usable.w<=EPS||usable.h<=EPS) continue;
  if(!footprints(inst.l,inst.w).some(ft=>fits(ft.w,ft.h,usable))) continue;
  if(chosen===-1||st.l*st.w<stocks[chosen].l*stocks[chosen].w-EPS) chosen=i;
 }
 if(chosen===-1) return false;
 used[chosen]++;
 const sheet={stockIdx:chosen,stock:stocks[chosen],free:[{rect:{x:0,y:0,w:stocks[chosen].l,h:stocks[chosen].w},depth:0}],placements:[],cuts:[]};
 sheets.push(sheet);
 const root=sheet.free[0];
 let rbest=null;
 for(const foot of footprints(inst.l,inst.w)){
  if(fits(foot.w,foot.h,root.rect)){
   const [s1,s2]=scores(root.rect,foot.w,foot.h);
   const cand={sheetIdx:sheets.length-1,freeIdx:0,w:foot.w,h:foot.h,rotated:foot.rotated,s1,s2,y:root.rect.y,x:root.rect.x};
   if(!rbest||better(cand,rbest)) rbest=cand;
  }
 }
 commit(rbest,inst,sheets[rbest.sheetIdx],kerf);
 return true;
}
function svgFor(sheet){
 const maxW=700,maxH=420;
 const scale=Math.min(maxW/sheet.stock.l,maxH/sheet.stock.w);
 const W=sheet.stock.l*scale,H=sheet.stock.w*scale;
 const y=v=>H-v*scale; // flip so origin reads bottom-left like the app
 let s=`<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cutting diagram for ${sheet.stock.name}">`;
 s+=`<rect x="0" y="0" width="${W}" height="${H}" fill="#f8f5ef" stroke="#B9B2A6"/>`;
 for(const p of sheet.placements){
  const px=p.x*scale, pw=p.w*scale, ph=p.h*scale, py=y(p.y)-ph;
  s+=`<rect x="${px.toFixed(1)}" y="${py.toFixed(1)}" width="${pw.toFixed(1)}" height="${ph.toFixed(1)}" fill="${p.color}" fill-opacity="0.82" stroke="#2C282C" stroke-width="1.5"/>`;
  if(pw>46&&ph>20){
   s+=`<text x="${(px+pw/2).toFixed(1)}" y="${(py+ph/2-5).toFixed(1)}" font-size="11" font-family="ui-monospace,monospace" fill="#fff" text-anchor="middle">${esc(p.name)}</text>`;
   s+=`<text x="${(px+pw/2).toFixed(1)}" y="${(py+ph/2+9).toFixed(1)}" font-size="10" font-family="ui-monospace,monospace" fill="#fff" text-anchor="middle">${p.origW}×${p.origH}${p.rotated?' ⟳':''}</text>`;
  }
 }
 for(const c of sheet.cuts){
  if(c.axis==="h") s+=`<line x1="${(c.s*scale).toFixed(1)}" y1="${y(c.pos).toFixed(1)}" x2="${(c.e*scale).toFixed(1)}" y2="${y(c.pos).toFixed(1)}" stroke="#7A2E33" stroke-width="1" stroke-dasharray="4 3"/>`;
  else s+=`<line x1="${(c.pos*scale).toFixed(1)}" y1="${y(c.s).toFixed(1)}" x2="${(c.pos*scale).toFixed(1)}" y2="${y(c.e).toFixed(1)}" stroke="#7A2E33" stroke-width="1" stroke-dasharray="4 3"/>`;
 }
 s+="</svg>";
 return s;
}
function esc(t){return String(t).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")}
function run(){
 const err=document.querySelector("#cut-error"); err.textContent="";
 document.querySelector("#cut-result").hidden=true;
 const kerf=Number(document.querySelector("#kerf").value);
 if(!Number.isFinite(kerf)||kerf<0){err.textContent="Enter a valid kerf width.";return}
 const stocks=[...stockWrap.children].map(row=>({
  name:row.querySelector(".c-name").value.trim()||"Stock",
  l:Number(row.querySelector(".c-l").value), w:Number(row.querySelector(".c-w").value),
  qty:Number(row.querySelector(".c-qty").value)||0
 }));
 if(stocks.some(s=>!(s.l>0)||!(s.w>0))){err.textContent="Every stock size needs a length and width greater than 0.";return}
 const partRows=[...partWrap.children].map((row,i)=>({
  name:row.querySelector(".c-name").value.trim()||"Part",
  l:Number(row.querySelector(".c-l").value), w:Number(row.querySelector(".c-w").value),
  qty:Math.max(1,Math.round(Number(row.querySelector(".c-qty").value)||1)),
  color:PALETTE[i%PALETTE.length]
 }));
 if(partRows.some(p=>!(p.l>0)||!(p.w>0))){err.textContent="Every part needs a length and width greater than 0.";return}
 const totalQty=partRows.reduce((n,p)=>n+p.qty,0);
 if(totalQty>10){err.textContent=`This free tool plans up to 10 parts total (you have ${totalQty}). Reduce quantities, or use Boardcut on iPhone for unlimited parts.`;return}
 if(totalQty===0){err.textContent="Add at least one part.";return}
 let instances=[];
 partRows.forEach(p=>{for(let i=0;i<p.qty;i++)instances.push({name:p.name,l:p.l,w:p.w,origW:p.l,origH:p.w,color:p.color})});
 instances.sort((a,b)=>(b.l*b.w)-(a.l*a.w));
 const sheets=[]; const used=stocks.map(()=>0); const unplaced=[];
 for(const inst of instances){ if(!place(inst,sheets,stocks,used,kerf)) unplaced.push(inst.name); }
 let partsArea=0, usedArea=0, placedCount=0;
 for(const sh of sheets){ usedArea+=sh.stock.l*sh.stock.w; for(const p of sh.placements){partsArea+=p.w*p.h; placedCount++} }
 const yieldPct = usedArea>EPS ? (partsArea/usedArea*100) : 0;
 document.querySelector("#yield-pct").textContent = yieldPct.toFixed(1)+"%";
 document.querySelector("#sheets-used").textContent = String(sheets.length);
 document.querySelector("#parts-placed").textContent = `${placedCount} / ${instances.length}`;
 document.querySelector("#parts-area").textContent = (partsArea/144).toFixed(2)+" sq ft";
 const out=document.querySelector("#sheet-output"); out.innerHTML="";
 sheets.forEach((sh,i)=>{
  const fig=document.createElement("figure");
  fig.innerHTML=`<figcaption>${esc(sh.stock.name)} #${i+1} — ${sh.stock.l}×${sh.stock.w}in</figcaption>`+svgFor(sh);
  out.append(fig);
 });
 if(unplaced.length){ err.textContent = `Couldn't fit: ${unplaced.join(", ")}. Add more stock or a larger sheet size.`; }
 document.querySelector("#cut-result").hidden=false;
}
document.querySelector("#cut-calc").addEventListener("click",run);
run();
})();
</script>'''
    below = '''
<section><h2>How the layout is built</h2><p>This tool packs parts using the same guillotine-cut model as Boardcut: every placement is separated from the rest of the sheet by straight, full-length saw cuts, and every cut consumes one blade kerf. Parts are placed largest-area-first into the best-fitting leftover space (best short-side fit), and rotation is allowed unless a part is square.</p><p>Boardcut's iPhone app runs 24 restarts of this solver (different sort orders, split rules, and scoring) and keeps the best result, plus supports grain-direction locking, multiple material groups, and dimensional lumber. This free web version runs one high-quality pass for up to 10 parts.</p></section>
<section><h2>Questions</h2><details><summary>Is this a true guillotine cut layout?</summary><p>Yes — every part can be freed using only straight, edge-to-edge saw cuts, in the order shown by the dashed lines, which is what a table saw or panel saw needs.</p></details><details><summary>What does "yield" mean here?</summary><p>Total part area divided by the area of the stock actually used, as a percentage. It does not subtract reusable offcuts, so it's a conservative (lower) number than Boardcut's in-app waste metric, which credits offcuts large enough to reuse.</p></details>'''
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebApplication", "name": "Cut List Optimizer", "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any", "url": ORIGIN + "/tools/cut-list-optimizer/", "isAccessibleForFree": True, "description": "Free online cut list optimizer: enter stock sheet sizes and part dimensions to get a guillotine cutting diagram and yield, kerf-aware."},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "Is this a true guillotine cut layout?", "acceptedAnswer": {"@type": "Answer", "text": "Yes, every part can be freed using only straight, edge-to-edge saw cuts."}}, {"@type": "Question", "name": "What does yield mean here?", "acceptedAnswer": {"@type": "Answer", "text": "Total part area divided by the stock area used, as a percentage."}}]}]}
    body = tool_shell("boardcut", "Free woodworking tool", "Cut list optimizer", "Turn a stock list and a parts list into a kerf-aware cutting diagram. Free for up to 10 parts.", calculator, below)
    return page("Free Cut List Optimizer Online — Plywood & Sheet Cutting Layout | Softgrove", "Free online cut list optimizer for plywood and sheet goods. Enter stock sizes and part dimensions, get a guillotine cutting diagram, kerf, and yield. Up to 10 parts free.", "/tools/cut-list-optimizer/", body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-cut-list-optimizer.png")

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
            a = DATA["apps"][k]
            if a["asc"] not in DESCS: continue  # e.g. Fibrolog: added to apps.json, ASC desc not live yet
            p = PARSED[a["asc"]]; d = DESCS[a["asc"]]
            pricing = a.get("pricing")
            price = f'free with no piece limit; Pro {pricing["weekly"]} or {pricing["lifetime"]} lifetime, with a {pricing["trial"]} for eligible customers' if pricing and "weekly" in pricing else (
                f'free core; one-time {pricing["lifetime"]} Lifetime unlock adds Blade Card sharing and CSV export (no subscription)' if pricing else
                f"free core; Premium ${p['monthly']}/mo or ${p['yearly']}/yr" if p["monthly"] else "free")
            lines.append(f"- [{a['name']}]({ORIGIN}/apps/{k}/): {d['subtitle']} — {a['catLabel']}; {price}. App Store id{a['id']}.")
    lines += ["", "## Free web tools (no sign-up, no install)",
              f"- [Film Reciprocity Failure Calculator]({ORIGIN}/tools/reciprocity-calculator/): Reciprocity-corrected long exposure times for HP5 Plus, Tri-X, T-Max, Delta, Portra 400, Fomapan, and more.",
              f"- [Kiln Firing Cost Calculator]({ORIGIN}/tools/kiln-firing-cost-calculator/): Electric kiln firing cost from kilowatts, Orton cone, ramp rate, and electricity rate; 49 Skutt/L&L presets or custom.",
              f"- [Cut List Optimizer]({ORIGIN}/tools/cut-list-optimizer/): Guillotine cutting diagram and yield from stock and part dimensions, kerf-aware; free for up to 10 parts."]
    lines += ["", "## Free printable templates (PDF, no sign-up)"]
    for slug, t in DATA["templates"].items():
        lines.append(f"- [{t['h1']}]({ORIGIN}/templates/{slug}/): {t['desc']}")
    lines += ["", "## Workshop guides (woodworking & sharpening)"]
    for slug, g in DATA.get("guides", {}).items():
        lines.append(f"- [{g['h1']}]({ORIGIN}/guides/{slug}/): {g['desc']}")
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
    pages = {"/": house(), "/templates/": templates_hub(), "/404.html": not_found(),
             "/tools/reciprocity-calculator/": reciprocity_tool(),
             "/tools/kiln-firing-cost-calculator/": kiln_cost_tool(),
             "/tools/cut-list-optimizer/": cutlist_tool()}
    for key, a in DATA["apps"].items():
        if a["asc"] not in DESCS: continue  # e.g. Fibrolog: added to apps.json, ASC desc not live yet
        pages[f"/apps/{key}/"] = app_page(key)
    for slug in DATA["templates"]:
        pages[f"/templates/{slug}/"] = template_page(slug)
    for slug in DATA.get("guides", {}):
        pages[f"/guides/{slug}/"] = guide_page(slug)
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
