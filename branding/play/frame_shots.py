#!/usr/bin/env python3
"""Puts the raw store screenshots from store_shots.py into the Resolute Play frame
(dark background, red glow, headline, phone outline), 1080x1920 PNG.

Usage: frame_shots.py <dir with raw shots> <output dir>
Needs Python Playwright with Chromium (the E2E workflow installs it).
Only shots listed in SHOTS are framed, in that order (the Play order).
"""
import html
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent.parent / "chromium" / "resolute_home" / "fonts"

# raw shot name, kicker, headline, subline
SHOTS = [
    ("1-home", "Resolute Home", "Level up as you explore", "Daily quests and XP on every new tab"),
    ("2-wallet", "Wallet", "Your wallet, one tap away", "MetaMask and other wallets sit right in the toolbar"),
    ("3-extensions", "Extensions", "Real desktop extensions", "From the Chrome Web Store, on your phone"),
    ("4-workspaces", "Tabs", "Workspaces for your tabs", "Keep projects apart and switch in one tap"),
    ("5-menu", "One hand", "Everything under your thumb", "Address bar, buttons and menu at the bottom"),
]


def main():
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    template = (HERE / "screenshot_frame.html").read_text(encoding="utf-8")
    page_file = out / "frame.html"
    made = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        for name, kicker, title, sub in SHOTS:
            img = raw / f"{name}.png"
            if not img.exists():
                print(f"missing {img}, skipped")
                continue
            page_file.write_text(
                template.replace("FONTDIR", FONTS.as_uri())
                .replace("IMG", img.resolve().as_uri())
                .replace("KICKER", html.escape(kicker))
                .replace("TITLE", html.escape(title))
                .replace("SUB", html.escape(sub)),
                encoding="utf-8")
            page.goto(page_file.as_uri())
            page.wait_for_timeout(500)
            page.screenshot(path=str(out / f"{name}.png"))
            made += 1
            print(f"framed {name}")
        browser.close()
    page_file.unlink(missing_ok=True)
    if made < 2:
        sys.exit(f"only {made} framed screenshots (Play needs at least 2)")


if __name__ == "__main__":
    main()
