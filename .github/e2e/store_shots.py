# Takes the Google Play store screenshots after run_tests.py (which has installed
# MetaMask and uBlock from the Chrome Web Store). Run on a 1080x1920 emulator
# (e2e-test.yml input store_shots); branding/play/frame_shots.py then puts them in
# the Resolute frame and Sign Play release (input screenshots_run) sends them to Play.
# Usage: store_shots.py OUT_DIR
#
# Shots (names must match SHOTS in branding/play/frame_shots.py):
#   1-home        Resolute Home (welcome tour closed)
#   2-wallet      a dapp with the red MetaMask button in the toolbar
#   3-extensions  the extensions menu on that dapp
#   4-workspaces  the tab screen
#   5-menu        the app menu on a web page (Make Resolute default at the top)
import re
import subprocess
import sys
import time
from pathlib import Path

PKG = "com.resolute.browser"
BASE = Path(sys.argv[1])
OUT = BASE / "store"
OUT.mkdir(parents=True, exist_ok=True)


def adb(*args, timeout=120):
    return subprocess.run(["adb", *args], capture_output=True, text=True, timeout=timeout).stdout


def shot(name):
    with open(OUT / f"{name}.png", "wb") as f:
        subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f, timeout=60)
    print("shot", name, flush=True)


def dump():
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    return adb("shell", "cat", "/sdcard/ui.xml")


def tap_id(rid, tries=5):
    for _ in range(tries):
        m = re.search(r'resource-id="%s:id/%s"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
                      % (PKG, rid), dump())
        if m:
            x1, y1, x2, y2 = map(int, m.groups())
            adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
            return True
        time.sleep(3)
    print("not found:", rid, flush=True)
    return False


def tap_text(pattern, tries=3):
    """Taps the first view whose text or description matches pattern (e.g. a "Got it")."""
    for _ in range(tries):
        for m in re.finditer(r'<node [^>]*>', dump()):
            node = m.group(0)
            label = " ".join(re.findall(r'(?:text|content-desc)="([^"]*)"', node))
            b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
            if b and re.search(pattern, label):
                x1, y1, x2, y2 = map(int, b.groups())
                adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
                return True
        time.sleep(2)
    return False


def open_url(url, wait=25):
    adb("shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url, "-p", PKG)
    time.sleep(wait)


def back(n=1):
    for _ in range(n):
        adb("shell", "input", "keyevent", "BACK")
        time.sleep(2)


print(adb("shell", "wm", "size"), adb("shell", "wm", "density"), flush=True)

# 0. Close Resolute Home's welcome tour (it is saved in Resolute Home's storage), while
# the test flags file still turns on DevTools. Uses run_tests.py's DevTools helpers.
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.argv = [sys.argv[0], "unused.apk", str(BASE)]
import run_tests as rt  # noqa: E402

try:
    rt.cdp_forward()
    first = next((t for t in rt.cdp_targets() if t.get("type") == "page"), None)
    if first is not None:
        rt.cdp_send(first, [("Target.createTarget", {"url": "chrome://newtab/"})])
    time.sleep(10)
    home = next((t for t in rt.cdp_targets() if rt.RESOLUTE_HOME in t.get("url", "")), None)
    if home is not None:
        print("tour:", rt.cdp_eval(home, "(() => { const s = document.getElementById('tour-skip');"
                                         " if (s && !document.getElementById('tour').hidden)"
                                         " { s.click(); return 'closed'; } return 'not shown'; })()"),
              flush=True)
    else:
        print("no Resolute Home tab for the tour", flush=True)
except Exception as e:  # noqa: BLE001
    print("tour step failed:", e, flush=True)

# Restart without the test flags file, so the "loading flags from a command-line
# file" message does not show.
adb("shell", "rm", "-f", "/data/local/tmp/chrome-command-line")
adb("shell", "am", "force-stop", PKG)
adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
time.sleep(30)

# 1. Resolute Home, opened with the toolbar's home button (a chrome:// link from
# outside the app is not opened: run 45042205048 showed the phone's home screen).
open_url("https://example.com/", 15)
if tap_id("home_button"):
    time.sleep(12)
    shot("1-home")

# 2 and 3. A dapp with the wallet button, then the extensions menu.
open_url("https://app.uniswap.org/", 40)
shot("2-wallet")
if tap_id("extensions_menu_button"):
    time.sleep(4)
    shot("3-extensions")
    back()

# 4. The tab screen.
if tap_id("tab_switcher_button"):
    time.sleep(5)
    # Chromium's one-time "Your inactive items won't pile up" sheet covers the tabs.
    if tap_text(r"^Got it$"):
        time.sleep(3)
    shot("4-workspaces")
    back()

# 5. The app menu on a normal web page.
open_url("https://en.wikipedia.org/wiki/Web3", 25)
if tap_id("menu_button"):
    time.sleep(3)
    shot("5-menu")
    back()
