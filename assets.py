#!/usr/bin/env python3
"""OG images (PNG via headless Chrome screenshot) + printable PDFs (Chrome print-to-pdf).
No PIL/wkhtmltopdf dependency — one renderer for everything."""
import json, subprocess, pathlib, html as htmlmod, tempfile, shutil

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "docs"
DATA = json.loads((ROOT / "apps.json").read_text())
DESCS = json.loads((ROOT / "_asc_descs.json").read_text())
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
esc = lambda s: htmlmod.escape(s)

FONT = ('<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..600&display=swap" rel="stylesheet">')

def og_html(title, sub, chips):
    chip_divs = "".join(f'<div class="chip" style="background:{c}"></div>' for c in chips)
    return f"""<!doctype html><html><head><meta charset="utf-8">{FONT}<style>
body{{margin:0;width:1200px;height:630px;background:#FBFAF7;font-family:-apple-system,sans-serif;
 display:flex;flex-direction:column;justify-content:space-between;padding:72px 84px;box-sizing:border-box}}
.chips{{display:flex;gap:12px}}
.chip{{width:64px;height:16px;border-radius:8px}}
h1{{font-family:"Newsreader",Georgia,serif;font-weight:500;font-size:74px;line-height:1.08;
 letter-spacing:-.015em;color:#2C282C;margin:0;max-width:15ch}}
.foot{{display:flex;justify-content:space-between;align-items:baseline}}
.wm{{font-family:"Newsreader",Georgia,serif;font-weight:600;font-size:34px;color:#2C282C}}
.wm b{{color:#3E8E8C}}
.sub{{font-size:24px;color:#6E6870}}
</style></head><body>
<div class="chips">{chip_divs}</div>
<h1>{esc(title)}</h1>
<div class="foot"><span class="wm">softgrove<b>.</b></span><span class="sub">{esc(sub)}</span></div>
</body></html>"""

def pdf_html(slug):
    t = DATA["templates"][slug]; a = DATA["apps"][t["app"]]
    n = len(t["columns"])
    widths = {6: [11, 30, 17, 10, 14, 18], 5: [11, 15, 15, 37, 22]}.get(n, [round(100 / n)] * n)
    heads = "".join(f'<th style="width:{w}%">{esc(c)}</th>' for c, w in zip(t["columns"], widths))
    rows = "".join("<tr>" + "<td></td>" * n + "</tr>" for _ in range(19 if n == 6 else 21))
    title = t["h1"].replace("Free Printable ", "").replace(" (PDF)", "")
    return f"""<!doctype html><html><head><meta charset="utf-8">{FONT}<style>
@page{{size:letter;margin:0}}
body{{margin:0;padding:44px 48px;font-family:-apple-system,Helvetica,sans-serif;color:#2C282C}}
.head{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:3px solid {a["accent"]};padding-bottom:10px}}
h1{{font-family:"Newsreader",Georgia,serif;font-weight:500;font-size:26px;margin:0}}
.wm{{font-family:"Newsreader",Georgia,serif;font-size:13px;color:#6E6870}}
.meta{{display:flex;gap:36px;margin:12px 0 16px;font-size:11px;color:#6E6870}}
.meta span b{{color:#2C282C;font-weight:600}}
.meta .line{{display:inline-block;width:130px;border-bottom:1px solid #B9B2A6;transform:translateY(3px)}}
table{{width:100%;border-collapse:collapse;table-layout:fixed}}
th{{font-family:ui-monospace,Menlo,monospace;font-size:8px;text-transform:uppercase;letter-spacing:.05em;
 color:#6E6870;font-weight:500;text-align:left;padding:7px 6px;border-bottom:1.5px solid #2C282C;vertical-align:bottom}}
td{{height:34px;border-bottom:1px solid #D9D3C7}}
td+td,th+th{{border-left:1px solid #EAE5DB}}
.foot{{margin-top:14px;display:flex;justify-content:space-between;font-size:9px;color:#6E6870}}
</style></head><body>
<div class="head"><h1>{esc(title)}</h1><span class="wm">softgrove.github.io</span></div>
<div class="meta"><span>Name <span class="line"></span></span><span>Week of <span class="line"></span></span></div>
<table><thead><tr>{heads}</tr></thead><tbody>{rows}</tbody></table>
<div class="foot"><span>Free template — print as many as you need.</span>
<span>App version with automatic analysis: {esc(a["name"])} on the App Store · softgrove.github.io/apps/{t["app"]}/</span></div>
</body></html>"""

def chrome(args):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                    "--virtual-time-budget=8000", "--hide-scrollbars"] + args,
                   check=True, capture_output=True, timeout=120)

def main():
    tmp = pathlib.Path(tempfile.mkdtemp())
    og_dir = OUT / "og"; og_dir.mkdir(parents=True, exist_ok=True)
    jobs = [("home", "Quiet, private logbooks for the things you live with.", "Private iPhone apps",
             ["#3E8E8C", "#7A2E33", "#E87722", "#2E5E54", "#E07A5F", "#2A3354"])]
    for key, a in DATA["apps"].items():
        sub = DESCS[a["asc"]]["subtitle"]
        jobs.append((f"apps-{key}", f"{a['name']} — {sub}", "Free on the App Store",
                     [a.get("spine_bg", a["accent"]), a["bg"]]))
    jobs.append(("templates", "Tracker templates, free to print.", "PDF · no sign-up",
                 [DATA["apps"][t["app"]]["accent"] for t in DATA["templates"].values()]))
    for slug, t in DATA["templates"].items():
        jobs.append((f"templates-{slug}", t["h1"], "Free PDF download",
                     [DATA["apps"][t["app"]]["accent"]]))
    for name, title, sub, chips in jobs:
        src = tmp / f"{name}.html"; src.write_text(og_html(title, sub, chips))
        chrome([f"--screenshot={og_dir / (name + '.png')}", "--window-size=1200,630", f"file://{src}"])
        print("og:", name)
    for slug in DATA["templates"]:
        src = tmp / f"{slug}-pdf.html"; src.write_text(pdf_html(slug))
        dest = OUT / "templates" / slug / f"{slug}.pdf"
        dest.parent.mkdir(parents=True, exist_ok=True)
        chrome([f"--print-to-pdf={dest}", "--no-pdf-header-footer", f"file://{src}"])
        print("pdf:", slug)
    shutil.rmtree(tmp)

if __name__ == "__main__":
    main()
