#!/usr/bin/env python3
"""Captures each Resolute Pick's website icon into config/icons/<id>.png.

Runs in GitHub Actions (.github/workflows/pick-icons.yml). For every partner in
config/partners.json it opens the partner's site, collects icon candidates
(apple-touch-icon, <link rel="icon"> with sizes, /favicon.ico), keeps the
largest bitmap, and saves it as a 128x128 PNG. The partner's "icon" field is
set to "icons/<id>.png". If a site can't be reached, the previous icon is kept
and the app falls back to a letter tile.
"""
import io
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "partners.json"
ICONS = ROOT / "icons"
SIZE = 128
UA = ("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/156.0 Mobile Safari/537.36")
TIMEOUT = 15


class IconLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = []  # (declared_size, href)
        self.manifest = None

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        rel = a.get("rel", "").lower()
        if rel == "manifest" and a.get("href"):
            self.manifest = a["href"]
            return
        if "icon" not in rel or not a.get("href"):
            return
        size = 0
        for s in a.get("sizes", "").split():
            try:
                size = max(size, int(s.lower().split("x")[0]))
            except ValueError:
                pass
        if "apple-touch-icon" in rel and size == 0:
            size = 180
        self.found.append((size, a["href"]))


def get(session, url):
    r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    return r


def candidates(session, site):
    urls = []
    try:
        page = get(session, site)
        parser = IconLinks()
        parser.feed(page.text[:500_000])
        if parser.manifest:
            try:
                murl = urljoin(page.url, parser.manifest)
                icons = get(session, murl).json().get("icons", [])
                def msize(i):
                    try:
                        return max(int(x.split("x")[0]) for x in i.get("sizes", "0x0").split())
                    except ValueError:
                        return 0
                for i in sorted(icons, key=msize, reverse=True):
                    if i.get("src"):
                        urls.append(urljoin(murl, i["src"]))
            except Exception as e:
                print(f"  manifest failed: {e}")
        for _, href in sorted(parser.found, reverse=True):
            urls.append(urljoin(page.url, href))
        base = page.url
    except Exception as e:  # site blocks bots, timeouts, ...
        print(f"  page failed: {e}")
        base = site
    origin = "{0.scheme}://{0.netloc}".format(urlparse(base))
    urls += [origin + "/apple-touch-icon.png", origin + "/favicon.ico"]
    seen, out = set(), []
    for u in urls:
        if u not in seen and not u.lower().endswith(".svg"):
            seen.add(u)
            out.append(u)
    return out


def best_image(session, urls):
    best = None
    for u in urls:
        try:
            data = get(session, u).content
            img = Image.open(io.BytesIO(data))
            if getattr(img, "n_frames", 1) > 1 and img.format == "ICO":
                sizes = sorted(img.ico.sizes(), reverse=True)
                img = img.ico.getimage(sizes[0])
            img = img.convert("RGBA")
        except Exception:
            continue
        if best is None or img.width > best.width:
            best = img
        if best.width >= SIZE:
            break
    return best


def to_tile(img):
    img.thumbnail((SIZE, SIZE), Image.LANCZOS)
    tile = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    tile.alpha_composite(img, ((SIZE - img.width) // 2, (SIZE - img.height) // 2))
    return tile


def main():
    cfg = json.loads(CONFIG.read_text())
    ICONS.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = UA
    failed = []
    for p in cfg["partners"]:
        print(f"{p['id']}: {p['url']}")
        # "icon_site" overrides where the icon is taken from (e.g. when the
        # referral link is on a sign-up subdomain that blocks bots).
        site = p.get("icon_site") or "{0.scheme}://{0.netloc}/".format(urlparse(p["url"]))
        img = best_image(session, candidates(session, site))
        target = ICONS / f"{p['id']}.png"
        if img is None:
            print("  no icon found" + (", keeping previous" if target.exists() else ""))
            failed.append(p["id"])
        else:
            to_tile(img).save(target, optimize=True)
            print(f"  saved {target.name} (source {img.width}px)")
        p["icon"] = f"icons/{p['id']}.png" if target.exists() else None
    CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    if failed:
        print("No icon for: " + ", ".join(failed) + " (app shows a letter tile)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
