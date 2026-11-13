#!/usr/bin/env python3
"""Puts Resolute's name and icon into the Chromium tree (run after the patches).

Usage: apply_branding.py <chromium src dir> <resolute chromium/ dir>

Chromium's non-Google builds take their name and launcher icons from
chrome/android/java/res_chromium_base. Instead of a patch with binary images
(which would break whenever Chromium redraws its icons), this script:
  * renames "Chromium" to "Resolute" in values/channel_constants.xml
  * finds every launcher icon PNG there and replaces it with Resolute's icon
    of the same pixel size, from chromium/branding/<kind>_<size>.png
Plain Python only (no image library): the CI machine's python has none.
It prints every file it changes and every PNG it leaves alone.
"""
import pathlib
import re
import shutil
import struct
import sys

src = pathlib.Path(sys.argv[1])
ours = pathlib.Path(sys.argv[2]) / "branding"
base = src / "chrome/android/java/res_chromium_base"

# 1. Name
names = base / "values/channel_constants.xml"
text = names.read_text()
names.write_text(re.sub(r">Chromium", ">Resolute", text))
print(f"name: {names.relative_to(src)} ({text.count('>Chromium')} strings)")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    return struct.unpack(">II", head[16:24])


# 2. Icons: which kind of Resolute image replaces which Chromium icon.
KINDS = [
    ("layered_app_icon_background", "adaptive_background"),
    ("layered_app_icon", "adaptive_foreground"),
    ("app_icon", "legacy_icon"),
]

changed = kept = 0
missing = []
for png in sorted(base.rglob("*.png")):
    stem = png.name[:-4]
    kind = next((k for prefix, k in KINDS if stem.startswith(prefix)), None)
    if kind is None:
        print(f"kept: {png.relative_to(src)}")
        kept += 1
        continue
    w, h = png_size(png)
    mine = ours / f"{kind}_{w}.png"
    if w != h or not mine.exists():
        missing.append(f"{png.relative_to(src)} needs {kind}_{w}.png ({w}x{h})")
        continue
    shutil.copyfile(mine, png)
    print(f"icon: {png.relative_to(src)} {w}x{h} <- {mine.name}")
    changed += 1

print(f"branding done: {changed} icons replaced, {kept} PNGs left as they were")
for m in missing:
    # Not fatal: the icon simply stays Chromium's until we add that size.
    print(f"WARNING no Resolute icon, left Chromium's: {m}")
if changed == 0:
    sys.exit("no launcher icons found: Chromium moved them, update apply_branding.py")
