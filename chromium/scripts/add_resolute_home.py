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
  * bundles a gzipped copy of MetaMask's phishing list for Resolute Shield
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

# Resolute Shield's starting list (shield.js downloads fresh copies every 12 hours):
# MetaMask's phishing list (DBAD licence, credited in NOTICE), gzipped. A failed download
# only means Shield starts empty until its first refresh; the build goes on.
SHIELD_LIST = "https://raw.githubusercontent.com/MetaMask/eth-phishing-detect/main/src/config.json"
try:
    import gzip, json, urllib.request
    with urllib.request.urlopen(SHIELD_LIST, timeout=60) as r:
        meta = json.loads(r.read().decode())
    keep = {k: meta[k] for k in ("version", "tolerance", "fuzzylist", "whitelist", "blacklist") if k in meta}
    (dest / "shield-list.json.gz").write_bytes(
        gzip.compress(json.dumps(keep, separators=(",", ":")).encode(), mtime=0))
    print(f"shield list: {len(keep.get('blacklist', []))} sites bundled")
except Exception as e:  # noqa: BLE001
    print(f"shield list not bundled ({e}); Shield downloads it on the phone")

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
