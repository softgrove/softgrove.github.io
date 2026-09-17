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
TODAY = "2026-09-18"  # set per release; hash-gate keeps unchanged pages stable

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
    built = lambda k: DATA["apps"][k]["asc"] in DESCS  # only link apps that have a built /apps/<k>/ page
    sibs = [k for sh in DATA["shelves"] for k in sh["apps"] if k != key and built(k)][:20]
    same_shelf = next(sh["apps"] for sh in DATA["shelves"] if key in sh["apps"])
    picks = [k for k in same_shelf if k != key and built(k)][:3] or sibs[:3]
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

def tool_shell_standalone(eyebrow, h1, lede, calculator, below):
    """Same layout as tool_shell but with no app tie-in — for tools whose
    matching app isn't published yet, so we make no App Store promise."""
    return f"""
<style>
.tool-hero{{padding:64px 0 30px;max-width:820px}}
.tool-hero h1{{font-size:clamp(38px,6vw,60px);max-width:18ch;margin-top:8px}}
.tool-hero .lede{{font-size:19px;color:#4d4850;margin-top:18px;max-width:64ch}}
.calculator{{max-width:820px;background:#fff;border:1px solid var(--line);border-top:5px solid var(--teal);border-radius:14px;padding:clamp(18px,4vw,34px);box-shadow:0 10px 30px rgba(44,40,44,.06)}}
.fields{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}
.field{{display:flex;flex-direction:column;gap:6px;min-width:0}}
.field.wide{{grid-column:1/-1}}
label,.label{{font-weight:600;font-size:14px}}
input,select,button{{font:inherit}}
input,select{{width:100%;min-height:46px;border:1px solid #b9b2a6;border-radius:8px;background:#fff;color:var(--ink);padding:9px 11px}}
select:disabled,input:disabled{{opacity:.6}}
button{{border:0;border-radius:8px;background:var(--ink);color:var(--paper);font-weight:600;padding:12px 19px;cursor:pointer}}
button.secondary{{background:#fff;color:var(--ink);border:1px solid var(--line)}}
.actions{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:20px}}
.hint,.fine{{font-size:13px;color:var(--muted)}}
.result{{margin-top:24px;background:#EAF3F2;border-radius:10px;padding:20px}}
.result strong.big{{display:block;font-family:"Newsreader",Georgia,serif;font-size:clamp(28px,6vw,42px);font-weight:500;line-height:1.1;color:#2A6E6C}}
.result dl{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:16px}}
.result dt{{font-size:12px;color:var(--muted)}}.result dd{{font-weight:600}}
.error{{color:#9b2c2c;font-size:14px;margin-top:12px;min-height:1.5em}}
.tool-copy{{max-width:780px;margin-top:62px}}.tool-copy section{{margin-top:46px}}
.tool-copy h2{{font-size:30px;margin-bottom:14px}}.tool-copy p{{margin-top:12px;max-width:66ch}}
.sources{{padding-left:20px;display:grid;gap:9px;margin-top:14px;font-size:14px}}
@media(max-width:640px){{.tool-hero{{padding-top:46px}}.fields,.result dl{{grid-template-columns:1fr}}nav.top a{{margin-left:12px;font-size:12px}}}}
</style>
<main class="wrap">
<header class="tool-hero"><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(h1)}</h1><p class="lede">{esc(lede)}</p></header>
<section class="calculator" aria-label="{esc(h1)}">{calculator}</section>
<article class="tool-copy">{below}
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

# ---------------------------------------------------- free tools, batch 2 (2026-09-17)
# One page per app that had no acquisition page. Each calculator mirrors the
# app's own pure logic (file:line noted in the "Sources" section of the page).

def tool_faq(items):
    """items: [(question, answer_html)] -> (details html, FAQPage json-ld)."""
    html = "".join(f"<details><summary>{esc(q)}</summary><p>{a}</p></details>" for q, a in items)
    ld = {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
        for q, a in items]}
    return html, ld

def tool_ld(name, path, desc, category, faq_ld):
    return {"@context": "https://schema.org", "@graph": [
        {"@type": "WebApplication", "name": name, "applicationCategory": category, "operatingSystem": "Any",
         "url": ORIGIN + path, "isAccessibleForFree": True, "description": desc,
         "publisher": {"@type": "Organization", "name": "Softgrove", "url": ORIGIN + "/"}},
        faq_ld]}

TOOLS_INDEX = [
    # (path, title on hub, one-line, app key)
    ("/tools/fuel-cost-calculator/", "Fuel cost calculator", "Trip fuel cost and cost per mile from distance, economy, and pump price; MPG from two fill-ups.", "motorlog"),
    ("/tools/houseplant-watering-calculator/", "Houseplant watering calculator", "How often to water 25 common houseplants, with your next watering dates.", "plantlog"),
    ("/tools/sourdough-hydration-calculator/", "Sourdough hydration calculator", "Dough hydration with levain included, or the water to hit a target, plus salt.", "banneton"),
    ("/tools/reef-dosing-calculator/", "Reef dosing calculator", "Millilitres of alkalinity, calcium, or magnesium additive to reach a target, from your product label.", "coralog"),
    ("/tools/reading-time-calculator/", "Reading time calculator", "Days to finish a book from your page pace, or pages per day to hit a deadline.", "readlog"),
    ("/tools/varroa-mite-calculator/", "Varroa mite calculator", "Mites per 100 bees from an alcohol wash or sugar roll, with the 3% treatment flag.", "combwise"),
    ("/tools/reciprocity-calculator/", "Film reciprocity failure calculator", "Corrected long-exposure times for HP5 Plus, Tri-X, T-Max, Delta, Portra, Fomapan.", "filmrecip"),
    ("/tools/kiln-firing-cost-calculator/", "Kiln firing cost calculator", "Electric kiln firing cost from kilowatts, Orton cone, ramp rate, and electricity rate.", "kilncost"),
    ("/tools/cut-list-optimizer/", "Cut list optimizer", "Guillotine cutting diagram and yield from stock and part sizes, kerf-aware.", "boardcut"),
    ("/tools/board-feet-calculator/", "Board feet calculator", "Total board feet and cost for a lumber order, across as many board sizes as you need.", "boardcut"),
    ("/tools/miter-angle-calculator/", "Miter angle calculator", "Compound miter and bevel for crown molding, or a plain miter for baseboard and picture frames.", "boardcut"),
    ("/tools/wood-shelf-sag-calculator/", "Wood shelf sag calculator", "Expected shelf sag from span, depth, thickness, material, and load, Sagulator-style.", "boardcut"),
    ("/tools/pet-age-calculator/", "Pet age calculator", "Dog or cat age in human years — a 2020 DNA-methylation study for dogs, International Cat Care's chart for cats.", "pawlog"),
    ("/tools/dog-cat-calorie-calculator/", "Dog & cat calorie calculator", "Daily calories (RER/MER) from weight, species, and life stage or status, the standard veterinary formula.", "pawlog"),
    ("/tools/whetstone-angle-calculator/", "Whetstone angle calculator", "Spine-lift height for a target sharpening angle, or the angle for a lift you used — freehand or guided rod.", "whetlog"),
    ("/tools/wallpaper-roll-calculator/", "Wallpaper roll calculator", "Rolls needed from wall width, ceiling height, roll size, pattern repeat, and door/window openings, metric or imperial.", None),
    ("/tools/dough-temperature-calculator/", "Dough temperature calculator", "Water temperature to hit a target dough temp from room, flour, and levain temperature — the standard ×3/×4 baker's formula.", "banneton"),
    ("/tools/bee-syrup-calculator/", "Bee syrup calculator", "Sugar to add for 1:1 spring or 2:1 fall syrup, by the correct weight-based ratio, with a cup measure.", "combwise"),
]

def more_tools(current_path):
    items = "".join(
        f'<li><a href="{p}">{esc(t)}</a> — {esc(d)}</li>'
        for p, t, d, _ in TOOLS_INDEX if p != current_path)
    return f'<section><h2>More free tools</h2><ul class="sources" style="font-size:15px">{items}</ul><p class="fine" style="margin-top:12px"><a href="/tools/">All free tools</a> · <a href="/templates/">Free printable templates</a></p></section>'

# ------------------------------------------------------------ 1. fuel cost (MotorLog)
def fuel_cost_tool():
    a = DATA["apps"]["motorlog"]; path = "/tools/fuel-cost-calculator/"
    calculator = r'''
<style>.calculator [hidden]{display:none!important}</style>
<div class="fields">
<div class="field wide"><label for="fc-mode">What do you want to work out?</label><select id="fc-mode"><option value="trip">Fuel cost of a trip</option><option value="mpg">Fuel economy from two fill-ups</option></select></div>
</div>
<div id="fc-trip">
<div class="fields" style="margin-top:16px">
<div class="field"><label for="fc-dist">Distance</label><input id="fc-dist" type="number" min="0" step="1" value="250" inputmode="decimal"></div>
<div class="field"><label for="fc-dist-unit">Distance unit</label><select id="fc-dist-unit"><option value="mi">miles</option><option value="km">kilometres</option></select></div>
<div class="field"><label for="fc-econ">Fuel economy</label><input id="fc-econ" type="number" min="0" step="0.1" value="32" inputmode="decimal"></div>
<div class="field"><label for="fc-econ-unit">Economy unit</label><select id="fc-econ-unit"><option value="mpgus">MPG (US gallon)</option><option value="mpguk">MPG (UK gallon)</option><option value="l100">L/100 km</option><option value="kml">km/L</option></select></div>
<div class="field"><label for="fc-price">Fuel price</label><input id="fc-price" type="number" min="0" step="0.001" value="3.45" inputmode="decimal"></div>
<div class="field"><label for="fc-price-unit">Price per</label><select id="fc-price-unit"><option value="galus">US gallon</option><option value="galuk">UK gallon</option><option value="l">litre</option></select></div>
</div>
</div>
<div id="fc-fill" hidden>
<div class="fields" style="margin-top:16px">
<div class="field"><label for="fc-odo1">Odometer at previous full fill</label><input id="fc-odo1" type="number" min="0" step="1" value="41200" inputmode="decimal"></div>
<div class="field"><label for="fc-odo2">Odometer at this full fill</label><input id="fc-odo2" type="number" min="0" step="1" value="41538" inputmode="decimal"></div>
<div class="field"><label for="fc-vol">Fuel added to refill (this fill + any partial fills since)</label><input id="fc-vol" type="number" min="0" step="0.01" value="10.6" inputmode="decimal"></div>
<div class="field"><label for="fc-vol-unit">Units</label><select id="fc-vol-unit"><option value="mi-galus">miles &amp; US gallons</option><option value="mi-galuk">miles &amp; UK gallons</option><option value="km-l">kilometres &amp; litres</option></select></div>
<div class="field"><label for="fc-paid">Total paid for that fuel (optional)</label><input id="fc-paid" type="number" min="0" step="0.01" value="36.57" inputmode="decimal"></div>
</div>
</div>
<div class="actions"><button id="fc-calc" type="button">Calculate</button><span class="hint">Updates as you type</span></div>
<p id="fc-error" class="error" role="alert"></p>
<div id="fc-result" class="result" aria-live="polite">
<span class="eyebrow" id="fc-lead">Trip fuel cost</span><strong class="big" id="fc-big">—</strong>
<dl><div><dt id="fc-k1">Fuel needed</dt><dd id="fc-v1">—</dd></div><div><dt id="fc-k2">Cost per mile</dt><dd id="fc-v2">—</dd></div><div><dt id="fc-k3">Economy used</dt><dd id="fc-v3">—</dd></div></dl>
<p class="fine" id="fc-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const KM_PER_MI=1.609344,L_PER_GALUS=3.785411784,L_PER_GALUK=4.54609;
const $=s=>document.querySelector(s),num=id=>Number($(id).value);
function toL100(v,u){if(v<=0)return NaN;if(u==="l100")return v;if(u==="kml")return 100/v;if(u==="mpgus")return 100*L_PER_GALUS/(v*KM_PER_MI);return 100*L_PER_GALUK/(v*KM_PER_MI)}
function litresPerUnit(u){return u==="galus"?L_PER_GALUS:u==="galuk"?L_PER_GALUK:1}
function money(x){return x.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}
function trip(){
 const dist=num("#fc-dist"),du=$("#fc-dist-unit").value,econ=num("#fc-econ"),eu=$("#fc-econ-unit").value,price=num("#fc-price"),pu=$("#fc-price-unit").value;
 if(!(dist>0)||!(econ>0)||!(price>=0))return "Enter a distance, a fuel economy, and a fuel price above zero.";
 const km=du==="mi"?dist*KM_PER_MI:dist,l100=toL100(econ,eu),litres=km*l100/100,perUnit=litresPerUnit(pu),units=litres/perUnit,cost=units*price;
 const unitName=pu==="l"?"L":pu==="galus"?"US gal":"UK gal",dn=du==="mi"?"mile":"km";
 $("#fc-lead").textContent="Trip fuel cost";$("#fc-big").textContent=money(cost);
 $("#fc-k1").textContent="Fuel needed";$("#fc-v1").textContent=`${units.toFixed(2)} ${unitName}`;
 $("#fc-k2").textContent=`Cost per ${dn}`;$("#fc-v2").textContent=(cost/dist).toFixed(3);
 $("#fc-k3").textContent="Economy used";$("#fc-v3").textContent=`${l100.toFixed(2)} L/100 km`;
 $("#fc-note").textContent=`${dist.toLocaleString()} ${du} at ${econ} ${$("#fc-econ-unit").selectedOptions[0].textContent} with fuel at ${price} per ${$("#fc-price-unit").selectedOptions[0].textContent}. Same arithmetic as MotorLog's cost-per-mile figure: fuel used × price ÷ distance.`;
 return ""}
function fill(){
 const o1=num("#fc-odo1"),o2=num("#fc-odo2"),vol=num("#fc-vol"),u=$("#fc-vol-unit").value,paid=num("#fc-paid");
 const distance=o2-o1;if(!(distance>0))return "The second odometer reading must be higher than the first.";if(!(vol>0))return "Enter the fuel volume added.";
 const km=u==="km-l"?distance:distance*KM_PER_MI,litres=u==="km-l"?vol:vol*(u==="mi-galus"?L_PER_GALUS:L_PER_GALUK);
 const l100=100*litres/km,mpgus=(km/KM_PER_MI)/(litres/L_PER_GALUS),mpguk=(km/KM_PER_MI)/(litres/L_PER_GALUK),kml=km/litres;
 const primary=u==="km-l"?`${kml.toFixed(2)} km/L`:u==="mi-galus"?`${mpgus.toFixed(1)} MPG`:`${mpguk.toFixed(1)} MPG (UK)`;
 $("#fc-lead").textContent="Fuel economy over this tank";$("#fc-big").textContent=primary;
 $("#fc-k1").textContent="Also";$("#fc-v1").textContent=u==="km-l"?`${mpgus.toFixed(1)} MPG · ${l100.toFixed(2)} L/100 km`:`${l100.toFixed(2)} L/100 km · ${kml.toFixed(2)} km/L`;
 const dn=u==="km-l"?"km":"mile";$("#fc-k2").textContent=`Cost per ${dn}`;$("#fc-v2").textContent=paid>0?(paid/distance).toFixed(3):"—";
 $("#fc-k3").textContent="Distance on this tank";$("#fc-v3").textContent=`${distance.toLocaleString()} ${u==="km-l"?"km":"mi"}`;
 $("#fc-note").textContent="MotorLog computes economy only between two full fill-ups: distance driven ÷ (this fill + any partial fills banked since the last full one). Partial fills alone never produce a reading.";
 return ""}
function run(){const mode=$("#fc-mode").value;$("#fc-trip").hidden=mode!=="trip";$("#fc-fill").hidden=mode!=="mpg";const err=mode==="trip"?trip():fill();$("#fc-error").textContent=err;if(err){$("#fc-big").textContent="—"}}
document.querySelectorAll("#fc-mode,#fc-trip input,#fc-trip select,#fc-fill input,#fc-fill select").forEach(el=>el.addEventListener("input",run));
$("#fc-calc").addEventListener("click",run);$("#fc-mode").addEventListener("change",run);run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("How do I calculate the fuel cost of a trip?", "Divide the distance by your fuel economy to get the fuel needed, then multiply by the price per gallon or litre. For 250 miles at 32 MPG and $3.45 per gallon: 250 ÷ 32 = 7.81 gallons, × 3.45 = $26.95."),
        ("How do I work out MPG from fill-ups?", "Fill the tank, note the odometer, drive, fill it again to full. MPG = miles driven ÷ gallons added on the second fill. Any partial fills in between are added to that gallon figure. Two full fills are the minimum."),
        ("What is cost per mile?", "Total spent on fuel divided by miles driven over the same interval. MotorLog also adds service costs to give an all-in cost per mile in its Insights view."),
        ("Why does the calculator support L/100 km, km/L, and UK MPG?", "Fuel economy is quoted differently by region. All inputs are converted to litres per 100 km internally, so mixing units such as miles with litre prices works."),
    ])
    below = f'''
<section><h2>How this fuel cost calculator works</h2><p>Trip cost is fuel used multiplied by pump price. Fuel used is distance divided by economy. Every economy unit is converted to litres per 100 km first, using 1 mile = 1.609344 km, 1 US gallon = 3.785 L, and 1 UK gallon = 4.546 L, so you can mix miles with a per-litre price.</p><p>The fill-up mode uses MotorLog's rule exactly: economy is only measured between two <em>full</em> fills, and the volume for the interval is this fill plus any partial fills since the previous full one. That is why a single fill-up cannot give an MPG figure.</p></section>
<section><h2>Sources</h2><p>Formulas copied from MotorLog's fuel economy engine on September 17, 2026: <span class="mono">mpg = miles / volumeUsed</span> and <span class="mono">costPerMile = costUsed / miles</span>, where <span class="mono">volumeUsed</span> is the closing full fill plus banked partial fills.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free fuel cost calculator: trip fuel cost and cost per mile from distance, MPG or L/100 km, and pump price. Also works out MPG from two fill-ups the way MotorLog does."
    ld = tool_ld("Fuel Cost Calculator", path, desc, "UtilitiesApplication", faq_ld)
    body = tool_shell("motorlog", "Free car tool", "Fuel cost calculator", "How much a trip will cost in fuel, your cost per mile, and the MPG you actually got on the last tank.", calculator, below)
    return page("Fuel Cost Calculator — Trip Cost, Cost per Mile & MPG | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-fuel-cost-calculator.png")

# ------------------------------------------------ 2. houseplant watering (PlantLog)
# Copied from plantlog/PlantLog/Data/PlantCareGuide.swift (25 entries, 2026-09-17).
PLANT_GUIDE = [
    ("Pothos", "Epipremnum aureum", "Low light", 10, "Trailing vines", "Tolerates a wide range of conditions. Let soil dry out between waterings. Yellowing leaves usually mean too much water."),
    ("Snake Plant", "Dracaena trifasciata", "Low light", 14, "Succulents & drought-tolerant", "Very drought-tolerant. Water sparingly; more plants die from overwatering than underwatering."),
    ("ZZ Plant", "Zamioculcas zamiifolia", "Low light", 14, "Succulents & drought-tolerant", "Stores water in rhizomes. Allow soil to dry completely. Handles low light."),
    ("Cast Iron Plant", "Aspidistra elatior", "Low light", 14, "Hardy foliage", "Extremely hardy. Slow grower. Tolerates neglect, deep shade, and temperature swings."),
    ("Peace Lily", "Spathiphyllum spp.", "Low light", 7, "Flowering", "Droops visibly when thirsty, a reliable watering signal. Prefers consistently moist, not soggy, soil."),
    ("Chinese Evergreen", "Aglaonema spp.", "Low light", 10, "Hardy foliage", "Tolerates low light, but variegated varieties prefer bright indirect. Avoid cold drafts."),
    ("Heartleaf Philodendron", "Philodendron hederaceum", "Bright indirect", 7, "Trailing vines", "Forgiving and fast-growing. Water when the top inch of soil is dry. Yellowing means overwatering."),
    ("Monstera", "Monstera deliciosa", "Bright indirect", 10, "Statement foliage", "Allow the top 2 inches of soil to dry between waterings. High humidity preferred. Wipe leaves to keep them breathing."),
    ("Bird of Paradise", "Strelitzia reginae", "Bright indirect", 10, "Statement foliage", "Needs bright indirect to filtered direct sun indoors. Water when the top 2 inches are dry."),
    ("Rubber Plant", "Ficus elastica", "Bright indirect", 10, "Statement foliage", "Keep soil lightly moist spring to summer; reduce in winter. Avoid moving it, leaf drop is common after a move."),
    ("Fiddle Leaf Fig", "Ficus lyrata", "Bright indirect", 10, "Statement foliage", "Sensitive to drafts and inconsistent watering. Water when the top inch is dry; avoid wet feet."),
    ("Calathea", "Calathea spp.", "Bright indirect", 7, "Patterned foliage", "Loves humidity. Use filtered or distilled water to avoid brown tips. Keep soil lightly moist."),
    ("Alocasia", "Alocasia spp.", "Bright indirect", 7, "Statement foliage", "Needs bright indirect light and high humidity. Allow the top soil to dry slightly between waterings."),
    ("Spider Plant", "Chlorophytum comosum", "Bright indirect", 7, "Trailing vines", "Very forgiving. Keep soil evenly moist. Produces offshoots that root easily."),
    ("Boston Fern", "Nephrolepis exaltata", "Bright indirect", 5, "Ferns", "Needs consistent moisture and high humidity. Fronds brown quickly if the air or soil is too dry."),
    ("Dracaena", "Dracaena spp.", "Bright indirect", 12, "Hardy foliage", "Allow the top inch to dry. Sensitive to fluoride; use filtered water if possible."),
    ("Jade Plant", "Crassula ovata", "Bright indirect", 14, "Succulents & drought-tolerant", "Water deeply, then let soil dry fully. Overwatering is the main killer."),
    ("Aloe Vera", "Aloe barbadensis miller", "Direct sun", 21, "Succulents & drought-tolerant", "Extremely drought-tolerant. Water thoroughly, then not again until the soil is bone dry."),
    ("Echeveria", "Echeveria spp.", "Direct sun", 14, "Succulents & drought-tolerant", "Needs bright direct light indoors. Use well-draining cactus mix. Water sparingly in winter."),
    ("Cactus (general)", "Cactaceae family", "Direct sun", 28, "Succulents & drought-tolerant", "Needs maximum direct sun indoors. In winter, water once a month or less."),
    ("String of Pearls", "Senecio rowleyanus", "Bright indirect", 14, "Trailing vines", "Delicate roots rot easily. Let soil dry fully. Bright indirect to some direct sun."),
    ("Anthurium", "Anthurium andraeanum", "Bright indirect", 7, "Flowering", "Blooms repeatedly in good indirect light. Water when the top inch is dry. High humidity prolongs blooms."),
    ("African Violet", "Saintpaulia spp.", "Bright indirect", 7, "Flowering", "Water from below to avoid crown rot. Keep roots lightly moist."),
    ("Orchid (Phalaenopsis)", "Phalaenopsis spp.", "Bright indirect", 10, "Flowering", "Water weekly by soaking roots, then let drain fully. Do not leave in standing water."),
    ("Tradescantia", "Tradescantia zebrina", "Bright indirect", 7, "Foliage", "Fast-growing trailing plant. Keep soil lightly moist; avoid soggy roots."),
]

def watering_tool():
    a = DATA["apps"]["plantlog"]; path = "/tools/houseplant-watering-calculator/"
    plants_js = json.dumps([list(p) for p in PLANT_GUIDE], ensure_ascii=False)
    options = "".join(f'<option value="{i}">{esc(p[0])}</option>' for i, p in enumerate(PLANT_GUIDE))
    table_rows = "".join(
        f'<tr><td><a href="#calc" data-plant="{i}">{esc(p[0])}</a><br><span class="fine"><i>{esc(p[1])}</i></span></td><td>Every {p[3]} days</td><td>{esc(p[2])}</td><td>{esc(p[5])}</td></tr>'
        for i, p in enumerate(PLANT_GUIDE))
    calculator = '''
<div class="fields" id="calc">
<div class="field"><label for="wt-plant">Plant</label><select id="wt-plant">''' + options + '''</select></div>
<div class="field"><label for="wt-last">Last watered</label><input id="wt-last" type="date"></div>
<div class="field"><label for="wt-interval">Days between waterings</label><input id="wt-interval" type="number" min="1" max="90" step="1" inputmode="numeric"><span class="hint" id="wt-suggest"></span></div>
<div class="field"><label for="wt-count">Dates to show</label><select id="wt-count"><option>4</option><option selected>6</option><option>8</option></select></div>
</div>
<div class="actions"><button id="wt-calc" type="button">Build schedule</button><button id="wt-reset" type="button" class="secondary">Use the guide interval</button></div>
<p id="wt-error" class="error" role="alert"></p>
<div id="wt-result" class="result" aria-live="polite">
<span class="eyebrow" id="wt-lead">Next watering</span><strong class="big" id="wt-big">—</strong>
<dl><div><dt>Typical interval</dt><dd id="wt-v1">—</dd></div><div><dt>Light</dt><dd id="wt-v2">—</dd></div><div><dt>Group</dt><dd id="wt-v3">—</dd></div></dl>
<p id="wt-note" style="margin-top:14px;font-size:15px"></p>
<p class="fine" style="margin-top:10px">Upcoming dates</p><ol id="wt-dates" style="margin:6px 0 0 20px;font-weight:600;display:grid;gap:3px"></ol>
</div>
<script>
(()=>{
"use strict";
const PLANTS=''' + plants_js + r''';
const $=s=>document.querySelector(s);
const sel=$("#wt-plant"),last=$("#wt-last"),intv=$("#wt-interval");
function iso(d){return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0")}
function fmt(d){return d.toLocaleDateString(undefined,{weekday:"short",month:"short",day:"numeric"})}
function guide(){return PLANTS[Number(sel.value)]}
function useGuide(){intv.value=guide()[3];run()}
function run(){
 const p=guide(),n=Number(intv.value),count=Number($("#wt-count").value);
 $("#wt-suggest").textContent=`PlantLog's guide says ${p[3]} days for ${p[0]}`;
 if(!(n>=1&&n<=90)){$("#wt-error").textContent="Enter an interval from 1 to 90 days.";return}
 if(!last.value){$("#wt-error").textContent="Enter the date you last watered.";return}
 $("#wt-error").textContent="";
 const [y,m,d]=last.value.split("-").map(Number);const anchor=new Date(y,m-1,d);const today=new Date();today.setHours(0,0,0,0);
 const dates=[];let cur=new Date(anchor);for(let i=0;i<count;i++){cur=new Date(cur.getFullYear(),cur.getMonth(),cur.getDate()+n);dates.push(new Date(cur))}
 const next=dates[0],overdue=next<today;
 $("#wt-lead").textContent=overdue?"Overdue since":"Next watering";$("#wt-big").textContent=fmt(next)+(overdue?"":next.getTime()===today.getTime()?" (today)":"");
 $("#wt-v1").textContent=`Every ${p[3]} days`;$("#wt-v2").textContent=p[2];$("#wt-v3").textContent=p[4];
 $("#wt-note").textContent=p[5];
 $("#wt-dates").innerHTML=dates.map(x=>`<li>${fmt(x)}${x<today?' <span class="fine">(missed)</span>':""}</li>`).join("");
}
last.value=iso(new Date());intv.value=guide()[3];
sel.addEventListener("change",useGuide);[last,intv,$("#wt-count")].forEach(el=>el.addEventListener("input",run));
$("#wt-calc").addEventListener("click",run);$("#wt-reset").addEventListener("click",useGuide);
document.querySelectorAll("[data-plant]").forEach(el=>el.addEventListener("click",()=>{sel.value=el.dataset.plant;useGuide()}));
run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("How often should I water houseplants?", "It depends on the plant: every 5 days for a Boston fern, 7 to 10 for most tropical foliage, 14 for snake plants and ZZ plants, and 3 to 4 weeks for aloe and cacti. The table on this page lists 25 common plants with PlantLog's typical interval for each."),
        ("Should I water on a fixed schedule?", "Use the schedule as a reminder to check, not a command. Push a finger an inch into the soil first: if it is still damp, wait. Pot size, soil mix, light, and season all change how fast soil dries."),
        ("Do plants need less water in winter?", "Usually, yes. Growth slows and soil dries more slowly, so many plants go a week or more longer between waterings. Stretch the interval in the calculator and keep checking the soil."),
        ("How does the calculator pick the next date?", "The same way PlantLog schedules reminders: next due = last watered + interval days. Each following date adds the interval again."),
    ])
    below = f'''
<section><h2>Watering guide for 25 common houseplants</h2><p>Typical days between waterings under average indoor conditions, about 65 to 75°F, moderate humidity. Adjust for your pot, soil, and light. Click a plant to load it into the calculator.</p>
<div style="overflow-x:auto;margin-top:14px"><table class="guide-table" style="width:100%;border-collapse:collapse;font-size:14px"><thead><tr style="text-align:left;border-bottom:2px solid var(--line)"><th style="padding:8px 6px">Plant</th><th style="padding:8px 6px">Water</th><th style="padding:8px 6px">Light</th><th style="padding:8px 6px">Notes</th></tr></thead><tbody>{table_rows}</tbody></table></div>
<style>.guide-table td{{padding:9px 6px;border-bottom:1px solid var(--line);vertical-align:top}}.guide-table td:nth-child(2){{white-space:nowrap;font-weight:600}}</style></section>
<section><h2>How this schedule works</h2><p>The next watering is the last watering plus the interval. That is exactly how PlantLog schedules its reminders. When you tap "watered" in the app the anchor moves, so a late watering pushes the whole schedule rather than piling up missed days.</p><p>Interval data comes from PlantLog's built-in care guide, which the app uses to suggest a schedule when you type a plant name. It is general guidance, not a substitute for looking at your plant.</p></section>
<section><h2>Sources</h2><p>Plant table and scheduling rule copied from PlantLog's care guide and reminder scheduler on September 17, 2026. A printable version of this schedule is on the <a href="/templates/plant-watering-schedule/">plant watering schedule template</a> page.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free houseplant watering calculator: how often to water pothos, monstera, snake plant, fiddle leaf fig, and 21 more, with your next watering dates. Uses PlantLog's care guide."
    ld = tool_ld("Houseplant Watering Schedule Calculator", path, desc, "LifestyleApplication", faq_ld)
    body = tool_shell("plantlog", "Free plant care tool", "How often to water houseplants", "Pick a plant, enter when you last watered, and get the next dates. Intervals come from the care guide inside PlantLog.", calculator, below)
    return page("How Often to Water Houseplants — Watering Schedule Calculator | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-houseplant-watering-calculator.png")

# ---------------------------------------------- 3. sourdough hydration (Banneton)
def hydration_tool():
    a = DATA["apps"]["banneton"]; path = "/tools/sourdough-hydration-calculator/"
    calculator = r'''
<style>.calculator [hidden]{display:none!important}</style>
<div class="fields">
<div class="field wide"><label for="hy-mode">Mode</label><select id="hy-mode"><option value="hydration">Work out my dough's hydration</option><option value="water">How much water for a target hydration</option></select></div>
<div class="field"><label for="hy-flour">Flour in the dough (g)</label><input id="hy-flour" type="number" min="0" step="1" value="500" inputmode="decimal"></div>
<div class="field" id="hy-water-field"><label for="hy-water">Water in the dough (g)</label><input id="hy-water" type="number" min="0" step="1" value="350" inputmode="decimal"></div>
<div class="field" id="hy-target-field" hidden><label for="hy-target">Target hydration (%)</label><input id="hy-target" type="number" min="0" max="150" step="1" value="75" inputmode="decimal"></div>
<div class="field"><label for="hy-levain">Levain / starter added (g)</label><input id="hy-levain" type="number" min="0" step="1" value="100" inputmode="decimal"></div>
<div class="field"><label for="hy-levain-h">Levain hydration (%)</label><input id="hy-levain-h" type="number" min="0" max="200" step="1" value="100" inputmode="decimal"></div>
<div class="field"><label for="hy-salt">Salt (% of total flour)</label><input id="hy-salt" type="number" min="0" max="5" step="0.1" value="2" inputmode="decimal"></div>
</div>
<div class="actions"><button id="hy-calc" type="button">Calculate</button><span class="hint">Levain counts toward flour and water, as in Banneton</span></div>
<p id="hy-error" class="error" role="alert"></p>
<div id="hy-result" class="result" aria-live="polite">
<span class="eyebrow" id="hy-lead">Total dough hydration</span><strong class="big" id="hy-big">—</strong>
<dl><div><dt>Total flour (incl. levain)</dt><dd id="hy-v1">—</dd></div><div><dt>Total water (incl. levain)</dt><dd id="hy-v2">—</dd></div><div><dt>Salt to add</dt><dd id="hy-v3">—</dd></div></dl>
<p class="fine" id="hy-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s),num=id=>Number($(id).value);
// BakersMath, copied from Banneton/Models/Models.swift
function levainSplit(grams,h){if(!(grams>0)||!(h>=0))return null;const flour=grams/(1+h/100);return{flour,water:grams-flour}}
function hydration(flour,water){return flour>0?water/flour*100:null}
function g(x){return Math.round(x)+" g"}
function run(){
 const mode=$("#hy-mode").value;$("#hy-water-field").hidden=mode!=="hydration";$("#hy-target-field").hidden=mode!=="water";
 const f=num("#hy-flour"),lg=num("#hy-levain"),lh=num("#hy-levain-h"),sp=num("#hy-salt");
 if(!(f>0)){$("#hy-error").textContent="Enter the flour weight.";$("#hy-big").textContent="—";return}
 const split=levainSplit(lg,lh)||{flour:0,water:0};const totalFlour=f+split.flour;
 $("#hy-error").textContent="";
 if(mode==="hydration"){
  const w=num("#hy-water");const totalWater=w+split.water;const h=hydration(totalFlour,totalWater);
  $("#hy-lead").textContent="Total dough hydration";$("#hy-big").textContent=h.toFixed(1)+"%";
  $("#hy-v1").textContent=g(totalFlour);$("#hy-v2").textContent=g(totalWater);$("#hy-v3").textContent=g(totalFlour*sp/100)+` (${sp}%)`;
  $("#hy-note").textContent=lg>0?`Your ${lg} g of ${lh}% levain brings ${Math.round(split.flour)} g flour and ${Math.round(split.water)} g water. Without counting it the dough would read ${hydration(f,w).toFixed(1)}%.`:"No levain entered, so hydration is simply water ÷ flour.";
 }else{
  const t=num("#hy-target");if(!(t>=0)){$("#hy-error").textContent="Enter a target hydration.";return}
  const wantWater=totalFlour*t/100;const add=Math.max(0,wantWater-split.water);
  $("#hy-lead").textContent="Water to add";$("#hy-big").textContent=g(add);
  $("#hy-v1").textContent=g(totalFlour);$("#hy-v2").textContent=g(wantWater);$("#hy-v3").textContent=g(totalFlour*sp/100)+` (${sp}%)`;
  $("#hy-note").textContent=lg>0?`Target ${t}% of ${Math.round(totalFlour)} g total flour is ${Math.round(wantWater)} g water; the levain already brings ${Math.round(split.water)} g, so add ${Math.round(add)} g.`:`Target ${t}% of ${Math.round(totalFlour)} g flour is ${Math.round(wantWater)} g water.`;
 }
}
document.querySelectorAll(".calculator input,.calculator select").forEach(el=>el.addEventListener("input",run));$("#hy-mode").addEventListener("change",run);$("#hy-calc").addEventListener("click",run);run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("What is sourdough hydration?", "Water weight divided by flour weight, as a percentage. 350 g water on 500 g flour is 70% hydration. Higher hydration gives a more open crumb but a slacker, harder-to-shape dough."),
        ("Does the levain count toward hydration?", "Yes. A 100%-hydration levain is half flour, half water by weight, so 100 g of it adds 50 g flour and 50 g water to the totals. Leaving it out is the most common reason a recipe's stated hydration doesn't match the dough in the bowl."),
        ("What hydration is good for a beginner?", "Around 65 to 72% is forgiving to shape and still gives a good crumb. Many popular country loaves sit at 75 to 78%. Whole grain and rye flours absorb more water, so the same percentage feels drier."),
        ("How much salt goes in sourdough?", "About 2% of total flour weight is standard. For 600 g total flour that's 12 g. The calculator uses total flour including the flour inside the levain, which is how baker's percentages are defined."),
    ])
    below = f'''
<section><h2>How this calculator works</h2><p>Baker's percentages express every ingredient against total flour. The levain is split into its flour and water parts first: <span class="mono">levainFlour = grams ÷ (1 + hydration/100)</span>, water is the rest. Total flour is dough flour plus levain flour; total water likewise. Hydration is total water ÷ total flour. Salt is a percentage of total flour.</p><p>"How much water" mode does the same in reverse: total flour × target ÷ 100, minus the water the levain already carries.</p></section>
<section><h2>Sources</h2><p>Formulas copied from Banneton's <span class="mono">BakersMath</span> (Models.swift) on September 17, 2026: <span class="mono">hydration</span>, <span class="mono">water(forFlour:targetHydration:)</span>, <span class="mono">levainSplit</span>, and <span class="mono">totalHydration</span>. The multi-flour version, which splits flour into two types, is in the app's advanced calculator.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free sourdough hydration calculator: total dough hydration with the levain counted, water needed for a target hydration, and salt by baker's percentage. Same math as Banneton."
    ld = tool_ld("Sourdough Hydration Calculator", path, desc, "FoodAndDrinkApplication", faq_ld)
    body = tool_shell("banneton", "Free baking tool", "Sourdough hydration calculator", "True dough hydration with the levain counted, or the exact water to hit a target. Salt included.", calculator, below)
    return page("Sourdough Hydration Calculator — Levain Included | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-sourdough-hydration-calculator.png")

# ------------------------------------------------------ 4. reef dosing (Coralog)
def reef_dosing_tool():
    a = DATA["apps"]["coralog"]; path = "/tools/reef-dosing-calculator/"
    # ParameterType.target / driftBand / unit from coralog/Coralog/Models/Models.swift
    params = [("alkalinity", "Alkalinity", "dKH", 8.0, 9.5, 0.5, 1, 0.1, 10),
              ("calcium", "Calcium", "ppm", 400, 450, 25, 1, 2, 10),
              ("magnesium", "Magnesium", "ppm", 1300, 1400, 50, 1, 1, 10)]
    ranges = [("Alkalinity", "8.0 – 9.5 dKH", "±0.5"), ("Calcium", "400 – 450 ppm", "±25"), ("Magnesium", "1300 – 1400 ppm", "±50"),
              ("Nitrate", "2 – 10 ppm", "±5"), ("Phosphate", "0.02 – 0.10 ppm", "±0.05"), ("Salinity", "34 – 35 ppt", "±0.5"),
              ("Temperature", "76 – 80 °F", "±1.5"), ("pH", "7.9 – 8.4", "±0.2")]
    range_rows = "".join(f"<tr><td>{n}</td><td>{r}</td><td>{d}</td></tr>" for n, r, d in ranges)
    params_js = json.dumps({k: {"name": n, "unit": u, "lo": lo, "hi": hi, "band": b, "refMl": rm, "refDelta": rd, "refGal": rg} for k, n, u, lo, hi, b, rm, rd, rg in params})
    calculator = '''
<div class="fields">
<div class="field"><label for="rd-param">Parameter</label><select id="rd-param"><option value="alkalinity">Alkalinity (dKH)</option><option value="calcium">Calcium (ppm)</option><option value="magnesium">Magnesium (ppm)</option></select></div>
<div class="field"><label for="rd-vol">Tank water volume</label><div style="display:flex;gap:8px"><input id="rd-vol" type="number" min="0" step="1" value="75" inputmode="decimal"><select id="rd-vol-unit" style="width:auto"><option value="gal">US gal</option><option value="l">litres</option></select></div></div>
<div class="field"><label for="rd-cur">Current reading</label><input id="rd-cur" type="number" min="0" step="0.1" value="7.6" inputmode="decimal"></div>
<div class="field"><label for="rd-tgt">Target</label><input id="rd-tgt" type="number" min="0" step="0.1" value="8.5" inputmode="decimal"></div>
<div class="field wide"><span class="label">Your additive's label says</span><div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:8px;align-items:center;margin-top:6px"><input id="rd-ref-ml" type="number" min="0" step="0.1" value="1" inputmode="decimal" aria-label="millilitres"><span class="fine">ml raises</span><input id="rd-ref-delta" type="number" min="0" step="0.01" value="0.1" inputmode="decimal" aria-label="amount raised"><span class="fine" id="rd-ref-unit">dKH in</span><input id="rd-ref-gal" type="number" min="0" step="1" value="10" inputmode="decimal" aria-label="reference volume"></div><span class="hint" id="rd-ref-hint">reference volume in US gallons. Copy the dosing line from your product's label.</span></div>
</div>
<div class="actions"><button id="rd-calc" type="button">Calculate dose</button></div>
<p id="rd-error" class="error" role="alert"></p>
<div id="rd-result" class="result" aria-live="polite">
<span class="eyebrow">Dose to add</span><strong class="big" id="rd-big">—</strong>
<dl><div><dt>Change needed</dt><dd id="rd-v1">—</dd></div><div><dt>Current reading is</dt><dd id="rd-v2">—</dd></div><div><dt>Mixed-reef target range</dt><dd id="rd-v3">—</dd></div></dl>
<p class="fine" id="rd-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const P=''' + params_js + r''';
const GAL_PER_L=1/3.785411784;
const $=s=>document.querySelector(s),num=id=>Number($(id).value);
// DosingMath.doseML, copied from Coralog/Features/Dose/DosingCalculator.swift
function doseML(current,target,gallons,refMl,refDelta,refGallons){const delta=target-current;if(!(delta>0&&gallons>0&&refMl>0&&refDelta>0&&refGallons>0))return null;return delta*gallons*refMl/(refDelta*refGallons)}
function state(p,v){if(v>=p.lo&&v<=p.hi)return"in range";if(v>=p.lo-p.band&&v<=p.hi+p.band)return"drifting";return"out of range"}
let lastParam=$("#rd-param").value;
function prefill(){const p=P[$("#rd-param").value];$("#rd-ref-ml").value=p.refMl;$("#rd-ref-delta").value=p.refDelta;$("#rd-ref-gal").value=p.refGal;$("#rd-ref-unit").textContent=p.unit+" in";$("#rd-cur").value=p.lo-p.band/2;$("#rd-tgt").value=((p.lo+p.hi)/2).toFixed(p.unit==="dKH"?1:0);$("#rd-cur").step=$("#rd-tgt").step=p.unit==="dKH"?"0.1":"1"}
function run(){
 const key=$("#rd-param").value,p=P[key];if(key!==lastParam){prefill();lastParam=key}
 const vu=$("#rd-vol-unit").value,vol=num("#rd-vol"),gallons=vu==="l"?vol*GAL_PER_L:vol;
 const refGal=vu==="l"?num("#rd-ref-gal")*GAL_PER_L:num("#rd-ref-gal");$("#rd-ref-hint").textContent=`reference volume in ${vu==="l"?"litres":"US gallons"}. Copy the dosing line from your product's label.`;
 const cur=num("#rd-cur"),tgt=num("#rd-tgt");
 $("#rd-v2").textContent=Number.isFinite(cur)?state(p,cur):"—";$("#rd-v3").textContent=`${p.lo} – ${p.hi} ${p.unit}`;
 if(!(vol>0)){$("#rd-error").textContent="Enter your tank's water volume.";$("#rd-big").textContent="—";return}
 if(!(tgt>cur)){$("#rd-error").textContent="Target must be above the current reading; this calculator only raises a parameter.";$("#rd-big").textContent="—";$("#rd-v1").textContent="—";return}
 const ml=doseML(cur,tgt,gallons,num("#rd-ref-ml"),num("#rd-ref-delta"),refGal);
 if(ml===null){$("#rd-error").textContent="Check the label figures: all three must be above zero.";$("#rd-big").textContent="—";return}
 $("#rd-error").textContent="";const delta=tgt-cur;
 $("#rd-big").textContent=(ml<10?ml.toFixed(1):Math.round(ml))+" ml";$("#rd-v1").textContent=`+${delta.toFixed(p.unit==="dKH"?2:0)} ${p.unit}`;
 let note=`${(tgt-cur).toFixed(2)} ${p.unit} × ${gallons.toFixed(1)} gal × ${num("#rd-ref-ml")} ml ÷ (${num("#rd-ref-delta")} × ${refGal.toFixed(1)} gal).`;
 if(key==="alkalinity"&&delta>1)note+=` That is a jump of more than 1 dKH. A common rule of thumb is to raise alkalinity no faster than about 1 dKH per day, so split this over ${Math.ceil(delta)} days and retest.`;
 if(tgt>p.hi+p.band)note+=` Your target is above the app's default range for a mixed reef.`;
 $("#rd-note").textContent=note;
}
document.querySelectorAll(".calculator input,.calculator select").forEach(el=>el.addEventListener("input",run));$("#rd-param").addEventListener("change",run);$("#rd-calc").addEventListener("click",run);run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("How do I calculate how much alkalinity to dose?", "Take the dosing line on your additive's label, for example 1 ml raises 0.1 dKH in 10 gallons. Dose = (target − current) × your gallons × label ml ÷ (label dKH × label gallons). For a 75 gallon tank going from 7.6 to 8.5 dKH with that label, the dose is 67.5 ml, which the calculator rounds to 68."),
        ("What are good reef tank parameters?", "Coralog's defaults for a mixed reef are alkalinity 8.0 to 9.5 dKH, calcium 400 to 450 ppm, magnesium 1300 to 1400 ppm, nitrate 2 to 10 ppm, phosphate 0.02 to 0.10 ppm, salinity 34 to 35 ppt, temperature 76 to 80°F, and pH 7.9 to 8.4. Stability matters more than any single number."),
        ("How fast can I raise alkalinity?", "A widely used rule of thumb is no more than about 1 dKH per day. Larger corrections should be spread over several days with a retest in between. Calcium and magnesium tolerate bigger steps but the same patience applies."),
        ("Why does the calculator only raise a parameter?", "Additives raise. To bring a value down you dose less or do a water change, which this tool doesn't model. Coralog's dosing calculator has the same guard."),
    ])
    below = f'''
<section><h2>Coralog's default target ranges (mixed reef)</h2><p>The "drift" column is how far outside the range still counts as drifting before the app calls it an alert. You can override every range in the app.</p>
<div style="overflow-x:auto;margin-top:14px"><table class="guide-table" style="width:100%;max-width:520px;border-collapse:collapse;font-size:14px"><thead><tr style="text-align:left;border-bottom:2px solid var(--line)"><th style="padding:8px 6px">Parameter</th><th style="padding:8px 6px">Target</th><th style="padding:8px 6px">Drift band</th></tr></thead><tbody>{range_rows}</tbody></table></div>
<style>.guide-table td{{padding:9px 6px;border-bottom:1px solid var(--line);vertical-align:top}}</style></section>
<section><h2>How the dose is calculated</h2><p>Every additive label states a reference: some millilitres raise a parameter by some amount in some volume. The needed change scales linearly with your tank volume, so <span class="mono">ml = delta × gallons × refMl ÷ (refDelta × refGallons)</span>. Litres are converted to US gallons at 3.785 L per gallon. The prefilled reference numbers are neutral placeholders; replace them with your product's label.</p><p>Use net water volume, not the tank's nominal size. Rock and sand displace a lot; a "75 gallon" system often holds 55 to 65 gallons of water.</p></section>
<section><h2>Sources</h2><p><span class="mono">DosingMath.doseML</span>, the default label references, the target ranges, and the drift bands were copied from Coralog's source on September 17, 2026.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free reef dosing calculator: millilitres of alkalinity, calcium, or magnesium additive to reach a target from your product's label and tank volume, plus mixed-reef target ranges. Same math as Coralog."
    ld = tool_ld("Reef Tank Dosing Calculator", path, desc, "LifestyleApplication", faq_ld)
    body = tool_shell("coralog", "Free reef tool", "Reef dosing calculator", "How many millilitres of alk, calcium, or magnesium additive to reach your target, from the dosing line on the bottle.", calculator, below)
    return page("Reef Dosing Calculator — Alkalinity, Calcium & Magnesium | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-reef-dosing-calculator.png")

# ----------------------------------------------------- 5. reading time (ReadLog)
def reading_time_tool():
    a = DATA["apps"]["readlog"]; path = "/tools/reading-time-calculator/"
    calculator = r'''
<style>.calculator [hidden]{display:none!important}</style>
<div class="fields">
<div class="field wide"><label for="rt-mode">Mode</label><select id="rt-mode"><option value="finish">When will I finish this book?</option><option value="pace">How many pages a day to finish by a date?</option></select></div>
<div class="field"><label for="rt-pages">Pages in the book</label><input id="rt-pages" type="number" min="1" step="1" value="384" inputmode="numeric"></div>
<div class="field"><label for="rt-read">Pages already read</label><input id="rt-read" type="number" min="0" step="1" value="60" inputmode="numeric"></div>
<div class="field" id="rt-pace-field"><label for="rt-pace">Your pace</label><div style="display:flex;gap:8px"><input id="rt-pace" type="number" min="0.1" step="1" value="25" inputmode="decimal"><select id="rt-pace-unit" style="width:auto"><option value="ppd">pages / day</option><option value="mpd">minutes / day</option></select></div></div>
<div class="field" id="rt-speed-field" hidden><label for="rt-speed">Pages you read per hour</label><input id="rt-speed" type="number" min="1" step="1" value="40" inputmode="numeric"><span class="hint">Typical is 30 to 50 for a novel; time yourself on 10 pages to find yours.</span></div>
<div class="field" id="rt-date-field" hidden><label for="rt-date">Finish by</label><input id="rt-date" type="date"></div>
</div>
<div class="actions"><button id="rt-calc" type="button">Calculate</button></div>
<p id="rt-error" class="error" role="alert"></p>
<div id="rt-result" class="result" aria-live="polite">
<span class="eyebrow" id="rt-lead">You'll finish on</span><strong class="big" id="rt-big">—</strong>
<dl><div><dt id="rt-k1">Days to go</dt><dd id="rt-v1">—</dd></div><div><dt id="rt-k2">Pages left</dt><dd id="rt-v2">—</dd></div><div><dt id="rt-k3">Reading time left</dt><dd id="rt-v3">—</dd></div></dl>
<p class="fine" id="rt-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s),num=id=>Number($(id).value);
function fmt(d){return d.toLocaleDateString(undefined,{weekday:"short",month:"long",day:"numeric",year:"numeric"})}
function hrs(pages,pph){const h=pages/pph;return h<1?`${Math.round(h*60)} min`:`${Math.floor(h)} h ${Math.round((h%1)*60)} min`}
function today(){const t=new Date();t.setHours(0,0,0,0);return t}
function run(){
 const mode=$("#rt-mode").value,unit=$("#rt-pace-unit").value;
 $("#rt-pace-field").hidden=mode!=="finish";$("#rt-speed-field").hidden=!(mode==="pace"||unit==="mpd");$("#rt-date-field").hidden=mode!=="pace";
 const pages=num("#rt-pages"),read=num("#rt-read"),pph=num("#rt-speed");
 if(!(pages>0)){$("#rt-error").textContent="Enter the number of pages.";return}
 const left=Math.max(0,pages-read);
 if(left===0){$("#rt-error").textContent="";$("#rt-lead").textContent="Done";$("#rt-big").textContent="Finished!";$("#rt-v1").textContent="0";$("#rt-v2").textContent="0";$("#rt-v3").textContent="0 min";$("#rt-note").textContent="";return}
 if(mode==="finish"){
  let ppd=num("#rt-pace");if(unit==="mpd"){if(!(pph>0)){$("#rt-error").textContent="Enter pages per hour.";return}ppd=ppd/60*pph}
  if(!(ppd>0)){$("#rt-error").textContent="Enter your pace.";return}
  $("#rt-error").textContent="";const days=Math.ceil(left/ppd);const end=today();end.setDate(end.getDate()+days);
  $("#rt-lead").textContent="You'll finish on";$("#rt-big").textContent=fmt(end);
  $("#rt-k1").textContent="Days to go";$("#rt-v1").textContent=String(days);$("#rt-k2").textContent="Pages left";$("#rt-v2").textContent=String(left);
  $("#rt-k3").textContent="Reading time left";$("#rt-v3").textContent=pph>0?hrs(left,pph):"—";
  $("#rt-note").textContent=`${left} pages ÷ ${ppd.toFixed(1)} pages a day = ${(left/ppd).toFixed(1)} days, rounded up. ReadLog measures your pace the same way: pages logged ÷ days elapsed over the last 30 days.`;
 }else{
  const dv=$("#rt-date").value;if(!dv){$("#rt-error").textContent="Pick a finish date.";return}
  const [y,m,d]=dv.split("-").map(Number);const target=new Date(y,m-1,d);const days=Math.round((target-today())/86400000);
  if(days<1){$("#rt-error").textContent="Pick a date after today.";return}
  $("#rt-error").textContent="";const ppd=left/days;
  $("#rt-lead").textContent="Pages per day";$("#rt-big").textContent=(Math.ceil(ppd*10)/10).toString();
  $("#rt-k1").textContent="Days available";$("#rt-v1").textContent=String(days);$("#rt-k2").textContent="Pages left";$("#rt-v2").textContent=String(left);
  $("#rt-k3").textContent="Minutes a day";$("#rt-v3").textContent=pph>0?`about ${Math.ceil(ppd/pph*60)} min`:"—";
  $("#rt-note").textContent=`${left} pages ÷ ${days} days = ${ppd.toFixed(2)} pages a day to finish by ${fmt(target)}.`;
 }
}
const dd=new Date();dd.setDate(dd.getDate()+14);$("#rt-date").value=dd.getFullYear()+"-"+String(dd.getMonth()+1).padStart(2,"0")+"-"+String(dd.getDate()).padStart(2,"0");
document.querySelectorAll(".calculator input,.calculator select").forEach(el=>el.addEventListener("input",run));document.querySelectorAll("#rt-mode,#rt-pace-unit").forEach(el=>el.addEventListener("change",run));$("#rt-calc").addEventListener("click",run);run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("How long does it take to read a 300-page book?", "At 40 pages an hour, a common pace for a novel, about 7.5 hours of reading. At 25 pages a day that's 12 days; at 50 pages a day, 6 days."),
        ("How many pages can the average person read in an hour?", "Roughly 30 to 50 pages of a typical novel, based on an adult silent reading speed of about 200 to 300 words per minute and 250 to 300 words per page. Dense non-fiction is slower. Time yourself on 10 pages for a number that's actually yours."),
        ("How does ReadLog measure my reading pace?", "Pages logged in the last 30 days divided by the days elapsed since your first session in that window, so a new reader isn't understated by a fixed 30-day divisor. This calculator uses the pace you type in."),
        ("How many books a year is 20 pages a day?", "20 pages a day is 7,300 pages a year. At 300 pages a book, that's about 24 books."),
    ])
    below = f'''
<section><h2>How this reading time calculator works</h2><p>Pages left divided by pages per day gives days to finish, rounded up to whole days, and the finish date is today plus that many days. If you know your time rather than your page count, minutes per day × pages per hour ÷ 60 converts it.</p><p>The deadline mode reverses it: pages left ÷ days until the date gives the pace you need, and pages per hour turns that into minutes a day.</p></section>
<section><h2>Sources</h2><p>Pace definition mirrors ReadLog's <span class="mono">pagePacePerDay</span> in ReadingStats.swift (pages ÷ elapsed days, capped at 30), copied September 17, 2026. Typical reading speeds are general figures, not measurements from the app.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free reading time calculator: how many days to finish a book from your pages-per-day pace, the finish date, and the pages a day needed to hit a deadline. Same pace rule as ReadLog."
    ld = tool_ld("Reading Time Calculator", path, desc, "LifestyleApplication", faq_ld)
    body = tool_shell("readlog", "Free reading tool", "Reading time calculator", "When you'll finish the book at your pace, or how many pages a day you need to finish by a date.", calculator, below)
    return page("Reading Time Calculator — How Long to Finish a Book | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-reading-time-calculator.png")

# ------------------------------------------------------ 6. varroa mites (Combwise)
def varroa_tool():
    a = DATA["apps"]["combwise"]; path = "/tools/varroa-mite-calculator/"
    calculator = r'''
<div class="fields">
<div class="field"><label for="vm-mites">Mites counted</label><input id="vm-mites" type="number" min="0" step="1" value="7" inputmode="numeric"></div>
<div class="field"><label for="vm-bees">Bees in the sample</label><input id="vm-bees" type="number" min="1" step="1" value="300" inputmode="numeric"><span class="hint">A level ½ cup of bees is about 300.</span></div>
<div class="field"><label for="vm-method">Method</label><select id="vm-method"><option value="wash">Alcohol wash</option><option value="roll">Sugar roll / shake</option><option value="co2">CO₂ shake</option></select></div>
<div class="field"><label for="vm-threshold">Treatment threshold (mites / 100 bees)</label><input id="vm-threshold" type="number" min="0.1" step="0.1" value="3" inputmode="decimal"><span class="hint">Combwise flags at 3.</span></div>
</div>
<div class="actions"><button id="vm-calc" type="button">Calculate</button></div>
<p id="vm-error" class="error" role="alert"></p>
<div id="vm-result" class="result" aria-live="polite">
<span class="eyebrow">Mite load</span><strong class="big" id="vm-big">—</strong>
<dl><div><dt>Infestation</dt><dd id="vm-v1">—</dd></div><div><dt>Against threshold</dt><dd id="vm-v2">—</dd></div><div><dt>Mites to reach threshold</dt><dd id="vm-v3">—</dd></div></dl>
<p class="fine" id="vm-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s),num=id=>Number($(id).value);
// BeeLogic.varroaNeedsTreatment, copied from Combwise/Models/Models.swift: mitesPer100 >= threshold (3.0)
function run(){
 const mites=num("#vm-mites"),bees=num("#vm-bees"),th=num("#vm-threshold"),method=$("#vm-method").value;
 if(!(bees>0)||!(mites>=0)){$("#vm-error").textContent="Enter the mites counted and the number of bees sampled.";$("#vm-big").textContent="—";return}
 $("#vm-error").textContent="";const per100=mites/bees*100,needs=per100>=th;
 $("#vm-big").textContent=`${per100.toFixed(1)} mites / 100 bees`;$("#vm-v1").textContent=`${per100.toFixed(1)}%`;
 $("#vm-v2").textContent=needs?`At or above ${th} — Combwise would flag this hive`:`Below ${th}`;
 $("#vm-v3").textContent=needs?"—":`${Math.ceil(th*bees/100)} of ${bees}`;
 let note=`${mites} mites ÷ ${bees} bees × 100.`;
 if(method==="roll")note+=" Sugar rolls tend to recover fewer mites than an alcohol wash from the same bees, so treat a borderline result as a reason to re-sample.";
 if(method==="co2")note+=" CO₂ shakes also tend to under-recover slightly compared with an alcohol wash.";
 if(bees<200)note+=" Small samples are noisy; 300 bees (½ cup) is the standard for a readable count.";
 $("#vm-note").textContent=note;
}
document.querySelectorAll(".calculator input,.calculator select").forEach(el=>el.addEventListener("input",run));$("#vm-calc").addEventListener("click",run);run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("How do I calculate mites per 100 bees?", "Divide the mites you counted by the number of bees in the sample and multiply by 100. A level half-cup of bees is about 300, so 9 mites from a half-cup is 3 per 100 bees, or 3%."),
        ("What varroa level needs treatment?", "A widely used action threshold is 3 mites per 100 bees, which is the level Combwise flags. Some guidance uses 2% in spring and 3% later in the season; you can change the threshold in the calculator."),
        ("Alcohol wash or sugar roll?", "An alcohol wash recovers more of the mites present and is the reference method, at the cost of the sampled bees. A sugar roll keeps the bees alive but tends to under-count, so a borderline sugar roll deserves a re-sample."),
        ("Where should I take the sample from?", "From a brood frame, where mites concentrate, after checking the queen isn't on it. A sample from the honey supers will understate the load."),
    ])
    below = f'''
<section><h2>How this calculator works</h2><p>Mite load is reported as mites per 100 bees, which is also the percentage of sampled bees carrying a mite. The number of bees in the sample matters more than people expect: 7 mites is 2.3% from 300 bees but 3.5% from 200. Combwise stores the per-100 figure on every inspection and raises a flag on the hive card when it reaches the threshold.</p></section>
<section><h2>Sources</h2><p>Threshold and comparison rule copied from Combwise's <span class="mono">BeeLogic</span> (Models.swift) on September 17, 2026: <span class="mono">varroaThreshold = 3.0</span>, treat when <span class="mono">mitesPer100 &gt;= threshold</span>. The 300-bees-per-half-cup convention and method notes are standard beekeeping practice rather than app data.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free varroa mite calculator: mites per 100 bees from an alcohol wash or sugar roll, with the 3% treatment flag used by Combwise. Enter mites counted and bees sampled."
    ld = tool_ld("Varroa Mite Count Calculator", path, desc, "LifestyleApplication", faq_ld)
    body = tool_shell("combwise", "Free beekeeping tool", "Varroa mite calculator", "Turn an alcohol wash or sugar roll count into mites per 100 bees, and see whether it crosses the treatment line.", calculator, below)
    return page("Varroa Mite Calculator — Mites per 100 Bees & Treatment Threshold | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-varroa-mite-calculator.png")

# ---------------------------------------------- free tools, batch 3 (2026-09-18)
# Standalone calculators — not mirroring an app's internal Swift code (Boardcut
# doesn't compute these), so each formula is sourced to a public/industry
# reference instead, per the "Sources" section below. All funnel to Boardcut.

def board_feet_tool():
    a = DATA["apps"]["boardcut"]; path = "/tools/board-feet-calculator/"
    calculator = r'''
<style>
.bf-row{display:grid;grid-template-columns:1fr 1fr 1fr 1fr auto;gap:8px;align-items:end}
.bf-row .rlabel{font-size:11px;color:var(--muted);margin-bottom:3px;display:block}
@media(max-width:640px){.bf-row{grid-template-columns:1fr 1fr 1fr;row-gap:8px}.bf-row>button{grid-column:1/-1;justify-self:start;padding:4px 10px}}
</style>
<div class="fields">
<div class="field"><label for="bf-lenunit">Length is in</label><select id="bf-lenunit"><option value="ft">feet</option><option value="in">inches</option></select></div>
<div class="field"><label for="bf-price">Price per board foot ($, optional)</label><input id="bf-price" type="number" min="0" step="0.01" value="6.50" inputmode="decimal"></div>
</div>
<h3 style="margin-top:24px;font-size:15px;font-weight:600">Boards</h3>
<div class="rows" id="bf-rows"></div>
<button type="button" class="secondary" id="bf-add" style="margin-top:10px">+ Add board size</button>
<div class="actions"><button id="bf-calc" type="button">Calculate</button><span class="hint">Nominal (rough-sawn) thickness, actual width &amp; length</span></div>
<p id="bf-error" class="error" role="alert"></p>
<div id="bf-result" class="result" aria-live="polite" hidden>
<span class="eyebrow">Total board feet</span><strong class="big" id="bf-big">0 bf</strong>
<dl><div><dt>Total cost</dt><dd id="bf-cost">—</dd></div><div><dt>Boards</dt><dd id="bf-count">0</dd></div><div><dt>Avg per board</dt><dd id="bf-avg">0 bf</dd></div></dl>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s);
const rowsWrap=$("#bf-rows");
function rowHTML(t,w,l,q){
 return `<div class="bf-row"><div><span class="rlabel">Thickness (in)</span><input class="bf-t" type="number" min="0.01" step="0.0625" value="${t}"></div>`+
 `<div><span class="rlabel">Width (in)</span><input class="bf-w" type="number" min="0.01" step="0.0625" value="${w}"></div>`+
 `<div><span class="rlabel">Length</span><input class="bf-l" type="number" min="0.01" step="0.01" value="${l}"></div>`+
 `<div><span class="rlabel">Qty</span><input class="bf-q" type="number" min="1" step="1" value="${q}"></div>`+
 `<button type="button" class="danger" aria-label="Remove row">&times;</button></div>`;
}
function addRow(t,w,l,q){const d=document.createElement("div");d.innerHTML=rowHTML(t,w,l,q);const row=d.firstElementChild;row.querySelector(".danger").addEventListener("click",()=>{if(rowsWrap.children.length>1){row.remove();run()}});rowsWrap.append(row)}
addRow(1,6,8,4);
addRow(0.75,4,10,6);
$("#bf-add").addEventListener("click",()=>{addRow(1,6,8,1);run()});
function money(x){return x.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}
function run(){
 const err=$("#bf-error"); err.textContent=""; $("#bf-result").hidden=true;
 const lu=$("#bf-lenunit").value, price=Number($("#bf-price").value)||0;
 const rows=[...rowsWrap.children].map(r=>({
  t:Number(r.querySelector(".bf-t").value), w:Number(r.querySelector(".bf-w").value),
  l:Number(r.querySelector(".bf-l").value), q:Math.max(1,Math.round(Number(r.querySelector(".bf-q").value)||1))
 }));
 if(rows.some(r=>!(r.t>0)||!(r.w>0)||!(r.l>0))){err.textContent="Every board needs a thickness, width, and length greater than 0.";return}
 let total=0,count=0;
 rows.forEach(r=>{const lenIn=lu==="ft"?r.l*12:r.l; const bf=(r.t*r.w*lenIn)/144; total+=bf*r.q; count+=r.q});
 $("#bf-big").textContent=`${total.toFixed(2)} bf`;
 $("#bf-cost").textContent=price>0?`$${money(total*price)}`:"—";
 $("#bf-count").textContent=String(count);
 $("#bf-avg").textContent=`${(total/count).toFixed(2)} bf`;
 $("#bf-result").hidden=false;
}
rowsWrap.addEventListener("input",run);
$("#bf-lenunit").addEventListener("change",run);$("#bf-price").addEventListener("input",run);$("#bf-calc").addEventListener("click",run);
run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("What is a board foot?", "A volume unit equal to 144 cubic inches — a board 12 in. long, 12 in. wide, and 1 in. thick. It's the standard unit hardwood is priced and sold by, because hardwood boards vary in width and length in a way that dimensional softwood lumber doesn't."),
        ("What is the board foot formula?", "Thickness (in) × width (in) × length (ft) ÷ 12, or thickness × width × length in inches ÷ 144. This calculator uses actual measured thickness and width, and lets you enter length in feet or inches."),
        ("How many board feet in an 8 ft 2×4?", "A construction 2×4 is nominal — its actual size is 1.5 × 3.5 in. So 1.5 × 3.5 × 8 ÷ 12 = 3.5 board feet, not 8 as the \"2×4\" name might suggest."),
        ("Rough or surfaced (S4S) thickness?", "Hardwood is sold and tallied at its rough-sawn nominal thickness (4/4 = 1 in., 5/4 = 1.25 in., 8/4 = 2 in.), even after it's been planed thinner. Use the nominal thickness here to match a lumberyard quote, or the true thickness if you're estimating your own material."),
    ])
    below = f'''
<section><h2>How this board foot calculator works</h2><p>Each row multiplies thickness × width × length and divides by 144 (or by 12 when length is in feet), then multiplies by quantity. Rows are summed, so you can total a mixed order — a few 4/4 boards and a few 8/4 boards — in one pass.</p><p>This is a volume figure. It says nothing about the shape you can actually cut from a board: two 6-ft boards and one 12-ft board have the same board footage but very different usable lengths. For laying out actual parts against actual stock, use the <a href="/tools/cut-list-optimizer/">cut list optimizer</a> instead.</p></section>
<section><h2>Sources</h2><p>Board foot definition and formula: <a href="https://woodweb.com/knowledge_base/What_is_a_Board_Foot.html">WoodWeb, "What is a Board Foot?"</a>. Nominal 2×4 actual dimensions (1.5 × 3.5 in.) are the standard S4S softwood sizing used throughout North American lumber yards.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free board feet calculator for lumber. Enter thickness, width, and length for as many board sizes as you need, get total board feet and cost. Handles feet or inches."
    ld = tool_ld("Board Feet Calculator", path, desc, "UtilitiesApplication", faq_ld)
    body = tool_shell("boardcut", "Free lumber tool", "Board feet calculator", "Total board feet and cost for a lumber order — thickness × width × length, added up across as many board sizes as you need.", calculator, below)
    return page("Board Feet Calculator — Lumber Volume & Cost | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-board-feet-calculator.png")

def miter_angle_tool():
    a = DATA["apps"]["boardcut"]; path = "/tools/miter-angle-calculator/"
    calculator = r'''
<style>.calculator [hidden]{display:none!important}</style>
<div class="fields">
<div class="field"><label for="ma-corner">Corner angle (degrees)</label><input id="ma-corner" type="number" min="1" max="179" step="0.1" value="90"></div>
<div class="field wide"><label for="ma-type">Trim type</label><select id="ma-type">
<option value="90">Flat trim — baseboard, casing, picture frames (no bevel)</option>
<option value="45">Crown molding, 45&deg; spring (45/45)</option>
<option value="38">Crown molding, 38&deg; spring (52/38)</option>
<option value="52">Crown molding, 52&deg; spring (38/52)</option>
<option value="custom">Custom spring angle</option>
</select></div>
<div class="field" id="ma-custom-field" hidden><label for="ma-custom">Spring angle (degrees)</label><input id="ma-custom" type="number" min="1" max="89" step="0.1" value="45"></div>
</div>
<div class="actions"><button id="ma-calc" type="button">Calculate</button><span class="hint">Cuts laid flat on the saw table (the modern compound-miter method)</span></div>
<p id="ma-error" class="error" role="alert"></p>
<div id="ma-result" class="result" aria-live="polite" hidden>
<span class="eyebrow">Miter angle</span><strong class="big" id="ma-miter">45.00&deg;</strong>
<dl><div><dt>Bevel angle</dt><dd id="ma-bevel">0.00&deg;</dd></div><div><dt>Spring angle used</dt><dd id="ma-spring">90&deg;</dd></div><div><dt>Corner angle</dt><dd id="ma-corner-out">90&deg;</dd></div></dl>
<p class="fine" id="ma-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s);
const typeSel=$("#ma-type"), customField=$("#ma-custom-field");
typeSel.addEventListener("change",()=>{customField.hidden=typeSel.value!=="custom";run()});
function run(){
 const err=$("#ma-error"); err.textContent=""; $("#ma-result").hidden=true;
 const corner=Number($("#ma-corner").value);
 if(!(corner>0)||corner>=180){err.textContent="Enter a corner angle greater than 0 and less than 180 degrees.";return}
 const spring=typeSel.value==="custom"?Number($("#ma-custom").value):Number(typeSel.value);
 if(!(spring>0)||spring>90){err.textContent="Enter a spring angle greater than 0 and up to 90 degrees.";return}
 const rad=d=>d*Math.PI/180, deg=r=>r*180/Math.PI;
 const miter=deg(Math.atan(Math.tan(rad(corner/2))*Math.sin(rad(spring))));
 const bevel=deg(Math.asin(Math.cos(rad(corner/2))*Math.cos(rad(spring))));
 $("#ma-miter").textContent=`${miter.toFixed(2)}°`;
 $("#ma-bevel").textContent=`${bevel.toFixed(2)}°`;
 $("#ma-spring").textContent=`${spring}°`;
 $("#ma-corner-out").textContent=`${corner}°`;
 $("#ma-note").textContent=bevel<0.05?"Bevel is 0° — this is a flat cut with no blade tilt. Set the miter gauge to this angle and cut both pieces, mirrored left and right.":"Set the miter (table rotation) and bevel (blade tilt) to these angles. Cut both mating pieces with the same settings, mirrored left/right so they meet at the corner. Always test-cut scrap first — real corners are rarely exactly square.";
 $("#ma-result").hidden=false;
}
$("#ma-calc").addEventListener("click",run);
document.querySelectorAll("#ma-corner,#ma-custom").forEach(el=>el.addEventListener("input",run));
run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("What is a compound miter cut?", "A cut that combines a miter angle (table rotation) with a bevel angle (blade tilt), needed whenever molding sits at a spring angle against the wall and ceiling instead of lying flat. Crown molding is the common example."),
        ("What is spring angle?", "The angle the back of the molding makes with the wall when installed. The two common crown profiles are 38° spring (labeled 52/38) and 45° spring (labeled 45/45); flat trim like baseboard or a picture frame has no spring angle, so its bevel is always 0°."),
        ("Why is the miter angle for crown molding not just half the corner angle?", "Because the molding is tilted against the wall at the spring angle, the saw doesn't see the room's true corner angle — it sees that angle projected through the spring tilt. Trigonometry corrects for it, which is why 38° crown and 45° crown need different saw settings for the same 90° corner."),
        ("How do I find the actual corner angle?", "Measure it with a digital angle finder or draw the two walls and measure with a protractor — don't assume 90°. Many room corners are a degree or two off, and crown molding is unforgiving of that error."),
    ])
    below = f'''
<section><h2>How this miter angle calculator works</h2><p>For a corner angle <span class="mono">C</span> and a spring angle <span class="mono">S</span>, laid flat on the saw table (the standard modern method, as opposed to holding crown upside-down against the fence):</p><p><span class="mono">miter = atan( tan(C / 2) &times; sin(S) )</span><br><span class="mono">bevel = asin( cos(C / 2) &times; cos(S) )</span></p><p>Flat trim is the special case S = 90&deg;, where <span class="mono">sin(S) = 1</span> and <span class="mono">cos(S) = 0</span> — the formula collapses to <span class="mono">miter = C / 2</span> and <span class="mono">bevel = 0</span>, which is exactly the simple miter rule for baseboard, casing, and picture frames.</p></section>
<section><h2>Sources</h2><p>Formula and worked reference check (90&deg; corner, 38&deg; spring → 31.62&deg; miter, 33.86&deg; bevel, the standard 38/52 crown setting) from <a href="https://starlighttools.org/construction/compound-miter-crown-molding-calculator">Starlight Tools' compound miter crown molding calculator</a> and <a href="https://blog.woodworkingforamateurs.com/compound-miter-cuts-for-crown-molding-the-angle-math-that-actually-works/">"Compound Miter Cuts for Crown Molding: The Angle Math That Actually Works"</a>. Verified against this calculator on September 18, 2026.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free miter angle calculator for crown molding (compound miter + bevel) and flat trim like baseboard or picture frames. Enter a corner angle and spring angle, get the saw settings."
    ld = tool_ld("Miter Angle Calculator", path, desc, "UtilitiesApplication", faq_ld)
    body = tool_shell("boardcut", "Free woodworking tool", "Miter angle calculator", "Miter and bevel angles for crown molding at any spring and corner angle, or a plain miter for baseboard and picture frames.", calculator, below)
    return page("Miter Angle Calculator — Crown Molding Miter & Bevel | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-miter-angle-calculator.png")

# Modulus of elasticity, 12% MC, static bending, 10^6 lbf/in^2 — USDA Forest
# Products Laboratory, Wood Handbook FPL-GTR-190, Table 5-3b (solid species).
# Sheet-good values are typical published figures (EngineeringToolBox), not
# lab-measured per species/grade, and assume face grain parallel to the span.
SHELF_SPECIES = [
    ("solid", "Pine, eastern white", 1.24), ("solid", "Pine, southern yellow (loblolly)", 1.79),
    ("solid", "Douglas fir", 1.95), ("solid", "Poplar, yellow", 1.58),
    ("solid", "Oak, red", 1.82), ("solid", "Oak, white", 1.78),
    ("solid", "Maple, hard (sugar)", 1.83), ("solid", "Maple, soft (red)", 1.64),
    ("solid", "Walnut, black", 1.68), ("solid", "Cherry, black", 1.49),
    ("solid", "Birch, yellow", 2.01), ("solid", "Hickory", 2.16),
    ("solid", "Aspen", 1.18), ("solid", "Basswood", 1.46),
    ("sheet", "Plywood (face grain parallel to span)", 1.50),
    ("sheet", "MDF", 0.50), ("sheet", "Particleboard", 0.45), ("sheet", "OSB", 0.70),
]

def shelf_sag_tool():
    a = DATA["apps"]["boardcut"]; path = "/tools/wood-shelf-sag-calculator/"
    solid_opts = "".join(f'<option value="{e}">{esc(n)} — {e:.2f}</option>' for k,n,e in SHELF_SPECIES if k=="solid")
    sheet_opts = "".join(f'<option value="{e}">{esc(n)} — {e:.2f}</option>' for k,n,e in SHELF_SPECIES if k=="sheet")
    calculator = f'''
<div class="fields">
<div class="field wide"><label for="ss-species">Shelf material (E, million psi)</label><select id="ss-species"><optgroup label="Solid wood">{solid_opts}</optgroup><optgroup label="Sheet goods (typical, varies by grade)">{sheet_opts}</optgroup></select></div>
<div class="field"><label for="ss-span">Span between supports (in)</label><input id="ss-span" type="number" min="1" max="240" step="0.25" value="30"></div>
<div class="field"><label for="ss-depth">Shelf depth, front to back (in)</label><input id="ss-depth" type="number" min="0.5" max="48" step="0.125" value="11.5"></div>
<div class="field"><label for="ss-thick">Shelf thickness (in)</label><input id="ss-thick" type="number" min="0.125" max="4" step="0.0625" value="0.75"></div>
<div class="field"><label for="ss-loadtype">How the load sits</label><select id="ss-loadtype"><option value="uniform">Spread evenly (books, general storage)</option><option value="point">Concentrated at the center (one heavy item)</option></select></div>
<div class="field"><label for="ss-load">Total load on the shelf (lb)</label><input id="ss-load" type="number" min="0.1" step="1" value="40"></div>
</div>
<div class="actions"><button id="ss-calc" type="button">Calculate sag</button></div>
<p id="ss-error" class="error" role="alert"></p>
<div id="ss-result" class="result" aria-live="polite" hidden>
<span class="eyebrow">Initial sag at center</span><strong class="big" id="ss-big">0.00&Prime;</strong>
<dl><div><dt>Sag per foot of span</dt><dd id="ss-perfoot">0.00&Prime;/ft</dd></div><div><dt>Estimated long-term sag</dt><dd id="ss-creep">0.00&Prime;</dd></div><div><dt>Verdict</dt><dd id="ss-verdict">—</dd></div></dl>
<p class="fine" id="ss-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{{
"use strict";
const $=s=>document.querySelector(s);
function run(){{
 const err=$("#ss-error"); err.textContent=""; $("#ss-result").hidden=true;
 const E=Number($("#ss-species").value)*1e6, span=Number($("#ss-span").value), depth=Number($("#ss-depth").value),
       thick=Number($("#ss-thick").value), load=Number($("#ss-load").value), loadType=$("#ss-loadtype").value;
 if(!(span>0)||!(depth>0)||!(thick>0)||!(load>0)){{err.textContent="Enter a span, depth, thickness, and load greater than 0.";return}}
 const I=(depth*Math.pow(thick,3))/12;
 const sag=loadType==="uniform" ? (5*load*Math.pow(span,3))/(384*E*I) : (load*Math.pow(span,3))/(48*E*I);
 const perFoot=sag/(span/12), creep=sag*1.5;
 $("#ss-big").textContent=`${{sag.toFixed(3)}}″`;
 $("#ss-perfoot").textContent=`${{perFoot.toFixed(3)}}″/ft`;
 $("#ss-creep").textContent=`${{creep.toFixed(3)}}″ (rule of thumb, +50%)`;
 let verdict, note;
 if(perFoot<=0.02){{verdict="Should read flat";note="At or under 0.02 in. per foot of span, the common engineering guideline for a shelf that won't visibly sag."}}
 else if(perFoot<=0.04){{verdict="Borderline";note="Above the 0.02 in./ft guideline. It may not bother you today, but visible sag (roughly 1/32 in. per foot) often shows up after months of sustained load."}}
 else{{verdict="Will sag visibly";note="Well above the 0.02 in./ft guideline. Use a stiffer species, a thicker shelf, a shorter span, or add a center support or a hardwood edge strip."}}
 $("#ss-verdict").textContent=verdict; $("#ss-note").textContent=note;
 $("#ss-result").hidden=false;
}}
document.querySelectorAll("#ss-species,#ss-span,#ss-depth,#ss-thick,#ss-loadtype,#ss-load").forEach(el=>el.addEventListener("input",run));
$("#ss-calc").addEventListener("click",run);
run();
}})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("How much shelf sag is acceptable?", "A common engineering guideline is 0.02 in. of sag per foot of span or less. Beyond that, sag around 1/32 in. (0.03 in.) per foot starts to look visibly crooked to the eye."),
        ("Does shelf sag get worse over time?", "Yes — wood creeps under sustained load, so a shelf that measures fine on day one typically sags further afterward. A widely used rule of thumb is roughly 50% more sag than the initial elastic deflection this calculator computes."),
        ("Is plywood or solid wood stiffer for a shelf?", "It depends on species and grain direction more than on plywood-vs-solid as a category. This calculator's plywood figure assumes the face grain runs parallel to the span (the stiffest orientation) — grain running across the span is much weaker."),
        ("What's the fastest way to stop a shelf from sagging?", "Shorten the span (add a support) or add thickness — thickness matters a lot, since stiffness scales with thickness cubed. Doubling thickness cuts sag to about an eighth, all else equal."),
    ])
    below = f'''
<section><h2>How this shelf sag calculator works</h2><p>It applies the standard simply-supported beam deflection formulas: for a load spread evenly across the shelf, <span class="mono">sag = 5WL&sup3; / (384EI)</span>; for a load concentrated at the center, <span class="mono">sag = WL&sup3; / (48EI)</span>. <span class="mono">W</span> is the total load in pounds, <span class="mono">L</span> the span in inches, <span class="mono">E</span> the species' modulus of elasticity, and <span class="mono">I = (depth &times; thickness&sup3;) / 12</span> the moment of inertia of the shelf's rectangular cross-section — which is why thickness matters so much more than depth.</p><p>This estimates the shelf itself, not the wall brackets, cleats, or dado joints holding its ends — those can sag or pull loose independently of the wood's own stiffness.</p></section>
<section><h2>Sources</h2><p>Modulus of elasticity for solid species: USDA Forest Products Laboratory, <a href="https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr190/chapter_05.pdf">Wood Handbook: Wood as an Engineering Material (FPL-GTR-190), Chapter 5, Table 5-3b</a> (12% moisture content, static bending). Sheet-good figures: <a href="https://www.engineeringtoolbox.com/timber-mechanical-properties-d_1789.html">Engineering ToolBox, timber &amp; panel mechanical properties</a>. Deflection formulas, the 0.02 in./ft guideline, and the "+50% over time" creep rule of thumb: <a href="https://www.finewoodworking.com/2007/01/05/engineer-shelves-with-the-sagulator">Fine Woodworking, "Engineer Shelves With the Sagulator"</a> and the <a href="https://woodbin.com/calcs/sagulator/">WoodBin Sagulator</a>.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free wood shelf sag calculator (Sagulator-style). Pick a species or sheet good, enter span, depth, thickness and load, get expected sag and whether it's within the usual 0.02in/ft guideline."
    ld = tool_ld("Wood Shelf Sag Calculator", path, desc, "UtilitiesApplication", faq_ld)
    body = tool_shell("boardcut", "Free woodworking tool", "Wood shelf sag calculator", "Estimate how much a shelf will sag from its span, depth, thickness, material, and load, using standard beam deflection formulas.", calculator, below)
    return page("Wood Shelf Sag Calculator — Shelf Deflection Estimator | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-wood-shelf-sag-calculator.png")

# ---------------------------------------------- free tools, batch 4 (2026-09-18)
# Three more tools for apps still without an acquisition page or a tool of
# their own: PawLog (pet age + calorie calculators) and Whetlog (sharpening
# angle calculator). Formulas cite external primary sources (peer-reviewed
# study, veterinary body guidelines, industry references) rather than
# mirroring app-internal logic, matching the board-feet/miter/shelf-sag set.

def pet_age_tool():
    a = DATA["apps"]["pawlog"]; path = "/tools/pet-age-calculator/"
    calculator = r'''
<style>.calculator [hidden]{display:none!important}</style>
<div class="fields">
<div class="field"><label for="pa-species">Pet</label><select id="pa-species"><option value="dog">Dog</option><option value="cat">Cat</option></select></div>
<div class="field"><label for="pa-age">Age (years)</label><input id="pa-age" type="number" min="0" step="0.01" value="3" inputmode="decimal"></div>
</div>
<div class="actions"><button id="pa-calc" type="button">Calculate</button><span class="hint" id="pa-hint">Use a decimal for months — 0.5 is 6 months</span></div>
<p id="pa-error" class="error" role="alert"></p>
<div id="pa-result" class="result" aria-live="polite" hidden>
<span class="eyebrow">In human years</span><strong class="big" id="pa-big">45</strong>
<dl><div><dt>You entered</dt><dd id="pa-age-out">3 years</dd></div><div><dt id="pa-k2">Life stage</dt><dd id="pa-v2">Adult</dd></div><div><dt>Source</dt><dd id="pa-v3">—</dd></div></dl>
<p class="fine" id="pa-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s);
const CAT_PTS=[[0,0],[0.0833,1],[0.1667,2],[0.25,4],[0.3333,6],[0.4167,8],[0.5,10],[0.5833,12],[1,15],[1.5,21],[2,24],[3,28],[4,32],[5,36],[6,40],[7,44],[8,48],[9,52],[10,56],[11,60],[12,64],[13,68],[14,72],[15,76]];
function catHuman(age){
 if(age>=15) return 76+4*(age-15);
 for(let i=1;i<CAT_PTS.length;i++){
  if(age<=CAT_PTS[i][0]){
   const a0=CAT_PTS[i-1][0],h0=CAT_PTS[i-1][1],a1=CAT_PTS[i][0],h1=CAT_PTS[i][1];
   const t=a1===a0?0:(age-a0)/(a1-a0);
   return h0+t*(h1-h0);
  }
 }
 return 76;
}
function catStage(age){
 if(age<0.5834) return "Kitten";
 if(age<3) return "Junior";
 if(age<7) return "Adult";
 if(age<11) return "Mature";
 if(age<15) return "Senior";
 return "Super Senior";
}
function dogHuman(age){ return 16*Math.log(age)+31; }
function run(){
 const err=$("#pa-error"); err.textContent=""; $("#pa-result").hidden=true;
 const species=$("#pa-species").value, age=Number($("#pa-age").value);
 if(!(age>=0)){err.textContent="Enter an age of 0 or more.";return}
 if(species==="dog"){
  if(age<0.15){err.textContent="Enter a dog age of at least 0.15 years (about 8 weeks) — that's the youngest age this formula is validated for.";return}
  const human=dogHuman(age);
  $("#pa-big").textContent=`${Math.round(human)}`;
  $("#pa-age-out").textContent=`${age} years`;
  $("#pa-k2").textContent="Formula";
  $("#pa-v2").textContent="16 × ln(age) + 31";
  $("#pa-v3").textContent="Wang et al., Cell Systems (2020)";
  $("#pa-note").textContent="Based on a DNA-methylation \"epigenetic clock\" built from 104 Labrador retrievers aged 4 weeks to 16 years. The study's own reference points: a 2-year-old dog ≈ 42, an 8-year-old ≈ 64, and a 12-year-old ≈ 71 — close to the 70-year worldwide human life expectancy the authors used to check the senior end of the curve.";
 } else {
  if(!(age>0)){err.textContent="Enter a cat age greater than 0.";return}
  const human=catHuman(age);
  $("#pa-big").textContent=`${Math.round(human)}`;
  $("#pa-age-out").textContent=`${age} years`;
  $("#pa-k2").textContent="Life stage";
  $("#pa-v2").textContent=catStage(age);
  $("#pa-v3").textContent="Int'l Cat Care / AAHA-AAFP (2021)";
  $("#pa-note").textContent="Interpolated from International Cat Care's published age chart (developed with the AAHA and AAFP): 6 months ≈ 10 human years, 1 year ≈ 15, 2 years ≈ 24, then +4 human years per cat year after that.";
 }
 $("#pa-result").hidden=false;
}
$("#pa-species").addEventListener("change",()=>{$("#pa-hint").textContent=$("#pa-species").value==="dog"?"Use a decimal for months — 0.17 is about 2 months. Minimum 0.15 years (8 weeks).":"Use a decimal for months — 0.5 is 6 months.";run()});
$("#pa-age").addEventListener("input",run);
$("#pa-calc").addEventListener("click",run);
run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("What formula converts dog years to human years?", "The most current science-based formula comes from a 2020 study that mapped DNA-methylation changes in dogs onto the same changes in humans: human age = 16 × ln(dog age) + 31. It replaces the old \"first year = 15, second = 9, then 5 per year after\" rule, which the AVMA has since removed from its site."),
        ("Is the cat-years formula the same everywhere?", "This calculator uses International Cat Care's published chart, developed jointly with the American Animal Hospital Association and the American Association of Feline Practitioners: the first year is 15 human years, the second brings the total to 24, and each year after that adds 4."),
        ("Why can't I enter a dog age under 0.15 years?", "The DNA-methylation formula was fit to dogs from about 4 weeks old, but the equation itself only holds up from roughly 8 weeks onward — below that it produces negative, meaningless numbers. For very young puppies, milestone-based charts are more reliable than a single equation."),
        ("Does breed or size change the human-year conversion?", "For dogs, yes in practice — small breeds tend to live longer and age more slowly than giant breeds, something one formula can't capture. The 2020 study's formula is a population average from Labrador retrievers, a medium-large breed, so treat it as a reasonable estimate rather than an exact figure for every breed."),
    ])
    below = f'''
<section><h2>How this pet age calculator works</h2><p>For dogs, it applies the combined function from a 2020 DNA-methylation study: <span class="mono">human age = 16 &times; ln(dog age) + 31</span>. For cats, it linearly interpolates International Cat Care's published age chart — a series of known points (6 months ≈ 10, 1 year ≈ 15, 2 years ≈ 24, then +4 per year) rather than a single formula, since cat aging doesn't follow a clean logarithmic curve the same way.</p></section>
<section><h2>Sources</h2><p>Dog formula and reference points: Wang, T., Ma, J., Hogan, A.N., et al., <a href="https://www.cell.com/cell-systems/fulltext/S2405-4712(20)30203-9">"Quantitative Translation of Dog-to-Human Aging by Conserved Remodeling of the DNA Methylome"</a>, Cell Systems 11 (2020) — formula confirmed from the <a href="https://idekerlab.ucsd.edu/wp-content/uploads/2020/07/Wang_CellSystems2020.pdf">authors' own PDF</a> (combined function, Figure 3D). Cat age chart: <a href="https://icatcare.org/articles/how-to-tell-your-cats-age-in-human-years">International Cat Care, "How to tell your cat's age in human years"</a>, developed with the AAHA and AAFP; life stage boundaries confirmed against the <a href="https://www.aaha.org/wp-content/uploads/globalassets/02-guidelines/feline-life-stage-2021/2021-aaha-aafp-feline-life-stage-guidelines.pdf">2021 AAHA/AAFP Feline Life Stage Guidelines</a>. Fetched September 18, 2026.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free pet age calculator for dogs and cats. Dogs use the 2020 DNA-methylation study formula; cats use International Cat Care's published age chart (with AAHA/AAFP). Get human years and life stage."
    ld = tool_ld("Pet Age Calculator", path, desc, "LifestyleApplication", faq_ld)
    body = tool_shell("pawlog", "Free pet tool", "Pet age calculator", "How old your dog or cat is in human years, using a 2020 DNA-methylation study for dogs and International Cat Care's published chart for cats.", calculator, below)
    return page("Pet Age Calculator — Dog & Cat Years to Human Years | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-pet-age-calculator.png")

def pet_calorie_tool():
    a = DATA["apps"]["pawlog"]; path = "/tools/dog-cat-calorie-calculator/"
    calculator = r'''
<style>.calculator [hidden]{display:none!important}</style>
<div class="fields">
<div class="field"><label for="pc-species">Pet</label><select id="pc-species"><option value="dog">Dog</option><option value="cat">Cat</option></select></div>
<div class="field"><label for="pc-weight">Weight</label><input id="pc-weight" type="number" min="0.1" step="0.1" value="20" inputmode="decimal"></div>
<div class="field"><label for="pc-unit">Unit</label><select id="pc-unit"><option value="kg">kg</option><option value="lb">lb</option></select></div>
<div class="field wide" id="pc-dog-status"><label for="pc-dog-select">Life stage / status</label><select id="pc-dog-select">
<option value="1.6">Adult, neutered or spayed</option>
<option value="1.8">Adult, intact (not neutered/spayed)</option>
<option value="1.4">Adult prone to weight gain, or on a weight-loss plan</option>
<option value="2">Puppy, over 4 months old</option>
<option value="3">Puppy, 4 months or younger</option>
</select></div>
<div class="field wide" id="pc-cat-status" hidden><label for="pc-cat-select">Life stage / status</label><select id="pc-cat-select">
<option value="1.2">Adult, neutered or spayed</option>
<option value="1.4">Adult, intact (not neutered/spayed)</option>
<option value="1">Adult prone to weight gain</option>
<option value="2.5">Kitten</option>
</select></div>
<div class="field"><label for="pc-kcal">Food energy (kcal per cup, optional)</label><input id="pc-kcal" type="number" min="0" step="1" value="" inputmode="decimal" placeholder="e.g. 350"></div>
</div>
<div class="actions"><button id="pc-calc" type="button">Calculate</button><span class="hint">Uses your pet's current healthy weight</span></div>
<p id="pc-error" class="error" role="alert"></p>
<div id="pc-result" class="result" aria-live="polite" hidden>
<span class="eyebrow">Daily calories (MER)</span><strong class="big" id="pc-big">—</strong>
<dl><div><dt>Resting energy (RER)</dt><dd id="pc-rer">—</dd></div><div><dt>Multiplier</dt><dd id="pc-mult">—</dd></div><div><dt>Food needed</dt><dd id="pc-cups">—</dd></div></dl>
<p class="fine" id="pc-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s);
const speciesSel=$("#pc-species");
speciesSel.addEventListener("change",()=>{$("#pc-dog-status").hidden=speciesSel.value!=="dog";$("#pc-cat-status").hidden=speciesSel.value!=="cat";run()});
function run(){
 const err=$("#pc-error"); err.textContent=""; $("#pc-result").hidden=true;
 const w=Number($("#pc-weight").value), unit=$("#pc-unit").value, kcalPerCup=Number($("#pc-kcal").value);
 if(!(w>0)){err.textContent="Enter a weight greater than 0.";return}
 const kg=unit==="lb"?w/2.2046226218:w;
 const species=speciesSel.value;
 const statusSel=species==="dog"?$("#pc-dog-select"):$("#pc-cat-select");
 const mult=Number(statusSel.value), label=statusSel.selectedOptions[0].textContent;
 const rer=70*Math.pow(kg,0.75);
 const mer=rer*mult;
 $("#pc-big").textContent=`${Math.round(mer)} kcal/day`;
 $("#pc-rer").textContent=`${Math.round(rer)} kcal/day`;
 $("#pc-mult").textContent=`${mult}× (${label})`;
 $("#pc-cups").textContent=kcalPerCup>0?`${(mer/kcalPerCup).toFixed(2)} cups/day`:"Enter kcal/cup above for a cups/day estimate";
 $("#pc-note").textContent=`RER = 70 × (weight in kg)^0.75 = 70 × ${kg.toFixed(2)}kg^0.75. MER = RER × ${mult} for "${label.toLowerCase()}". Treat this as a starting point — adjust from your pet's actual body condition, and check with a vet for weight-loss or medical diets.`;
 $("#pc-result").hidden=false;
}
$("#pc-weight").addEventListener("input",run);$("#pc-unit").addEventListener("input",run);$("#pc-kcal").addEventListener("input",run);
$("#pc-dog-select").addEventListener("input",run);$("#pc-cat-select").addEventListener("input",run);
$("#pc-calc").addEventListener("click",run);
run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("What is RER and MER?", "RER (Resting Energy Requirement) is the calories a pet burns at complete rest — base metabolism only. MER (Maintenance Energy Requirement) multiplies RER by a life-stage and activity factor to estimate typical daily need."),
        ("Why does neutering lower the calorie estimate?", "Neutered pets tend to run a lower metabolic rate, so veterinary references use a smaller multiplier — 1.6× RER for dogs and 1.2× for cats — than for intact adults, at 1.8× and 1.4×."),
        ("How much food is that in cups?", "Enter your food's energy density (kcal per cup — check the bag or the manufacturer's site for \"metabolizable energy\" or \"kcal/cup\") and the calculator divides your daily calories by it."),
        ("Should I trust this over my vet or the bag's feeding chart?", "Use it as a starting point, not a prescription. Bag feeding charts often run high because they assume an average, unneutered, moderately active pet — actual needs vary a good deal between individuals at the same weight. Weigh your pet periodically and adjust the amount you feed."),
    ])
    below = f'''
<section><h2>How this calorie calculator works</h2><p><span class="mono">RER = 70 &times; (weight in kg)<sup>0.75</sup></span> is the standard veterinary formula for resting energy, valid at any body weight. <span class="mono">MER = RER &times; multiplier</span>, where the multiplier depends on life stage and reproductive status — from 1.0&times; for a cat prone to weight gain up to 3&times; for a puppy under 4 months old.</p></section>
<section><h2>Sources</h2><p>RER formula and the full MER multiplier table (life stage / status &times; RER): <a href="https://www.merckvetmanual.com/management-and-nutrition/nutrition-small-animals/nutritional-requirements-of-small-animals">Merck Veterinary Manual, "Nutritional Requirements of Small Animals"</a>, the standard veterinary reference, itself drawn from the National Research Council's <em>Nutrient Requirements of Dogs and Cats</em> (2006). Fetched September 18, 2026.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free dog and cat daily calorie calculator (RER/MER). Enter weight, species, and life stage/status to get resting and maintenance energy needs, plus cups/day if you know your food's kcal per cup."
    ld = tool_ld("Dog & Cat Calorie Calculator", path, desc, "LifestyleApplication", faq_ld)
    body = tool_shell("pawlog", "Free pet tool", "Dog & cat calorie calculator", "Daily calorie needs (RER and MER) for a dog or cat, from weight, species, and life stage or status, using the standard veterinary formula.", calculator, below)
    return page("Dog & Cat Calorie Calculator — RER/MER Daily Feeding | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-dog-cat-calorie-calculator.png")

def whetstone_angle_tool():
    a = DATA["apps"]["whetlog"]; path = "/tools/whetstone-angle-calculator/"
    calculator = r'''
<style>.calculator [hidden]{display:none!important}</style>
<div class="fields">
<div class="field wide"><label for="wa-mode">Method</label><select id="wa-mode"><option value="freehand">Freehand — prop the spine up</option><option value="guided">Guided rod system</option></select></div>
</div>
<div id="wa-freehand">
<div class="fields" style="margin-top:16px">
<div class="field"><label for="wa-height">Blade height, edge to spine (mm)</label><input id="wa-height" type="number" min="1" max="200" step="0.5" value="35"></div>
<div class="field wide"><label for="wa-solve">Solve for</label><select id="wa-solve"><option value="lift">Spine lift, for a target angle</option><option value="angle">Angle, from a spine lift I used</option></select></div>
<div class="field" id="wa-anglefield"><label for="wa-angle-preset">Target angle, per side</label><select id="wa-angle-preset">
<option value="10">10&deg; — very acute (Japanese single-bevel)</option>
<option value="12">12&deg; — Japanese double-bevel, fine</option>
<option value="15" selected>15&deg; — Japanese double-bevel, standard</option>
<option value="18">18&deg; — Western kitchen knife</option>
<option value="20">20&deg; — Western kitchen / EDC</option>
<option value="25">25&deg; — outdoor / heavy-use knife</option>
<option value="custom">Custom</option>
</select></div>
<div class="field" id="wa-anglecustom" hidden><label for="wa-angle-custom">Custom angle, per side (&deg;)</label><input id="wa-angle-custom" type="number" min="1" max="45" step="0.1" value="15"></div>
<div class="field" id="wa-liftfield" hidden><label for="wa-lift">Spine lift you used (mm)</label><input id="wa-lift" type="number" min="0" step="0.1" value="9"></div>
</div>
</div>
<div id="wa-guided" hidden>
<div class="fields" style="margin-top:16px">
<div class="field"><label for="wa-rod">Rod / spacer height (mm)</label><input id="wa-rod" type="number" min="0.1" step="0.1" value="50"></div>
<div class="field"><label for="wa-dist">Horizontal distance, edge to rod (mm)</label><input id="wa-dist" type="number" min="1" step="1" value="200"></div>
</div>
</div>
<div class="actions"><button id="wa-calc" type="button">Calculate</button></div>
<p id="wa-error" class="error" role="alert"></p>
<div id="wa-result" class="result" aria-live="polite" hidden>
<span class="eyebrow" id="wa-lead">Per-side angle</span><strong class="big" id="wa-big">15.00&deg;</strong>
<dl><div><dt>Per-side angle</dt><dd id="wa-v1">15.00&deg;</dd></div><div><dt>Inclusive edge angle</dt><dd id="wa-v2">30.00&deg;</dd></div><div><dt id="wa-k3">Spine lift</dt><dd id="wa-v3">9.06mm</dd></div></dl>
<p class="fine" id="wa-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s);
const modeSel=$("#wa-mode"), solveSel=$("#wa-solve"), anglePreset=$("#wa-angle-preset");
function syncVisibility(){
 const mode=modeSel.value;
 $("#wa-freehand").hidden = mode!=="freehand";
 $("#wa-guided").hidden = mode!=="guided";
 const solve=solveSel.value;
 $("#wa-anglefield").hidden = solve!=="lift";
 $("#wa-anglecustom").hidden = !(solve==="lift" && anglePreset.value==="custom");
 $("#wa-liftfield").hidden = solve!=="angle";
}
modeSel.addEventListener("change",()=>{syncVisibility();run()});
solveSel.addEventListener("change",()=>{syncVisibility();run()});
anglePreset.addEventListener("change",()=>{syncVisibility();run()});
function run(){
 syncVisibility();
 const err=$("#wa-error"); err.textContent=""; $("#wa-result").hidden=true;
 const mode=modeSel.value;
 const rad=d=>d*Math.PI/180, deg=r=>r*180/Math.PI;
 if(mode==="freehand"){
  const height=Number($("#wa-height").value);
  if(!(height>0)){err.textContent="Enter a blade height greater than 0.";return}
  const solve=solveSel.value;
  let angle, lift;
  if(solve==="lift"){
   angle = anglePreset.value==="custom" ? Number($("#wa-angle-custom").value) : Number(anglePreset.value);
   if(!(angle>0)||angle>=90){err.textContent="Enter an angle greater than 0 and less than 90 degrees.";return}
   lift = height*Math.sin(rad(angle));
   $("#wa-lead").textContent="Spine lift";
   $("#wa-big").textContent=`${lift.toFixed(2)}mm`;
  } else {
   lift = Number($("#wa-lift").value);
   if(!(lift>0)||lift>height){err.textContent="Enter a spine lift greater than 0 and no more than the blade height.";return}
   angle = deg(Math.asin(lift/height));
   $("#wa-lead").textContent="Per-side angle";
   $("#wa-big").textContent=`${angle.toFixed(2)}°`;
  }
  $("#wa-v1").textContent=`${angle.toFixed(2)}°`;
  $("#wa-v2").textContent=`${(angle*2).toFixed(2)}°`;
  $("#wa-k3").textContent="Spine lift";
  $("#wa-v3").textContent=`${lift.toFixed(2)}mm`;
  $("#wa-note").textContent=`Prop the spine up ${lift.toFixed(1)}mm above the stone (stacked coins, a stack of cards, or an angle guide) and hold that height through every stroke. Blade height measured ${height}mm, edge to spine.`;
 } else {
  const rod=Number($("#wa-rod").value), dist=Number($("#wa-dist").value);
  if(!(rod>0)){err.textContent="Enter a rod or spacer height greater than 0.";return}
  if(!(dist>0)){err.textContent="Enter a horizontal distance greater than 0.";return}
  const angle=deg(Math.atan(rod/dist));
  $("#wa-lead").textContent="Per-side angle";
  $("#wa-big").textContent=`${angle.toFixed(2)}°`;
  $("#wa-v1").textContent=`${angle.toFixed(2)}°`;
  $("#wa-v2").textContent=`${(angle*2).toFixed(2)}°`;
  $("#wa-k3").textContent="Rod height : distance";
  $("#wa-v3").textContent=`${rod}mm : ${dist}mm`;
  $("#wa-note").textContent="Guided-rod angle = atan(rod height ÷ horizontal distance from the edge to the rod). Move the clamp further from the rod, or use a shorter rod, to shallow the angle.";
 }
 $("#wa-result").hidden=false;
}
document.querySelectorAll("#wa-height,#wa-angle-custom,#wa-lift,#wa-rod,#wa-dist").forEach(el=>el.addEventListener("input",run));
$("#wa-calc").addEventListener("click",run);
syncVisibility();run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("What's the easiest way to set a consistent sharpening angle without a jig?", "Measure your blade's height from edge to spine, multiply by the sine of your target angle, and that's how high to prop the spine off the stone — with two stacked coins, a stack of playing cards, or a wedge. Hold that height through every stroke."),
        ("Why do Japanese knives use a shallower angle than Western knives?", "Japanese kitchen knives typically run harder steel (often 60+ HRC) that can hold a thinner, more acute edge without chipping in normal kitchen use. Western knives use softer, tougher steel that needs more metal behind the edge to survive, hence the wider angle."),
        ("How does a guided (fixed-angle) sharpening system set its angle?", "The angle is the arctangent of the rod or spacer height divided by the horizontal distance from the blade's clamped edge to that rod. Raising the rod, or clamping the blade closer to it, steepens the angle."),
        ("Is spine lift the same as bevel width?", "No. Spine lift is how far you raise the knife's back off the stone to hit an angle; bevel width is how wide the resulting ground facet looks on the blade, which depends on the angle and the edge's thickness, not on spine lift directly."),
    ])
    below = f'''
<section><h2>How this whetstone angle calculator works</h2><p>Freehand mode uses the trigonometric relationship between a blade's height and the sharpening angle: <span class="mono">spine lift = blade height &times; sin(angle)</span>, and its inverse, <span class="mono">angle = asin(spine lift / blade height)</span>. Guided-rod mode uses <span class="mono">angle = atan(rod height / horizontal distance)</span>, the geometry of a fixed pivot and a spacer under one end of a straight guide rod. Both modes report the per-side angle (what you set on one face) and the inclusive angle (both sides combined, what you'd measure across the finished edge).</p></section>
<section><h2>Sources</h2><p>Spine-lift formula and worked check (50mm blade at 15&deg; needs 12.94mm of lift): <a href="https://www.knivesandtools.com/en/ct/find-the-correct-sharpening-angle-in-three-steps.htm">Knivesandtools, "Find the correct sharpening angle in three steps"</a>. Typical angle ranges (about 15&deg; per side for Japanese double-bevel knives, 18&ndash;20&deg; for Western): the same source and <a href="https://us.santokuknives.co.uk/blogs/blog/how-to-use-a-whetstone-angle-guide">Santoku Knives, "How to Use a Whetstone Angle Guide"</a>. Guided-rod formula and worked check (0.4cm spacer at 19cm gives 1.21&deg;, at 9.5cm gives 2.41&deg;): <a href="https://www.bladeforums.com/threads/trigonometry.369442/">BladeForums, "Trigonometry"</a>. Verified against this calculator on September 18, 2026.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free whetstone sharpening angle calculator. Freehand mode converts blade height and target angle to spine-lift height (or back). Guided-rod mode converts rod height and clamp distance to angle."
    ld = tool_ld("Whetstone Angle Calculator", path, desc, "UtilitiesApplication", faq_ld)
    body = tool_shell("whetlog", "Free sharpening tool", "Whetstone angle calculator", "Spine-lift height for a target sharpening angle (or the angle for a lift you used), freehand or on a guided rod system.", calculator, below)
    return page("Whetstone Angle Calculator — Sharpening Angle & Spine Lift | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-whetstone-angle-calculator.png")

def wallpaper_roll_tool():
    path = "/tools/wallpaper-roll-calculator/"
    calculator = r'''
<style>.calculator [hidden]{display:none!important}</style>
<div class="fields">
<div class="field wide"><label for="wr-units">Units</label><select id="wr-units"><option value="metric" selected>Metric (m / cm)</option><option value="imperial">Imperial (ft / in)</option></select></div>
<div class="field wide"><label for="wr-width" id="wr-width-label">Total wall width, all walls added together (m)</label><input id="wr-width" type="number" min="0" step="0.01" value="12" data-kind="length"></div>
<div class="field"><label for="wr-height" id="wr-height-label">Wall height / ceiling drop (m)</label><input id="wr-height" type="number" min="0" step="0.01" value="2.4" data-kind="length"></div>
<div class="field"><label for="wr-repeat" id="wr-repeat-label">Pattern repeat, 0 for none (cm)</label><input id="wr-repeat" type="number" min="0" step="0.1" value="0" data-kind="short"></div>
<div class="field"><label for="wr-doors">Doors</label><input id="wr-doors" type="number" min="0" max="20" step="1" value="0"></div>
<div class="field"><label for="wr-windows">Windows</label><input id="wr-windows" type="number" min="0" max="20" step="1" value="0"></div>
<div class="field wide"><label for="wr-preset">Roll size</label><select id="wr-preset"><option value="european" selected>European roll — 53cm &times; 10m</option><option value="us">US roll/bolt — 20.5in &times; 33ft</option><option value="custom">Custom</option></select></div>
<div class="field"><label for="wr-rollwidth" id="wr-rollwidth-label">Roll width (cm)</label><input id="wr-rollwidth" type="number" min="0.1" step="0.1" value="53" data-kind="short"></div>
<div class="field"><label for="wr-rolllength" id="wr-rolllength-label">Roll length (m)</label><input id="wr-rolllength" type="number" min="0.1" step="0.1" value="10" data-kind="length"></div>
<div class="field"><label for="wr-waste">Waste / buffer</label><select id="wr-waste"><option value="0">0%</option><option value="0.05">5%</option><option value="0.10" selected>10%</option><option value="0.15">15%</option><option value="0.20">20%</option><option value="0.25">25%</option><option value="0.30">30%</option></select></div>
<div class="field"><label for="wr-price">Price per roll ($, optional)</label><input id="wr-price" type="number" min="0" step="0.01" placeholder="0.00"></div>
</div>
<div class="actions"><button id="wr-calc" type="button">Calculate</button><span class="hint">Updates as you type</span></div>
<p id="wr-error" class="error" role="alert"></p>
<div id="wr-result" class="result" aria-live="polite" hidden>
<span class="eyebrow">Rolls needed</span><strong class="big" id="wr-big">6 rolls</strong>
<dl>
<div><dt>Strips needed</dt><dd id="wr-v1">23</dd></div>
<div><dt>Strip length</dt><dd id="wr-v2">2.50 m</dd></div>
<div><dt>Strips per roll</dt><dd id="wr-v3">4</dd></div>
<div><dt>Rolls before buffer</dt><dd id="wr-v4">6</dd></div>
<div><dt>Total cost</dt><dd id="wr-v5">—</dd></div>
</dl>
<p class="fine" id="wr-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s);
const MM_PER_M=1000, MM_PER_FT=304.8, MM_PER_CM=10, MM_PER_IN=25.4;
const TRIM_MM=100, OPENING_MM=700;
const PRESETS={european:{widthMM:530, lengthMM:10000}, us:{widthMM:520.7, lengthMM:10058.4}};
const LABELS={
 metric:{width:"Total wall width, all walls added together (m)", height:"Wall height / ceiling drop (m)", repeat:"Pattern repeat, 0 for none (cm)", rollwidth:"Roll width (cm)", rolllength:"Roll length (m)"},
 imperial:{width:"Total wall width, all walls added together (ft)", height:"Wall height / ceiling drop (ft)", repeat:"Pattern repeat, 0 for none (in)", rollwidth:"Roll width (in)", rolllength:"Roll length (ft)"}
};
let currentUnit="metric";
function toMM(v,kind,unit){if(kind==="length")return unit==="metric"?v*MM_PER_M:v*MM_PER_FT;return unit==="metric"?v*MM_PER_CM:v*MM_PER_IN}
function fromMM(mm,kind,unit){if(kind==="length")return unit==="metric"?mm/MM_PER_M:mm/MM_PER_FT;return unit==="metric"?mm/MM_PER_CM:mm/MM_PER_IN}
function round2(v){return Math.round(v*100)/100}
function fmtLen(mm,unit){return unit==="metric"?`${round2(mm/MM_PER_M).toFixed(2)} m`:`${round2(mm/MM_PER_FT).toFixed(2)} ft`}
function relabel(){
 const L=LABELS[currentUnit];
 $("#wr-width-label").textContent=L.width; $("#wr-height-label").textContent=L.height;
 $("#wr-repeat-label").textContent=L.repeat; $("#wr-rollwidth-label").textContent=L.rollwidth;
 $("#wr-rolllength-label").textContent=L.rolllength;
}
function applyPreset(){
 const preset=$("#wr-preset").value; if(preset==="custom")return;
 const p=PRESETS[preset];
 $("#wr-rollwidth").value=round2(fromMM(p.widthMM,"short",currentUnit));
 $("#wr-rolllength").value=round2(fromMM(p.lengthMM,"length",currentUnit));
}
function convertOnUnitChange(newUnit){
 const oldUnit=currentUnit; if(newUnit===oldUnit)return;
 const custom=$("#wr-preset").value==="custom";
 const ids=custom?["wr-width","wr-height","wr-repeat","wr-rollwidth","wr-rolllength"]:["wr-width","wr-height","wr-repeat"];
 ids.forEach(id=>{
  const el=$("#"+id), kind=el.dataset.kind, v=Number(el.value);
  if(!(v>=0))return;
  el.value=round2(fromMM(toMM(v,kind,oldUnit),kind,newUnit));
 });
 currentUnit=newUnit; relabel();
 if(!custom)applyPreset();
}
function run(){
 const err=$("#wr-error"); err.textContent=""; $("#wr-result").hidden=true;
 const unit=currentUnit;
 const widthMM=toMM(Number($("#wr-width").value),"length",unit);
 const heightMM=toMM(Number($("#wr-height").value),"length",unit);
 const repeatMM=Math.max(0,toMM(Number($("#wr-repeat").value)||0,"short",unit));
 const doors=Math.max(0,Math.round(Number($("#wr-doors").value)||0));
 const windows=Math.max(0,Math.round(Number($("#wr-windows").value)||0));
 const rollWidthMM=toMM(Number($("#wr-rollwidth").value),"short",unit);
 const rollLengthMM=toMM(Number($("#wr-rolllength").value),"length",unit);
 const waste=Math.max(0,Number($("#wr-waste").value));
 const priceRaw=$("#wr-price").value.trim();
 const price=priceRaw!==""&&Number(priceRaw)>0?Number(priceRaw):null;
 if(!(widthMM>0)){err.textContent="Enter a total wall width greater than 0.";return}
 if(!(heightMM>0)){err.textContent="Enter a wall height greater than 0.";return}
 if(!(rollWidthMM>0)||!(rollLengthMM>0)){err.textContent="Enter a roll width and roll length greater than 0.";return}
 let stripLength=heightMM+TRIM_MM;
 if(repeatMM>0)stripLength=Math.ceil(stripLength/repeatMM)*repeatMM;
 const stripsPerRoll=Math.max(1,Math.floor(rollLengthMM/stripLength));
 const openingRelief=(doors+windows)*OPENING_MM;
 const paperableWidth=Math.max(0,widthMM-openingRelief);
 if(!(paperableWidth>0)){err.textContent="Doors and windows remove more width than your total wall width. Reduce the opening count or check the wall width.";return}
 const stripsNeeded=Math.ceil(paperableWidth/rollWidthMM);
 const rollsBeforeWaste=Math.ceil(stripsNeeded/stripsPerRoll);
 const rollsNeeded=waste>0?Math.ceil(rollsBeforeWaste*(1+waste)):rollsBeforeWaste;
 const totalCost=price!=null?rollsNeeded*price:null;
 $("#wr-big").textContent=`${rollsNeeded} roll${rollsNeeded===1?"":"s"}`;
 $("#wr-v1").textContent=String(stripsNeeded);
 $("#wr-v2").textContent=fmtLen(stripLength,unit);
 $("#wr-v3").textContent=String(stripsPerRoll);
 $("#wr-v4").textContent=String(rollsBeforeWaste);
 $("#wr-v5").textContent=totalCost!=null?`$${totalCost.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`:"—";
 $("#wr-note").textContent=`${stripsNeeded} strip${stripsNeeded===1?"":"s"} at ${fmtLen(stripLength,unit)} each, ${stripsPerRoll} per roll.`+(waste>0?` A ${Math.round(waste*100)}% buffer rounds ${rollsBeforeWaste} up to ${rollsNeeded}.`:" No waste buffer applied.");
 $("#wr-result").hidden=false;
}
$("#wr-units").addEventListener("change",e=>{convertOnUnitChange(e.target.value);run()});
$("#wr-preset").addEventListener("change",()=>{applyPreset();run()});
document.querySelectorAll("#wr-width,#wr-height,#wr-repeat,#wr-doors,#wr-windows,#wr-rollwidth,#wr-rolllength,#wr-waste,#wr-price").forEach(el=>el.addEventListener("input",run));
$("#wr-calc").addEventListener("click",run);
relabel();run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("How many rolls of wallpaper do I need for a room?", "Add up the width of every wall you're papering, divide by the roll width to get the number of strips, then divide the strips by how many strip-lengths fit in one roll (your ceiling height plus a trim allowance). Round each step up to a whole strip and a whole roll — you can't buy a fraction of either."),
        ("What's the difference between a \"single roll\" and a \"double roll\"?", "In the US, wallpaper is usually shipped as a bolt about 33 feet long — physically two old-style single rolls joined together — but many retailers still price and list it per \"single roll,\" even though what arrives is one double-roll bolt. Always check the roll dimensions printed on the label rather than assuming from the name."),
        ("How much extra wallpaper should I buy for waste?", "About 10% is standard for a plain or small-pattern wallpaper. A large pattern repeat pushes real-world waste higher because more of each strip gets trimmed to keep the pattern aligned, so 15–20% is a more realistic buffer once the repeat is over about 25–26cm (10in)."),
        ("Does a pattern repeat change how much wallpaper I need?", "Yes. Every strip has to be cut long enough to land on a full repeat, so the strip length gets rounded up to the next multiple of the repeat — which can also reduce how many strips fit in one roll. A 640mm repeat on a 2.4m wall, for example, rounds a 2.5m strip up to 2.56m."),
    ])
    below = f'''
<section><h2>How this wallpaper roll calculator works</h2><p>This is the standard strip method used by wallpaper retailers' own calculators: total wall width &divide; roll width gives the number of strips; wall height plus a fixed trim allowance (100mm, about 4 inches, for top and bottom slack) gives the length of one strip, rounded up to the next full pattern repeat if you set one; how many of those strips fit in one roll (rounded down) gives strips per roll; strips needed &divide; strips per roll, rounded up, gives rolls before any buffer. Each door or window then removes a flat width credit (700mm / 27.5in per opening) from the paperable wall width before the strip count is worked out — a conservative floor that only credits whole strips an opening fully covers, never a fractional strip. The waste buffer you choose is applied last and is always rounded up to a whole roll, never a fraction of one.</p></section>
<section><h2>Sources</h2><p>Strip-method formula (perimeter &divide; roll width = strips; height + trim = strip length; strips &times; strip length &divide; roll length = rolls) and the 10% plain-pattern / 15&ndash;20% large-repeat waste guidance: <a href="https://www.wallcover.com/blog/wallpaper-roll-calculation">Wallcover, "Wallpaper Roll Calculator: How Many Rolls Do You Need?"</a>. Standard European roll size (0.53m &times; 10m): the same source. US "single roll" vs. double-roll bolt naming: <a href="https://uswalldecor.com/blogs/inspiration/single-roll-vs-double-roll-wallpaper-key-differences-explained">US Wall Decor, "Single Roll vs Double Roll Wallpaper"</a> and <a href="https://www.wallpaperboulevard.com/page/single-vs-double-roll-23.aspx">Wallpaper Boulevard, "Single vs Double Roll"</a>. Coverage and trim allowances vary by manufacturer — always check the figures printed on your roll's label. Verified against this calculator on September 18, 2026.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free wallpaper roll calculator. Enter total wall width, ceiling height, roll size, pattern repeat, and door/window count to get rolls needed, strips per roll, and cost. Metric or imperial."
    ld = tool_ld("Wallpaper Roll Calculator", path, desc, "UtilitiesApplication", faq_ld)
    body = tool_shell_standalone("Free DIY tool", "Wallpaper roll calculator", "How many rolls of wallpaper you need, from wall width, ceiling height, roll size, pattern repeat, and door/window openings — the same strip-method math wallpaper retailers use.", calculator, below)
    return page("Wallpaper Roll Calculator — How Many Rolls Do I Need? | Softgrove", desc, path, body, ld)

def dough_temp_tool():
    a = DATA["apps"]["banneton"]; path = "/tools/dough-temperature-calculator/"
    calculator = r'''
<style>.calculator [hidden]{display:none!important}</style>
<div class="fields">
<div class="field"><label for="dt-unit">Temperature unit</label><select id="dt-unit"><option value="f" selected>&deg;F</option><option value="c">&deg;C</option></select></div>
<div class="field"><label for="dt-preferment">Dough type</label><select id="dt-preferment"><option value="3">Straight dough (no levain/preferment)</option><option value="4" selected>Levain or preferment included</option></select></div>
<div class="field"><label for="dt-ddt">Desired dough temperature</label><input id="dt-ddt" type="number" step="0.1" value="78" inputmode="decimal"></div>
<div class="field"><label for="dt-room">Room temperature</label><input id="dt-room" type="number" step="0.1" value="72" inputmode="decimal"></div>
<div class="field"><label for="dt-flour">Flour temperature</label><input id="dt-flour" type="number" step="0.1" value="71" inputmode="decimal"></div>
<div class="field" id="dt-lev-field"><label for="dt-levain">Levain / preferment temperature</label><input id="dt-levain" type="number" step="0.1" value="76" inputmode="decimal"></div>
<div class="field wide"><label for="dt-friction-preset">Friction factor</label><select id="dt-friction-preset">
<option value="custom">Custom (enter below)</option>
<option value="0">By hand, gentle folding (~0&deg;F / 0&deg;C)</option>
<option value="7" selected>By hand, vigorous kneading, ~8 min (~7&deg;F / 4&deg;C)</option>
<option value="23">Stand mixer, e.g. 7-qt KitchenAid (~23&deg;F / 13&deg;C)</option>
</select></div>
<div class="field"><label for="dt-friction">Friction factor (&deg;)</label><input id="dt-friction" type="number" step="0.1" value="7" inputmode="decimal"></div>
</div>
<div class="actions"><button id="dt-calc" type="button">Calculate</button><span class="hint">Updates as you type</span></div>
<p id="dt-error" class="error" role="alert"></p>
<div id="dt-result" class="result" aria-live="polite" hidden>
<span class="eyebrow">Water temperature to use</span><strong class="big" id="dt-big">&mdash;</strong>
<dl><div><dt>Total temperature factor</dt><dd id="dt-v1">&mdash;</dd></div><div><dt>Multiplier</dt><dd id="dt-v2">&mdash;</dd></div></dl>
<p class="fine" id="dt-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s);
const prefSel=$("#dt-preferment"), levField=$("#dt-lev-field");
function syncPreferment(){levField.hidden=prefSel.value!=="4"}
prefSel.addEventListener("change",()=>{syncPreferment();run()});
$("#dt-friction-preset").addEventListener("change",e=>{if(e.target.value!=="custom")$("#dt-friction").value=e.target.value;run()});
function run(){
 const err=$("#dt-error"); err.textContent=""; $("#dt-result").hidden=true;
 const unit=$("#dt-unit").value;
 const factors=Number(prefSel.value);
 const ddt=Number($("#dt-ddt").value), room=Number($("#dt-room").value), flour=Number($("#dt-flour").value);
 const levain=factors===4?Number($("#dt-levain").value):0;
 const friction=Number($("#dt-friction").value)||0;
 if(![ddt,room,flour,friction].every(Number.isFinite)||(factors===4&&!Number.isFinite(levain))){err.textContent="Enter a number in every temperature field.";return}
 const totalFactor=ddt*factors;
 const known=room+flour+friction+levain;
 const water=totalFactor-known;
 const deg=unit==="f"?"°F":"°C";
 $("#dt-big").textContent=`${water.toFixed(1)}${deg}`;
 $("#dt-v1").textContent=`${ddt} &times; ${factors} = ${totalFactor.toFixed(1)}${deg}`.replace("&times;","×");
 $("#dt-v2").textContent=factors===4?"×4 (room + flour + levain + friction)":"×3 (room + flour + friction)";
 const lowFlag=unit==="f"?(water<32||water>110):(water<0||water>43);
 $("#dt-note").textContent=`Water temp = (DDT × ${factors}) − room − flour${factors===4?" − levain":""} − friction factor = ${totalFactor.toFixed(1)} − ${known.toFixed(1)} = ${water.toFixed(1)}${deg}.`+(lowFlag?" That's outside a normal tap-water range — double-check your inputs, or use ice water / a touch of warm water and adjust by feel.":"");
 $("#dt-result").hidden=false;
}
["dt-ddt","dt-room","dt-flour","dt-levain","dt-friction"].forEach(id=>$("#"+id).addEventListener("input",run));
$("#dt-unit").addEventListener("change",run);
$("#dt-calc").addEventListener("click",run);
syncPreferment();run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("What is desired dough temperature (DDT)?", "The dough temperature you're aiming for right after mixing, because it's the single biggest lever over fermentation speed and, with it, flavor and rise. Most wheat-based yeast breads and sourdoughs target 75–78°F (24–26°C)."),
        ("Why multiply by 3 or by 4?", "The formula assumes final dough temperature is roughly the average of every ingredient's temperature plus the heat mixing adds. Multiplying DDT by the number of factors you're tracking — room, flour, and friction (3), or those plus a levain/preferment (4) — gives a \"total temperature factor\" you can subtract the known temperatures from, leaving the one you control: water."),
        ("What's a friction factor and how do I find mine?", "It's the heat your mixing method adds to the dough — near zero for gentle hand folding, a few degrees for vigorous hand kneading, and considerably more from a stand mixer's motor and friction (King Arthur measured roughly 22–24°F / 12–13°C for a 7-quart KitchenAid). To measure your own: mix a batch, take the dough's temperature right after, then solve the same formula backwards — friction factor = (final dough temp × factors) − room − flour − water (− levain if used)."),
        ("The water temperature comes out negative or oddly high — what does that mean?", "It usually means your room or flour is already warmer than needed to hit your DDT, so even ice-cold water can't bring it down (or vice versa in a cold kitchen). Treat that as a sign to adjust DDT slightly, chill your flour, or accept the dough will run a bit off-target rather than chasing an impossible tap temperature."),
    ])
    below = f'''
<section><h2>How this dough temperature calculator works</h2><p>This is the standard baker's Desired Dough Temperature (DDT) formula: multiply your target dough temperature by 3 (room + flour + friction) or by 4 if a levain or other preferment is part of the dough (room + flour + levain + friction), then subtract every temperature you already know. What's left is the water temperature to mix with. <span class="mono">Water = (DDT &times; factors) &minus; room &minus; flour &minus; friction &minus; levain</span>.</p></section>
<section><h2>Sources</h2><p>DDT formula, the &times;3/&times;4 multiplier logic, the 75&ndash;78&deg;F target range, and the worked example (78&deg;F DDT, 72&deg;F room, 71&deg;F flour, 22&deg;F friction factor → 69&deg;F water) verified against: <a href="https://www.kingarthurbaking.com/blog/2018/05/29/desired-dough-temperature">King Arthur Baking, "Desired dough temperature"</a>. Friction factor ranges by mixing method (hand kneading ~6&ndash;8&deg;F / 3&ndash;4&deg;C, gentle hand folding ~0&ndash;4&deg;F, 7-quart KitchenAid stand mixer ~22&ndash;24&deg;F / 12&ndash;13&deg;C) and how to measure your own: <a href="https://www.kingarthurbaking.com/blog/2018/08/27/determining-the-friction-factor-in-baking">King Arthur Baking, "Determining the friction factor in baking"</a>. Fetched September 18, 2026.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free desired dough temperature (DDT) calculator for bread and sourdough. Enter your target dough temperature, room, flour, and levain temperatures to get the water temperature to mix with — the standard ×3/×4 baker's formula."
    ld = tool_ld("Dough Temperature Calculator", path, desc, "FoodAndDrinkApplication", faq_ld)
    body = tool_shell("banneton", "Free sourdough tool", "Dough temperature calculator", "The water temperature to mix with, from your target dough temperature, room and flour temperature, friction factor, and levain temperature if you're using one — the standard baker's DDT formula.", calculator, below)
    return page("Dough Temperature Calculator (DDT) — Water Temp for Bread & Sourdough | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-dough-temperature-calculator.png")

def bee_syrup_tool():
    a = DATA["apps"]["combwise"]; path = "/tools/bee-syrup-calculator/"
    calculator = r'''
<style>.calculator [hidden]{display:none!important}</style>
<div class="fields">
<div class="field wide"><label for="bs-ratio-preset">Syrup ratio (by weight)</label><select id="bs-ratio-preset">
<option value="1">1:1 — light / spring syrup (stimulative feeding)</option>
<option value="2" selected>2:1 — heavy / fall syrup (winter stores)</option>
<option value="custom">Custom ratio</option>
</select></div>
<div class="field" id="bs-custom-field" hidden><label for="bs-ratio-custom">Custom ratio (sugar : 1 water, by weight)</label><input id="bs-ratio-custom" type="number" step="0.1" min="0.1" value="1.5" inputmode="decimal"></div>
<div class="field"><label for="bs-water">Water you're starting with</label><input id="bs-water" type="number" step="0.1" min="0" value="1" inputmode="decimal"></div>
<div class="field"><label for="bs-unit">Unit</label><select id="bs-unit">
<option value="quart" selected>US quarts</option>
<option value="gallon">US gallons</option>
<option value="cup">US cups</option>
<option value="l">Liters</option>
<option value="ml">Milliliters</option>
</select></div>
</div>
<div class="actions"><button id="bs-calc" type="button">Calculate</button><span class="hint">Updates as you type</span></div>
<p id="bs-error" class="error" role="alert"></p>
<div id="bs-result" class="result" aria-live="polite" hidden>
<span class="eyebrow">Sugar to add</span><strong class="big" id="bs-big">&mdash;</strong>
<dl><div><dt>In cups (granulated, approx.)</dt><dd id="bs-cups">&mdash;</dd></div><div><dt>Total finished syrup weight</dt><dd id="bs-total">&mdash;</dd></div></dl>
<p class="fine" id="bs-note" style="margin-top:14px"></p>
</div>
<script>
(()=>{
"use strict";
const $=s=>document.querySelector(s);
const presetSel=$("#bs-ratio-preset"), customField=$("#bs-custom-field");
const UNIT_G={quart:946.353,gallon:3785.41,cup:236.588,l:1000,ml:1};
function syncPreset(){customField.hidden=presetSel.value!=="custom"}
presetSel.addEventListener("change",()=>{syncPreset();run()});
function run(){
 const err=$("#bs-error"); err.textContent=""; $("#bs-result").hidden=true;
 const ratio=presetSel.value==="custom"?Number($("#bs-ratio-custom").value):Number(presetSel.value);
 const amount=Number($("#bs-water").value);
 const unit=$("#bs-unit").value;
 if(!Number.isFinite(ratio)||ratio<=0||!Number.isFinite(amount)||amount<=0){err.textContent="Enter a positive water amount and ratio.";return}
 const waterG=amount*UNIT_G[unit];
 const sugarG=waterG*ratio;
 const totalG=waterG+sugarG;
 const sugarLbTotal=sugarG/453.592;
 const lb=Math.floor(sugarLbTotal);
 const oz=(sugarLbTotal-lb)*16;
 const sugarKg=sugarG/1000;
 $("#bs-big").textContent=`${lb} lb ${oz.toFixed(1)} oz (${sugarKg.toFixed(2)} kg)`;
 $("#bs-cups").textContent=`${(sugarG/200).toFixed(2)} cups`;
 $("#bs-total").textContent=`${(totalG/453.592).toFixed(2)} lb (${(totalG/1000).toFixed(2)} kg)`;
 $("#bs-note").textContent=`${ratio}:1 sugar:water by weight — ${amount} ${unit==="l"?"L":unit==="ml"?"mL":unit+(amount===1?"":"s")} of water (${waterG.toFixed(0)} g) needs ${sugarG.toFixed(0)} g of sugar. Ratios are by weight, not volume — a cup of granulated sugar weighs less than a cup of water, so measuring 2:1 by volume gives a thinner syrup than 2:1 by weight. Use only plain white granulated cane or beet sugar; never brown sugar, molasses, sorghum, powdered sugar, or fruit juice — these can cause bee dysentery.`;
 $("#bs-result").hidden=false;
}
$("#bs-water").addEventListener("input",run);
$("#bs-unit").addEventListener("change",run);
$("#bs-ratio-custom").addEventListener("input",run);
$("#bs-calc").addEventListener("click",run);
syncPreset();run();
})();
</script>'''
    faq_html, faq_ld = tool_faq([
        ("Should sugar syrup ratios be measured by weight or volume?", "By weight. A cup of granulated sugar weighs less than a cup of water, so mixing \"2 cups sugar to 1 cup water\" produces a thinner syrup than a true 2:1 made by weighing both — close enough for small batches, but the gap grows with larger volumes. This calculator works in weight (grams/pounds) and converts to approximate cups so you can check either way."),
        ("When do I use 1:1 vs. 2:1 syrup?", "1:1 (light/spring syrup) is used for stimulative spring feeding — it's thin, close to the concentration of natural nectar, and encourages the queen to ramp up brood rearing. 2:1 (heavy/fall syrup) is used going into fall — it's thick, so bees spend less energy evaporating it before capping, which matters as days get shorter and cooler, and it packs more sugar into the same volume of stores for winter."),
        ("Can I use brown sugar, molasses, or powdered sugar instead of white granulated sugar?", "No. Only plain white granulated cane or beet sugar is safe for bees. Brown sugar, molasses, sorghum, powdered/confectioner's sugar (it contains cornstarch), and fruit juices contain impurities and ash content that bees can't digest well, which can cause dysentery — especially serious in winter when bees can't leave the hive to void."),
        ("How much does a gallon of 2:1 syrup add to a colony's stores?", "Roughly 7 pounds, since the finished syrup is mostly dissolved sugar by weight. That's why 2:1 is the standard choice for building up winter stores in the fall rather than 1:1, which carries less sugar per gallon fed."),
    ])
    below = f'''
<section><h2>How this bee syrup calculator works</h2><p>Beekeeping syrup ratios are defined by weight: 1:1 means one part sugar to one part water by weight, 2:1 means two parts sugar to one part water by weight. This calculator converts your water amount to grams, multiplies by the ratio to get the sugar weight, and also shows an approximate cup measure for granulated sugar (using the standard 200g per cup) since most beekeepers measure by volume in practice.</p></section>
<section><h2>Sources</h2><p>1:1 (light/spring) vs. 2:1 (heavy/fall) ratio definitions, that they are measured by weight, the stimulative-feeding rationale for 1:1, the winter-stores rationale for 2:1, the ~7 lb per gallon stores estimate for 2:1 syrup, and the white-sugar-only safety guidance (no brown sugar, molasses, sorghum, powdered sugar, or fruit juice, due to dysentery risk): <a href="https://www.honeybeesuite.com/sugar-syrup-ratios-which-one-to-use/">Honey Bee Suite, "Sugar syrup ratios: which one to use?"</a>. Seasonal use of 1:1 for spring/stimulative feeding and 2:1 for fall feeding, confirmed by weight, cross-checked against: <a href="https://extension.arizona.edu/sites/default/files/2024-08/az2014-2022.pdf">University of Arizona Cooperative Extension, "Feeding Your Bees"</a> and <a href="https://pollinators.msu.edu/sites/_pollinators/assets/File/FeedingHoneyBees-Final.pdf">Michigan State University Extension, "Feeding Honey Bees"</a>. Fetched September 18, 2026.</p></section>
<section><h2>Questions</h2>{faq_html}</section>
{more_tools(path)}'''
    desc = "Free bee syrup calculator for beekeepers. Enter your water amount and pick 1:1 (spring) or 2:1 (fall) — get the sugar weight to add, by the correct weight-based ratio, plus a cup measure."
    ld = tool_ld("Bee Syrup Calculator", path, desc, "FoodAndDrinkApplication", faq_ld)
    body = tool_shell("combwise", "Free beekeeping tool", "Bee syrup calculator", "How much sugar to add to your water for 1:1 spring syrup or 2:1 fall syrup — the correct weight-based ratio, with a cup measure for convenience.", calculator, below)
    return page("Bee Syrup Calculator — 1:1 & 2:1 Sugar Syrup for Bees | Softgrove", desc, path, body, ld, f'<meta name="apple-itunes-app" content="app-id={a["id"]}">', "/og/tools-bee-syrup-calculator.png")

# ---------------------------------------------------------------- tools hub
def tools_hub():
    cards = ""
    for p, t, d, key in TOOLS_INDEX:
        if key:
            ap = DATA["apps"][key]
            chip, origin = ap["accent"], f'<span class="fine" style="margin-top:6px">From {esc(ap["name"])}</span>'
        else:
            chip, origin = SITE["house_accent"], ""
        cards += (f'<a class="tpl-card" href="{p}"><span class="chip" style="background:{chip}"></span>'
                  f'<strong class="serif">{esc(t)}</strong><span>{esc(d)}</span>{origin}</a>')
    body = f"""
