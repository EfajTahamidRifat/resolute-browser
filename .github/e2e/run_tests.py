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


# ---------------------------------------------------------------- DevTools
# Web page content is not visible to uiautomator in this build, so pages are
# driven through Chromium's DevTools protocol (the same connection Chrome
# DevTools uses over adb). It also lists every page, popup and extension
# window the browser has open, which is what the wallet test needs.
CDP_PORT = 9222


def cdp_forward():
    socks = adb("shell", "cat", "/proc/net/unix")
    names = sorted(set(re.findall(r"@(\S*devtools_remote\S*)", socks)))
    if not names:
        return None
    adb("forward", f"tcp:{CDP_PORT}", f"localabstract:{names[0]}")
    return names[0]


def cdp_targets():
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list", timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001
        print(f"cdp_targets: {e}", flush=True)
        return []


def cdp_eval(target, expression):
    """Runs JavaScript in a page target; returns its value (or an error string)."""
    import websocket  # websocket-client, installed by the workflow
    ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=30,
                                     suppress_origin=True)
    try:
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
            "expression": expression, "returnByValue": True, "awaitPromise": True}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == 1:
                res = msg.get("result", {})
                if "exceptionDetails" in res:
                    return "JS error: " + json.dumps(res["exceptionDetails"])[:300]
                return res.get("result", {}).get("value")
    finally:
        ws.close()


def cdp_send(target, calls):
    """Sends DevTools commands [(method, params), ...] to one page, in order."""
    import websocket
    ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=30,
                                     suppress_origin=True)
    out = []
    try:
        for i, (method, params) in enumerate(calls, start=1):
            ws.send(json.dumps({"id": i, "method": method, "params": params}))
            while True:
                msg = json.loads(ws.recv())
                if msg.get("id") == i:
                    out.append(msg)
                    break
    finally:
        ws.close()
    return out


DESKTOP_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/158.0.0.0 Safari/537.36")


def cdp_desktop_mode(target):
    """Like ticking 'Desktop site': desktop user agent + non-mobile UA hints.
    The Chrome Web Store only installs (instead of offering to 'download to
    your desktop') when the browser looks like a desktop one."""
    return cdp_send(target, [
        ("Network.enable", {}),
        ("Network.setUserAgentOverride", {
            "userAgent": DESKTOP_UA, "platform": "Linux x86_64",
            "userAgentMetadata": {
                "brands": [{"brand": "Chromium", "version": "158"}],
                "fullVersionList": [{"brand": "Chromium", "version": "158.0.0.0"}],
                "platform": "Linux", "platformVersion": "6.0", "architecture": "x86",
                "model": "", "mobile": False}}),
        ("Page.reload", {"ignoreCache": True}),
    ])


def menu_desktop_site(name):
    """Ticks Resolute's own ⋮ > Desktop site, like a user (it persists for the
    tab, unlike a DevTools override, which ends when DevTools disconnects)."""
    menu = wait_for(r"^Customize and control", 20)
    if menu is None:
        return "menu button not found"
    tap(menu)
    time.sleep(2)
    item = None
    for _ in range(4):
        xml = ui_dump(f"{name}-menu")
        item = find(xml, r"^Desktop site$")
        if item is not None:
            break
        adb("shell", "input", "swipe", "540", "1500", "540", "700", "300")
        time.sleep(1)
    if item is None:
        adb("shell", "input", "keyevent", "4")
        return "Desktop site item not found"
    checked = None
    for n in nodes(xml):
        if (n.get("class") or "").endswith("CheckBox") and n.get("checked") == "true":
            checked = True
    tap(item)
    time.sleep(6)
    return "desktop site toggled"


def cdp_tap(target, find_js):
    """Taps an element like a finger would (a real input event, so pages treat
    it as a user gesture; a scripted .click() is not, and the Chrome Web Store
    then refuses to install). find_js must evaluate to the element or null."""
    import websocket
    rect = cdp_eval(target, "(() => { const e = " + find_js + "; if (!e) return null;"
                    " e.scrollIntoView({block: 'center'}); const r = e.getBoundingClientRect();"
                    " return {x: r.left + r.width / 2, y: r.top + r.height / 2,"
                    " label: (e.innerText || '').trim()}; })()")
    if not isinstance(rect, dict):
        return None
    ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=30,
                                     suppress_origin=True)
    try:
        for i, kind in enumerate(("mousePressed", "mouseReleased"), start=1):
            ws.send(json.dumps({"id": i, "method": "Input.dispatchMouseEvent", "params": {
                "type": kind, "x": rect["x"], "y": rect["y"], "button": "left",
                "clickCount": 1}}))
            while json.loads(ws.recv()).get("id") != i:
                pass
    finally:
        ws.close()
    return rect.get("label") or "tapped"


def cdp_wait_page(url_part, seconds=90):
    end = time.time() + seconds
    while time.time() < end:
        for t in cdp_targets():
            if t.get("type") == "page" and url_part in t.get("url", ""):
                return t
        time.sleep(3)
    return None


def crashed_since(mark):
    log = adb("logcat", "-d", "-v", "time", "-T", mark) if mark else adb("logcat", "-d")
    signals = ("FATAL EXCEPTION", "Fatal signal", "ANR in " + PKG,
               "Process " + PKG + " has crashed", "Failed to load native library")
    # Native crashes are logged under the process name, which Android may
    # shorten (e.g. "esolute.browser"), so match on the signal text.
    bad = [l for l in log.splitlines() if any(s in l for s in signals)]
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
    cdp_forward()
    t = cdp_wait_page("example.com", 90)
    time.sleep(3)
    title = cdp_eval(t, "document.title") if t else None
    return title == "Example Domain", f"page title: {title}", shot("03-example")


