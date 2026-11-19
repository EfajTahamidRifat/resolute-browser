#!/usr/bin/env python3
"""Puts Resolute Home (Resolute's new tab page) into the Chromium tree.

Usage: add_resolute_home.py <chromium src dir> <resolute repo dir>

Resolute Home is a built-in (component) extension whose page replaces the new
tab page (chrome_url_overrides). Patch 0008 makes Chromium load it; this script
provides its files:
  * copies <repo>/chromium/resolute_home/ to
    src/chrome/browser/resources/resolute_home/
  * adds the current config/partners.json and config/icons/ (the page also
    refreshes them from GitHub, so new partners appear without an app update)
  * lists every file in chrome/browser/resources/component_extension_resources.grd
    so it is packed into the app (manifest.json becomes IDR_RESOLUTE_HOME_MANIFEST)
Plain Python only. Run after the patches, before building.
"""
import pathlib
import re
import shutil
import sys

src = pathlib.Path(sys.argv[1])
repo = pathlib.Path(sys.argv[2])
dest = src / "chrome/browser/resources/resolute_home"
grd = src / "chrome/browser/resources/component_extension_resources.grd"

if dest.exists():
    shutil.rmtree(dest)
shutil.copytree(repo / "chromium/resolute_home", dest)
shutil.copyfile(repo / "config/partners.json", dest / "partners.json")
shutil.copytree(repo / "config/icons", dest / "icons")

files = sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file())
lines = []
for rel in files:
    if rel == "manifest.json":
        name = "IDR_RESOLUTE_HOME_MANIFEST"
    else:
        name = "IDR_RESOLUTE_HOME_" + re.sub(r"[^A-Z0-9]+", "_", rel.upper()).strip("_")
    lines.append(
        f'      <include name="{name}" file="resolute_home/{rel}" '
        f'resource_path="resolute_home/{rel}" type="BINDATA" />'
    )

text = grd.read_text(encoding="utf-8")
if "IDR_RESOLUTE_HOME_MANIFEST" in text:
    sys.exit("component_extension_resources.grd already lists Resolute Home")
marker = "<includes>"
if marker not in text:
    sys.exit("no <includes> in component_extension_resources.grd: update add_resolute_home.py")
block = "\n      <!-- Resolute Home (added by add_resolute_home.py) -->\n" + "\n".join(lines)
text = text.replace(marker, marker + block, 1)
grd.write_text(text, encoding="utf-8")
print(f"resolute home: {len(files)} files -> {dest.relative_to(src)}")
for rel in files:
    print(f"  {rel}")
