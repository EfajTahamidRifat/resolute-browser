# Takes Google Play store screenshots after run_tests.py (which has installed
# MetaMask and uBlock from the Chrome Web Store). Run on a 1080x1920 emulator
# (e2e-test.yml input store_shots). Removes the test flags file first, so the
# "loading flags from a command-line file" snackbar does not appear.
# Usage: store_shots.py OUT_DIR
import re
import subprocess
import sys
import time
from pathlib import Path

PKG = "com.resolute.browser"
OUT = Path(sys.argv[1]) / "store"
OUT.mkdir(parents=True, exist_ok=True)


def adb(*args, timeout=120):
    return subprocess.run(["adb", *args], capture_output=True, text=True, timeout=timeout).stdout


def shot(name):
    with open(OUT / f"{name}.png", "wb") as f:
        subprocess.run(["adb", "exec-out", "screencap", "-p"], stdout=f, timeout=60)
    print("shot", name)


def dump():
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    return adb("shell", "cat", "/sdcard/ui.xml")


def tap_id(rid):
    m = re.search(r'resource-id="%s:id/%s"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"' % (PKG, rid), dump())
    if not m:
        print("not found:", rid)
        return False
    x1, y1, x2, y2 = map(int, m.groups())
    adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
    return True


def open_url(url, wait=25):
    adb("shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url, "-p", PKG)
    time.sleep(wait)


print(adb("shell", "wm", "size"), adb("shell", "wm", "density"))
adb("shell", "rm", "-f", "/data/local/tmp/chrome-command-line")
adb("shell", "am", "force-stop", PKG)
adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
time.sleep(30)

# 1. Resolute Home in a new tab.
open_url("chrome://newtab/", 20)
adb("shell", "input", "keyevent", "BACK")  # close the keyboard if the box took focus
time.sleep(3)
shot("1-home")

# 2. MetaMask in the Chrome Web Store.
open_url("https://chromewebstore.google.com/detail/metamask/nkbihfbeogaeaoehlefnkodbefgpgknn", 35)
shot("2-web-store-metamask")

# 3. The extensions menu on a dapp.
open_url("https://app.uniswap.org/", 40)
shot("3-dapp")
if tap_id("extensions_menu_button"):
    time.sleep(4)
    shot("4-extensions-menu")
    adb("shell", "input", "keyevent", "BACK")

# 5. A normal web page.
open_url("https://en.wikipedia.org/wiki/Web3", 25)
shot("5-wikipedia")