@test("04-load-wikipedia")
def t_wiki():
    open_url("https://www.wikipedia.org")
    node = wait_for(r"Wikipedia", 90, "04-wikipedia")
    return node is not None, "page text found" if node is not None else "page text not found", shot("04-wikipedia")


def install_from_store(ext_id, name):
    open_url(f"https://chromewebstore.google.com/detail/{ext_id}")
    cdp_forward()
    page = cdp_wait_page(ext_id, 120)
    if page is None:
        return False, "store page not found through DevTools", shot(f"{name}-store")
    desk = menu_desktop_site(name)
    time.sleep(6)
    page = cdp_wait_page(ext_id, 60) or page
    button = ("[...document.querySelectorAll('button')]"
              ".find(x => /^Add to /.test((x.innerText || '').trim()))")
    label = None
    for _ in range(30):
        label = cdp_tap(page, button)
        if label:
            break
        time.sleep(3)
    png = shot(f"{name}-store")
    if not label:
        return False, "store button not found", png
    confirm = wait_for(r"^Add extension$", 60, f"{name}-confirm")
    shot(f"{name}-confirm")
    if confirm is None:
        return False, f"clicked '{label}' ({desk}) but no install dialog appeared", png
    tap(confirm)
    time.sleep(25)
    return True, f"clicked '{label}', install confirmed", shot(f"{name}-installed")


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
    urls = " ".join(t.get("url", "") for t in cdp_targets())
    have = [n for n, i in (("uBlock Origin Lite", UBLOCK_LITE), ("MetaMask", METAMASK))
            if f"chrome-extension://{i}" in urls or find(xml, re.escape(n)) is not None]
    (OUT / "07-targets.json").write_text(json.dumps(cdp_targets(), indent=1))
    return len(have) == 2, "running/listed: " + (", ".join(have) or "none"), png


@test("08-wallet-connect")
def t_wallet():
    """Taps Connect on a local dApp page and records what happens to MetaMask's
    approval window (the bug owner hit on real phones, 2026-11-13)."""
    import http.server, threading, functools

    class Handler(http.server.SimpleHTTPRequestHandler):
        # The browser opens spare connections it never uses; without a timeout
        # the server waited on one forever and the whole job hung (2026-11-14).
        timeout = 10

    pages = Path(__file__).parent / "pages"
    handler = functools.partial(Handler, directory=str(pages))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8765), handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    adb("reverse", "tcp:8765", "tcp:8765")
    try:
        mark = logcat_mark()
        open_url("http://localhost:8765/connect.html")
        cdp_forward()
        page = cdp_wait_page("localhost:8765", 90)
        if page is None:
            return False, "test page did not load", shot("08-page")
        # dApps only use a browser extension wallet in desktop mode (in phone
        # mode they open the wallet app instead), so test it that way.
        desk = menu_desktop_site("08")
        time.sleep(4)
        page = cdp_wait_page("localhost:8765", 60) or page
        shot("08-page")
        time.sleep(4)
        provider = cdp_eval(page, "document.getElementById('provider').textContent")
        before = {t.get("id") for t in cdp_targets()}
        cdp_tap(page, "document.getElementById('go')")
        time.sleep(25)
        targets = cdp_targets()
        (OUT / "08-targets.json").write_text(json.dumps(targets, indent=1))
        new = [t for t in targets if t.get("id") not in before]
        result = cdp_eval(page, "document.getElementById('result').textContent")
        xml = ui_dump("08-after")
        png = shot("08-after")
        (OUT / "08-activities.txt").write_text(adb("shell", "dumpsys", "activity", "activities"))
        log = adb("logcat", "-d", "-v", "time", "-T", mark, timeout=300)
        keep = [l for l in log.splitlines() if re.search(
            r"PopupCreator|BrowserWindow|ChromeAndroidTask|MultiInstance|CustomTab|"
            r"RESOLUTE_E2E|xtension|windows\.create|ActivityTaskManager|"
            r"chromium.*(ERROR|WARNING|FATAL)", l)]
        (OUT / "08-wallet-logcat.txt").write_text("\n".join(keep))
        mm_new = [t["url"] for t in new if METAMASK in t.get("url", "")]
        visible = find(xml, r"MetaMask|Connect with MetaMask|Unlock|Create a new wallet") is not None
        detail = (f"{provider}; {result}; new MetaMask pages: {mm_new or 'none'}; "
                  f"other new targets: {[t.get('url') for t in new if t.get('url') not in mm_new][:4]}; "
                  f"MetaMask visible on screen={visible}")
        return bool(mm_new) and visible, detail, png
    finally:
        threading.Thread(target=srv.shutdown, daemon=True).start()
        srv.server_close()


def main():
    adb("wait-for-device")
    adb("logcat", "-c")
    adb("shell", "settings", "put", "global", "window_animation_scale", "0")
    adb("shell", "settings", "put", "global", "transition_animation_scale", "0")
    adb("shell", "settings", "put", "global", "animator_duration_scale", "0")
    for t in (t_install, t_launch, t_example, t_wiki, t_ublock, t_metamask, t_listed, t_wallet):
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
