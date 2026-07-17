#!/usr/bin/env python3
"""IndexNow submission — ping Bing/Yandex/etc. with all site URLs after a build.

IndexNow protocol: https://www.indexnow.org/
- Key file must exist at https://softgrove.github.io/<key>.txt containing just the key
- POST to https://api.indexnow.org/IndexNow with JSON body
- Engines that implement IndexNow (Bing, Yandex, Seznam, Naver) share the submission

Run after: python3 build.py && python3 assets.py && git push
"""
import json, urllib.request, urllib.error, pathlib

KEY = "8a4b2c6d9e1f3a5b7c8d2e4f6a0b1c3d"
HOST = "softgrove.github.io"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ORIGIN = f"https://{HOST}"
SITEMAP = pathlib.Path(__file__).parent / "docs" / "sitemap.xml"

def get_urls_from_sitemap():
    import re
    xml = SITEMAP.read_text()
    return re.findall(r"<loc>(https://[^<]+)</loc>", xml)

def submit(urls):
    payload = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls
    }).encode()
    req = urllib.request.Request(
        "https://api.indexnow.org/IndexNow",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow: {resp.status} {resp.reason} — {len(urls)} URLs submitted")
    except urllib.error.HTTPError as e:
        print(f"IndexNow HTTP error: {e.code} {e.reason}")
        print(e.read().decode())
    except Exception as e:
        print(f"IndexNow error: {e}")

if __name__ == "__main__":
    urls = get_urls_from_sitemap()
    print(f"Submitting {len(urls)} URLs to IndexNow...")
    for u in urls[:5]:
        print(" ", u)
    if len(urls) > 5:
        print(f"  ... and {len(urls)-5} more")
    submit(urls)
