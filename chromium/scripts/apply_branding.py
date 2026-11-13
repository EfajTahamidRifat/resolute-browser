#!/usr/bin/env python3
"""Puts Resolute's name and icon into the Chromium tree (run after the patches).

Usage: apply_branding.py <chromium src dir> <resolute chromium/ dir>

Chromium's non-Google builds take their name and launcher icons from
chrome/android/java/res_chromium_base. Instead of a patch with binary images
(which would break whenever Chromium redraws its icons), this script:
  * renames "Chromium" to "Resolute" in values/channel_constants.xml
  * finds every launcher icon PNG there and overwrites it with Resolute's,
    resized to the same pixel size as the file it replaces
It prints every file it changes and every PNG it leaves alone, so the build
log shows what still carries Chromium's look.
"""
import pathlib
import re
import subprocess
import sys

try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                           "--break-system-packages", "pillow"])
    from PIL import Image

src = pathlib.Path(sys.argv[1])
ours = pathlib.Path(sys.argv[2]) / "branding"
base = src / "chrome/android/java/res_chromium_base"

# 1. Name
names = base / "values/channel_constants.xml"
text = names.read_text()
new = re.sub(r">Chromium", ">Resolute", text)
names.write_text(new)
print(f"name: {names.relative_to(src)} ({text.count('>Chromium')} strings)")

# 2. Icons. Which of our images replaces which kind of Chromium icon.
SOURCES = [
    ("layered_app_icon_background", "adaptive_background_1024.png"),
    ("layered_app_icon", "adaptive_foreground_1024.png"),
    ("app_icon", "legacy_icon_1024.png"),
]
images = {f: Image.open(ours / f).convert("RGBA") for _, f in SOURCES}

changed = kept = 0
for png in sorted(base.rglob("*.png")):
    stem = png.name[:-4]
    pick = next((f for prefix, f in SOURCES if stem.startswith(prefix)), None)
    if pick is None:
        print(f"kept: {png.relative_to(src)}")
        kept += 1
        continue
    with Image.open(png) as old:
        size = old.size
    images[pick].resize(size, Image.LANCZOS).save(png, optimize=True)
    print(f"icon: {png.relative_to(src)} {size[0]}x{size[1]} <- {pick}")
    changed += 1

print(f"branding done: {changed} icons replaced, {kept} PNGs left as they were")
if changed == 0:
    sys.exit("no launcher icons found: Chromium moved them, update apply_branding.py")
