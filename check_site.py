#!/usr/bin/env python3
"""Post-build checks for docs/: broken internal links, duplicate <title>/description,
sitemap and llms.txt coverage. Exit 1 on any failure. Run after build.py (+ assets.py)."""
import pathlib, re, sys, html as htmlmod
from collections import defaultdict

OUT = pathlib.Path(__file__).parent / "docs"
ORIGIN = "https://softgrove.github.io"
pages = sorted(p for p in OUT.rglob("*.html") if not p.name.startswith("google"))  # search-console verification file
problems = []

def exists(path):
    path = path.split("#")[0].split("?")[0]
    if not path or not path.startswith("/"): return True
    f = OUT / path.lstrip("/")
    if path.endswith("/"): f = f / "index.html"
    return f.exists()

titles, descs = defaultdict(list), defaultdict(list)
for p in pages:
    s = p.read_text()
    rel = "/" + str(p.relative_to(OUT)).replace("index.html", "")
    for href in re.findall(r'(?:href|src)="([^"]+)"', s):
        href = htmlmod.unescape(href)
        if href.startswith(ORIGIN): href = href[len(ORIGIN):]
        if href.startswith("/") and not exists(href):
            problems.append(f"broken link {rel} -> {href}")
    m = re.search(r"<title>(.*?)</title>", s); t = m.group(1) if m else ""
    m = re.search(r'<meta name="description" content="([^"]*)"', s); d = m.group(1) if m else ""
    if rel != "/404.html":
        if not t: problems.append(f"missing title {rel}")
        if not d: problems.append(f"missing description {rel}")
        titles[t].append(rel); descs[d].append(rel)
        if not re.search(r'<link rel="canonical" href="' + re.escape(ORIGIN + rel) + '"', s):
            problems.append(f"canonical mismatch {rel}")
        if 'application/ld+json' not in s and rel not in ("/",):
            pass  # hubs/home may omit; template/guide/tool pages always have it
for t, rels in titles.items():
    if len(rels) > 1: problems.append(f"duplicate title {t!r}: {rels}")
for d, rels in descs.items():
    if len(rels) > 1: problems.append(f"duplicate description: {rels}")

# sitemap: every listed URL exists and every built page (except 404) is listed
sm = (OUT / "sitemap.xml").read_text()
sm_urls = set(re.findall(r"<loc>(.*?)</loc>", sm))
built = {ORIGIN + "/" + str(p.relative_to(OUT)).replace("index.html", "") for p in pages} - {ORIGIN + "/404.html"}
for u in sm_urls - built: problems.append(f"sitemap lists missing page {u}")
for u in built - sm_urls: problems.append(f"page not in sitemap {u}")

# llms.txt and sitemap links resolve; template PDFs exist
for u in re.findall(r"\]\((https://softgrove\.github\.io[^)]+)\)", (OUT / "llms.txt").read_text()):
    if not exists(u[len(ORIGIN):]): problems.append(f"llms.txt dead link {u}")
for d in (OUT / "templates").iterdir():
    if d.is_dir() and not (d / f"{d.name}.pdf").exists(): problems.append(f"missing PDF for /templates/{d.name}/")
    if d.is_dir() and not (OUT / "og" / f"templates-{d.name}.png").exists(): problems.append(f"missing OG image for /templates/{d.name}/")

print(f"checked {len(pages)} pages, {len(sm_urls)} sitemap urls")
for x in problems: print("FAIL", x)
print("OK" if not problems else f"{len(problems)} problem(s)")
sys.exit(1 if problems else 0)
