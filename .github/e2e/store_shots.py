# Takes the Google Play store screenshots after run_tests.py (which has installed
# MetaMask and uBlock from the Chrome Web Store). Run on a 1080x1920 emulator
# (e2e-test.yml input store_shots); branding/play/frame_shots.py then puts them in
# the Resolute frame and Sign Play release (input screenshots_run) sends them to Play.
# Usage: store_shots.py OUT_DIR
#
# Shots (names must match SHOTS in branding/play/frame_shots.py). Old tabs are closed
# first and the test flags file is kept (DevTools tidies the dapp page):
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
            labels = re.findall(r'(?:text|content-desc)="([^"]*)"', node)
            b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
            if b and any(re.search(pattern, label) for label in labels):
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
    home = next((t for t in rt.cdp_targets() if rt.RESOLUTE_HOME in t.get("url", "")
                 or t.get("url", "").startswith("chrome://newtab")), None)
    if home is not None:
        print("tour:", rt.cdp_eval(home, "(() => { const s = document.getElementById('tour-skip');"
                                         " if (s && !document.getElementById('tour').hidden)"
                                         " { s.click(); return 'closed'; } return 'not shown'; })()"),
              flush=True)
        time.sleep(2)  # closing the tour saves the page's state; mark tips after it
        # Quick tips would cover Resolute Home in shot 1: mark them seen.
        print("tips:", rt.cdp_eval(home, "chrome.storage.local.get('home').then(r => {"
                                         " const h = r.home || {}; h.tipsSeen = true;"
                                         " return chrome.storage.local.set({home: h}).then(() => 'seen'); })"),
              flush=True)
    else:
        print("no Resolute Home tab for the tour", flush=True)
except Exception as e:  # noqa: BLE001
    print("tour step failed:", e, flush=True)

# Close every tab the tests left behind (blank pages, example.com, foreign text), so
# the tab screen only shows the tabs opened below. DevTools still works here.
try:
    pages = [t for t in rt.cdp_targets() if t.get("type") == "page"]
    for t in pages[1:]:
        rt.cdp_send(pages[0], [("Target.closeTarget", {"targetId": t["id"]})])
    print("closed old tabs:", len(pages) - 1, flush=True)
except Exception as e:  # noqa: BLE001
    print("closing tabs failed:", e, flush=True)


def flags_message_gone(seconds=60):
    """The test flags file shows a "loading flags from a command-line file" message
    after a start; wait until it has gone so it is not in a screenshot."""
    end = time.time() + seconds
    while time.time() < end:
        if "command-line file" not in dump():
            return True
        time.sleep(3)
    print("flags message still showing", flush=True)
    return False


def page(url_part):
    for _ in range(10):
        t = next((t for t in rt.cdp_targets() if t.get("type") == "page"
                  and url_part in t.get("url", "")), None)
        if t is not None:
            return t
        time.sleep(3)
    return None


# Restart (keeps the flags file so DevTools can tidy the dapp page below).
adb("shell", "am", "force-stop", PKG)
adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
time.sleep(20)
rt.cdp_forward()
flags_message_gone()

# 1. Resolute Home, opened with the toolbar's home button (a chrome:// link from
# outside the app is not opened: run 45042205048 showed the phone's home screen).
# Uses the one tab left open (no second Resolute Home tab on the tab screen).
if tap_id("home_button"):
    time.sleep(12)
    flags_message_gone()
    shot("1-home")

# 2 and 3. A dapp with the wallet button. Its own banners ("Get app", promos) are
# closed first; then the extensions menu, then the dapp's wallet list with MetaMask.
open_url("https://app.uniswap.org/", 40)
TIDY_JS = r"""(() => {
  let n = 0;
  for (const b of document.querySelectorAll('button,[role=button],[aria-label]')) {
    const l = (b.getAttribute('aria-label') || '') + ' ' + (b.getAttribute('data-testid') || '');
    if (/close|dismiss/i.test(l) && b.offsetParent !== null) { b.click(); n++; }
  }
  for (const e of document.querySelectorAll('div,section,aside')) {
    const t = e.innerText || '';
    if ((/Get the Uniswap Wallet app/.test(t) || /Trade stocks and bonds/.test(t))
        && t.length < 400 && e.getBoundingClientRect().height < 700
        && e.style.visibility !== 'hidden') { e.style.visibility = 'hidden'; n++; }
  }
  return n;
})()"""
uni = page("uniswap")
if uni is not None:
    print("tidy:", rt.cdp_eval(uni, TIDY_JS), flush=True)
    time.sleep(3)
    print("tidy again:", rt.cdp_eval(uni, TIDY_JS), flush=True)
    time.sleep(3)
if tap_id("extensions_menu_button"):
    time.sleep(4)
    shot("3-extensions")
    back()
    time.sleep(2)
if uni is not None:
    print("connect:", rt.cdp_eval(uni, r"""(() => {
      const b = [...document.querySelectorAll('button,[role=button]')]
        .find(b => /^\s*Connect/.test(b.innerText || '') && b.offsetParent !== null);
      if (!b) return 'no connect button'; b.click(); return 'clicked';
    })()"""), flush=True)
    time.sleep(6)
shot("2-wallet")
back()
time.sleep(2)

# 4. Workspaces: a few clean tabs, one of them in its own workspace.
open_url("https://ethereum.org/", 25)
if tap_id("menu_button"):
    time.sleep(3)
    if tap_text(r"new workspace", tries=2):
        time.sleep(3)
        # Name it if a naming dialog shows, then confirm.
        adb("shell", "input", "text", "Research")
        time.sleep(1)
        tap_text(r"^(Done|Save|Create|OK)$", tries=2)
        time.sleep(3)
    else:
        back()
open_url("https://en.wikipedia.org/wiki/Web3", 25)
wiki = page("wikipedia")
if wiki is not None:  # the fundraising banner would fill the tab's picture
    rt.cdp_eval(wiki, "(() => { const s = document.createElement('style'); s.textContent ="
                " '#siteNotice,#centralNotice,.cn-fundraising,.frb{display:none!important}';"
                " document.head.appendChild(s); return 1; })()")
    time.sleep(3)
if tap_id("tab_switcher_button"):
    time.sleep(6)
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
