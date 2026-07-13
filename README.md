# softgrove.github.io

Marketing site for the Softgrove app portfolio. Static, no framework.

- `apps.json` — palette (from each app's Theme.swift) + metadata + template definitions
- `_asc_descs.json` — live App Store descriptions (ground truth for LP copy; refresh via the snippet in build.py docstring)
- `build.py` — generates all HTML into `docs/` (GitHub Pages source)
- `assets.py` — OG PNGs + printable PDFs via headless Chrome
- `page_hashes.json` — per-page content hashes so sitemap lastmod only bumps on real changes

Build: `python3 build.py && python3 assets.py`