<style>
.hub-hero{{padding:64px 0 30px;max-width:760px}}.hub-hero h1{{font-size:clamp(38px,6vw,60px);margin-top:8px}}
.hub-hero .lede{{font-size:19px;color:#4d4850;margin-top:18px;max-width:60ch}}
.tpl-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin-top:34px}}
.tpl-card{{border:1px solid var(--line);background:#fff;border-radius:10px;padding:19px;text-decoration:none;display:flex;flex-direction:column;gap:7px}}
.tpl-card:hover{{border-color:var(--teal)}}.tpl-card .chip{{width:36px;height:8px;border-radius:4px}}
.tpl-card strong{{font-size:21px;font-weight:500;line-height:1.22}}.tpl-card>span:nth-child(3){{font-size:14px;color:var(--muted)}}
</style>
<main class="wrap">
<header class="hub-hero"><p class="eyebrow">Free web tools</p><h1>Calculators that run in your browser</h1><p class="lede">Each one uses the same logic as the Softgrove app it comes from. No sign-up, nothing installed, nothing sent to a server.</p></header>
<div class="tpl-grid">{cards}</div>
<p class="fine" style="margin-top:40px">Looking for something printable instead? See the <a href="/templates/">free tracker templates</a>.</p>
</main>"""
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "Free web tools", "url": ORIGIN + "/tools/",
          "publisher": {"@type": "Organization", "name": "Softgrove", "url": ORIGIN + "/"}}
    return page("Free Web Calculators — Fuel Cost, Sourdough Hydration, Reef Dosing & More | Softgrove",
                "Seventeen free browser calculators from Softgrove: fuel cost, houseplant watering, sourdough hydration, reef dosing, reading time, varroa mites, film reciprocity, kiln cost, cut list, board feet, miter angle, shelf sag, pet age, pet calories, whetstone angle, wallpaper rolls, dough temperature.",
                "/tools/", body, ld, "", "/og/tools.png")

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
    lines += [f"- [{t}]({ORIGIN}{p}): {d}" for p, t, d, _ in TOOLS_INDEX if p not in ("/tools/reciprocity-calculator/", "/tools/kiln-firing-cost-calculator/", "/tools/cut-list-optimizer/")]
    lines.append(f"- Index of all tools: {ORIGIN}/tools/")
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
             "/tools/cut-list-optimizer/": cutlist_tool(),
             "/tools/": tools_hub(),
             "/tools/fuel-cost-calculator/": fuel_cost_tool(),
             "/tools/houseplant-watering-calculator/": watering_tool(),
             "/tools/sourdough-hydration-calculator/": hydration_tool(),
             "/tools/reef-dosing-calculator/": reef_dosing_tool(),
             "/tools/reading-time-calculator/": reading_time_tool(),
             "/tools/varroa-mite-calculator/": varroa_tool(),
             "/tools/board-feet-calculator/": board_feet_tool(),
             "/tools/miter-angle-calculator/": miter_angle_tool(),
             "/tools/wood-shelf-sag-calculator/": shelf_sag_tool(),
             "/tools/pet-age-calculator/": pet_age_tool(),
             "/tools/dog-cat-calorie-calculator/": pet_calorie_tool(),
             "/tools/whetstone-angle-calculator/": whetstone_angle_tool(),
             "/tools/wallpaper-roll-calculator/": wallpaper_roll_tool(),
             "/tools/dough-temperature-calculator/": dough_temp_tool(),
             "/tools/bee-syrup-calculator/": bee_syrup_tool()}
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
