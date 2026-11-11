#!/usr/bin/env python3
"""End-to-end tests for the Resolute APK on an Android emulator.

Runs inside .github/workflows/e2e-test.yml after the emulator has booted.
Drives the browser with adb (intents, taps found through uiautomator dumps),
records screenshots, UI dumps and logcat, and writes results/report.md and
results/report.json. Each test passes or fails on its own; the script exits 1
if any test failed.

Usage: run_tests.py <apk> <results-dir>
"""
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PKG = "com.resolute.browser"
APK = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

# Chrome Web Store item IDs.
UBLOCK_LITE = "ddkjiahejlhfcafbddmgiahcphecmpfh"
METAMASK = "nkbihfbeogaeaoehlefnkodbefgpgknn"

FLAGS = ("_ --disable-fre --no-default-browser-check --no-first-run "
         "--force-renderer-accessibility --disable-features=SigninPromo")

results = []


def adb(*args, check=False, timeout=120):
    r = subprocess.run(["adb", *args], capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"adb {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def shot(name):
    path = OUT / f"{name}.png"
    with open(path, "wb") as f:
        subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f, timeout=60)
    return path.name


def ui_dump(name=None):
    """Returns the uiautomator XML (and saves it when a name is given)."""
    for _ in range(3):
        adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
        xml = adb("shell", "cat", "/sdcard/ui.xml")
        if xml.strip().startswith("<?xml"):
            if name:
                (OUT / f"{name}.xml").write_text(xml)
            return xml
        time.sleep(2)
    return ""


def nodes(xml):
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    return list(root.iter("node"))


def find(xml, pattern):
    rx = re.compile(pattern, re.I)
    for n in nodes(xml):
        label = (n.get("text") or "") + " " + (n.get("content-desc") or "")
        if rx.search(label):
            return n
    return None


def tap(node):
    x1, y1, x2, y2 = map(int, re.findall(r"\d+", node.get("bounds")))
    adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))


def wait_for(pattern, seconds=60, name=None):
    end = time.time() + seconds
    xml = ""
    while time.time() < end:
        xml = ui_dump()
        node = find(xml, pattern)
        if node is not None:
            if name:
                (OUT / f"{name}.xml").write_text(xml)
            return node
        dismiss_popups(xml)
        time.sleep(3)
    if name:
        (OUT / f"{name}.xml").write_text(xml)
    return None


def dismiss_popups(xml):
    """Closes first-run, sign-in and notification prompts if they appear."""
    for label in (r"^No thanks$", r"^Use without an account$", r"^Accept & continue$",
                  r"^Got it$", r"^Not now$", r"^Don.t allow$", r"^Skip$"):
        n = find(xml, label)
        if n is not None:
            tap(n)
            time.sleep(2)
            return True
    return False


def open_url(url):
    adb("shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url, "-p", PKG)


def crashed_since(mark):
    log = adb("logcat", "-d", "-v", "time", "-T", mark) if mark else adb("logcat", "-d")
    bad = [l for l in log.splitlines()
           if ("FATAL EXCEPTION" in l or "Fatal signal" in l or "ANR in " + PKG in l)
           and (PKG in l or "Fatal signal" in l)]
    return bad[:20]


def logcat_mark():
    out = adb("shell", "date", "+%m-%d %H:%M:%S.000").strip()
    return out


def record(name, ok, detail, screenshot=None):
    results.append({"test": name, "passed": bool(ok), "detail": detail, "screenshot": screenshot})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}", flush=True)


def test(name):
    def wrap(fn):
        def run():
            mark = logcat_mark()
            try:
                ok, detail, png = fn()
            except Exception as e:  # keep going with the other tests
                ok, detail, png = False, f"error: {e}", shot(f"{name}-error")
            crashes = crashed_since(mark)
            if crashes:
                ok = False
                detail += " | CRASH: " + crashes[0]
                (OUT / f"{name}-crash.txt").write_text("\n".join(crashes))
            record(name, ok, detail, png)
        return run
    return wrap


# ------------------------------------------------------------------ tests

@test("01-install")
def t_install():
    out = adb("install", "-r", "-g", str(APK), timeout=600)
    ok = "Success" in out
    adb("shell", f"echo '{FLAGS}' > /data/local/tmp/chrome-command-line")
    adb("shell", "chmod", "644", "/data/local/tmp/chrome-command-line")
    return ok, out.strip().splitlines()[-1] if out.strip() else "no output", None


@test("02-launch")
def t_launch():
    adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(20)
    dismiss_popups(ui_dump())
    pid = adb("shell", "pidof", PKG).strip()
    return bool(pid), f"process id {pid or 'none'}", shot("02-launch")


@test("03-load-example")
def t_example():
    open_url("https://example.com")
    node = wait_for(r"Example Domain", 90, "03-example")
    return node is not None, "page text found" if node is not None else "page text not found", shot("03-example")


@test("04-load-wikipedia")
def t_wiki():
    open_url("https://www.wikipedia.org")
    node = wait_for(r"Wikipedia", 90, "04-wikipedia")
    return node is not None, "page text found" if node is not None else "page text not found", shot("04-wikipedia")


def install_from_store(ext_id, name):
    open_url(f"https://chromewebstore.google.com/detail/{ext_id}")
    button = wait_for(r"^Add to (Chrome|Chromium|Resolute)$", 120, f"{name}-store")
    png = shot(f"{name}-store")
    if button is None:
        return False, "'Add to Chrome' button not found on the store page", png
    tap(button)
    confirm = wait_for(r"^Add extension$", 60, f"{name}-confirm")
    shot(f"{name}-confirm")
    if confirm is None:
        return False, "install confirmation dialog did not appear", png
    tap(confirm)
    time.sleep(25)
    return True, "install confirmed", shot(f"{name}-installed")


@test("05-store-install-ublock-lite")
def t_ublock():
    return install_from_store(UBLOCK_LITE, "05-ublock")


@test("06-store-install-metamask")
def t_metamask():
    return install_from_store(METAMASK, "06-metamask")


@test("07-extensions-listed")
def t_listed():
    open_url("chrome://extensions")
    time.sleep(10)
    xml = ui_dump("07-extensions")
    png = shot("07-extensions")
    have = [n for n in ("uBlock Origin Lite", "MetaMask") if find(xml, re.escape(n)) is not None]
    return len(have) == 2, "listed: " + (", ".join(have) or "none"), png


def main():
    adb("wait-for-device")
    adb("logcat", "-c")
    adb("shell", "settings", "put", "global", "window_animation_scale", "0")
    adb("shell", "settings", "put", "global", "transition_animation_scale", "0")
    adb("shell", "settings", "put", "global", "animator_duration_scale", "0")
    for t in (t_install, t_launch, t_example, t_wiki, t_ublock, t_metamask, t_listed):
        t()
    (OUT / "logcat.txt").write_text(adb("logcat", "-d", "-v", "time", timeout=300))
    (OUT / "report.json").write_text(json.dumps(results, indent=2))
    passed = sum(r["passed"] for r in results)
    lines = [f"# Resolute E2E: {passed}/{len(results)} passed", "",
             "| Test | Result | Detail | Screenshot |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['test']} | {'✅' if r['passed'] else '❌'} | "
                     f"{r['detail'].replace('|', '/')} | {r['screenshot'] or ''} |")
    (OUT / "report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
