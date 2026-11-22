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

# No --disable-fre: since patch 0013 Resolute has no first-run screens, and the
# test must see the real first launch (Chrome's welcome slipped through before).
FLAGS = ("_ --no-default-browser-check --no-first-run "
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
        # Check text and description separately: an icon button has only a
        # description, and "text + ' ' + desc" broke patterns anchored with ^.
        for label in (n.get("text") or "", n.get("content-desc") or ""):
            if label and rx.search(label):
                return n
    return None


def screen_size():
    m = re.search(r"(\d+)x(\d+)", adb("shell", "wm", "size"))
    return (int(m.group(1)), int(m.group(2))) if m else (1080, 1920)


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
    # Scroll inside the menu using this screen's real size. A fixed 1080p
    # swipe started below the 320x640 emulator screen, which Android read as
    # the "go home" gesture and sent Resolute to the background (2026-11-14).
    w, h = screen_size()
    item = None
    for i in range(5):
        xml = ui_dump(f"{name}-menu{i}")
        item = find(xml, r"^Desktop site$")
        if item is not None:
            break
        if find(xml, r"^(New tab|History|Settings|Bookmarks|Downloads)$") is None:
            # Menu isn't open (yet): tap the button again.
            again = find(xml, r"Customize and control")
            if again is not None:
                tap(again)
            time.sleep(2)
            continue
        adb("shell", "input", "swipe", str(int(w * 0.7)), str(int(h * 0.75)),
            str(int(w * 0.7)), str(int(h * 0.35)), "400")
        time.sleep(1.5)
    if item is None:
        adb("shell", "input", "keyevent", "4")
        return "Desktop site item not found"
    # The setting carries over to new tabs, so only tap it when it's off.
    # The item's description says "Turn on/off Request desktop site".
    if "Turn off" in (item.get("content-desc") or ""):
        adb("shell", "input", "keyevent", "4")
        time.sleep(1)
        return "desktop site already on"
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


def cdp_on_page(url_part, fn, tries=8):
    """Runs fn(target) on the current page whose URL contains url_part.
    Ticking 'Desktop site' reloads the tab as a new DevTools target, so an old
    target id stops working ("No such target id"); look it up fresh each try."""
    last = None
    for _ in range(tries):
        t = cdp_wait_page(url_part, 10)
        if t is not None:
            try:
                res = fn(t)
                if res:
                    return res
                last = res
            except Exception as e:  # noqa: BLE001  target went away; retry
                last = f"retry after: {e}"[:200]
        time.sleep(3)
    print(f"cdp_on_page({url_part}): gave up, last={last}", flush=True)
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
    focus = focused_window()
    first_dump = ui_dump("02-first-screen")
    shot("02-first-screen")
    chrome_words = sorted(set(
        t for t in re.findall(r'(?:text|content-desc)="([^"]*\bChrome\b[^"]*)"', first_dump)
        if "Chrome Web Store" not in t))
    dismiss_popups(first_dump)
    pid = adb("shell", "pidof", PKG).strip()
    first_run = "FirstRun" in focus or "SigninFirstRun" in focus
    ok = bool(pid) and not first_run
    detail = f"process id {pid or 'none'}; first window: {focus or 'none'}"
    if chrome_words:
        detail += f"; says Chrome: {chrome_words[:5]}"
    return ok, detail, shot("02-launch")


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
    button = ("[...document.querySelectorAll('button')]"
              ".find(x => /^Add to /.test((x.innerText || '').trim()))")
    label = cdp_on_page(ext_id, lambda t: cdp_tap(t, button), 15)
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


UBLOCK_PAGE = f"chrome-extension://{UBLOCK_LITE}/dashboard.html"


def open_ublock_page():
    """Opens uBlock Origin Lite's settings page in the example.com tab
    (DevTools navigation; Android intents can't open extension pages)."""
    if cdp_wait_page(UBLOCK_PAGE, 2):
        return True
    return bool(cdp_on_page("example.com", lambda t: cdp_send(t, [
        ("Page.navigate", {"url": UBLOCK_PAGE})]), 3)) and \
        cdp_wait_page(UBLOCK_PAGE, 20) is not None


@test("07-extensions-listed")
def t_listed():
    """uBlock's own page opens (so it is installed) and MetaMask's background
    worker runs (so it is installed)."""
    ub = open_ublock_page()
    time.sleep(3)
    mm = any(t.get("type") == "service_worker" and METAMASK in t.get("url", "")
             for t in cdp_targets())
    (OUT / "07-targets.json").write_text(json.dumps(cdp_targets(), indent=1))
    return ub and mm, f"uBlock Origin Lite page opens: {ub}; MetaMask running: {mm}", None


class DappServer:
    """Serves .github/e2e/pages on the phone's localhost:8765 (adb reverse)."""

    def __enter__(self):
        import http.server, threading, functools

        class Handler(http.server.SimpleHTTPRequestHandler):
            # The browser opens spare connections it never uses; without a
            # timeout the server waited on one forever (2026-11-14).
            timeout = 10

        pages = Path(__file__).parent / "pages"
        self.srv = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 8765), functools.partial(Handler, directory=str(pages)))
        self.srv.daemon_threads = True
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        adb("reverse", "tcp:8765", "tcp:8765")
        return self

    def __exit__(self, *exc):
        import threading
        threading.Thread(target=self.srv.shutdown, daemon=True).start()
        self.srv.server_close()


DAPP = "localhost:8765/connect.html"


def top_activity():
    m = re.search(r"topResumedActivity=ActivityRecord\{\S+ \S+ (\S+)",
                  adb("shell", "dumpsys", "activity", "activities"))
    return m.group(1) if m else "unknown"


ACTIVE_TABS_JS = ("chrome.tabs.query({active: true}).then(ts => ts.map(t => ({id: t.id,"
                  " windowId: t.windowId, url: t.url || null})))")


def page_inventory():
    """Every page target with what it really is (an empty URL in /json/list
    can hide a still-running extension page, e.g. MetaMask's closed popup)."""
    out = []
    for t in cdp_targets():
        if t.get("type") != "page":
            continue
        item = {"id": t.get("id"), "listed_url": t.get("url")}
        try:
            item["real"] = cdp_eval(t, "location.href + ' | ' + document.title + ' | ' +"
                                       " (document.body ? document.body.innerText.slice(0, 120) : '')")
        except Exception as e:  # noqa: BLE001
            item["real"] = f"error: {e}"[:120]
        out.append(item)
    return out


WINDOWS_JS = ("chrome.windows.getAll({populate: true}).then(ws => ws.map(w => ({id: w.id,"
              " type: w.type, state: w.state, focused: w.focused,"
              " tabs: (w.tabs || []).map(t => t.url)})))")


def mm_windows():
    """The browser's window list as extensions see it (chrome.windows.getAll),
    read from uBlock Lite's page because MetaMask's LavaMoat hides `chrome`
    from DevTools. If MetaMask's closed popup is still listed, MetaMask focuses
    it instead of opening a new one (suspected cause of the stuck request)."""
    if not open_ublock_page():
        return "uBlock page not available"
    r = cdp_on_page(UBLOCK_PAGE, lambda t: cdp_eval(t, WINDOWS_JS), 3)
    return r if r is not None else "no answer"


def dapp_connect(tag, wait=25):
    """Opens the test dApp (desktop mode), taps Connect, and returns what
    happened: new MetaMask pages, the screen's top activity, the result."""
    if cdp_wait_page(DAPP, 3) is None:
        open_url("http://" + DAPP)
        cdp_forward()
        if cdp_wait_page(DAPP, 90) is None:
            return None
        menu_desktop_site(tag)
        time.sleep(6)
    cdp_on_page(DAPP, lambda t: cdp_send(t, [("Page.bringToFront", {})]) or True, 3)
    time.sleep(3)
    provider = cdp_on_page(DAPP, lambda t: cdp_eval(t, "document.getElementById('provider').textContent"))
    before = {t.get("id") for t in cdp_targets()}
    win_before = mm_windows()
    pages_before = page_inventory()
    active_before = cdp_on_page(UBLOCK_PAGE, lambda t: cdp_eval(t, ACTIVE_TABS_JS), 2)
    mark = logcat_mark()
    cdp_on_page(DAPP, lambda t: cdp_tap(t, "document.getElementById('go')"))
    info = {"provider": provider, "mm_new": [], "top": [], "popup": None}
    end = time.time() + wait
    while time.time() < end:
        time.sleep(2)
        info["top"].append(top_activity().split("/")[-1])
        new = [t for t in cdp_targets() if t.get("id") not in before]
        info["mm_new"] = [t["url"] for t in new if METAMASK in t.get("url", "")]
        pop = [u for u in info["mm_new"] if "notification.html" in u]
        if pop and not info["popup"]:
            info["popup"] = pop[0]
            shot(f"{tag}-popup")
    targets = cdp_targets()
    (OUT / f"{tag}-targets.json").write_text(json.dumps(targets, indent=1))
    (OUT / f"{tag}-windows.json").write_text(json.dumps(
        {"before_tap": win_before, "after": mm_windows(),
         "active_tabs_before": active_before, "pages_before": pages_before,
         "pages_after": page_inventory()}, indent=1))
    (OUT / f"{tag}-activities.txt").write_text(adb("shell", "dumpsys", "activity", "activities"))
    log = adb("logcat", "-d", "-v", "time", "-T", mark, timeout=300)
    keep = [l for l in log.splitlines() if re.search(
        r"PopupCreator|BrowserWindow|ChromeAndroidTask|CustomTab|ActivityTaskManager|"
        r"RESOLUTE_E2E|windows\.create|MetaMask|chromium.*(ERROR|FATAL)", l)]
    (OUT / f"{tag}-wallet-logcat.txt").write_text("\n".join(keep))
    info["result"] = cdp_on_page(DAPP, lambda t: cdp_eval(t, "document.getElementById('result').textContent"), 3)
    # collapse repeated activity names: Main > CustomTabActivity > Main
    info["top"] = [a for i, a in enumerate(info["top"]) if i == 0 or a != info["top"][i - 1]]
    return info


@test("08-wallet-opens")
def t_wallet_opens():
    """Connect with no wallet set up yet: MetaMask should open its window
    (on a PC it then switches to its 'Create a new wallet' page)."""
    with DappServer():
        info = dapp_connect("08")
        if info is None:
            return False, "test page did not load", shot("08-page")
        png = shot("08-after")
        return bool(info["mm_new"]), (f"{info['provider']}; {info['result']}; screens: "
                                      f"{' > '.join(info['top'])}; MetaMask pages opened: "
                                      f"{info['mm_new'] or 'none'}"), png


ONBOARD_JS = r"""(() => {
  // MetaMask's LavaMoat hides globals like HTMLInputElement and Event, so
  // passwords are typed by DevTools (Input.insertText) instead: this only
  // focuses the next empty field and asks Python to type.
  const PW = 'Resolute-e2e-Test-1!';
  const did = [];
  const pw = [...document.querySelectorAll('input[type=password]')].find(i => i.value !== PW);
  if (pw) { pw.focus(); pw.select(); return {type: true, url: location.href}; }
  // Tick boxes only on the password page ("I understand..."), not the
  // data-collection page.
  if (location.hash.includes('create-password'))
    document.querySelectorAll('input[type=checkbox]').forEach(c => {
      if (!c.checked && !c.disabled) { c.click(); did.push('checkbox'); } });
  const visible = [...document.querySelectorAll('button,[role=button]')]
    .filter(b => b.offsetParent !== null);
  const texts = visible.map(b => (b.innerText || '').trim()).filter(Boolean).slice(0, 12);
  if (did.length) return {clicked: null, did, texts, url: location.href};
  const order = [/^Use Secret Recovery Phrase/i, /^I agree/i, /^No thanks/i,
    /^Create a new wallet/i, /^Create password/i, /^Remind me later/i, /^Skip/i,
    /^Got it/i, /^Done/i, /^Next/i, /^Continue$/i, /^Confirm/i, /^Open wallet/i];
  for (const rx of order) {
    const b = visible.find(b => !b.disabled && rx.test((b.innerText || '').trim()));
    if (b) { b.click(); return {clicked: b.innerText.trim(), did, texts, url: location.href}; }
  }
  return {clicked: null, did, texts, url: location.href};
})()"""


@test("09-wallet-setup")
def t_wallet_setup():
    """Creates a throwaway MetaMask wallet inside the emulator, by pressing
    MetaMask's own onboarding buttons. Nothing is saved: the emulator is
    deleted after the run and the wallet never holds funds."""
    trace = []
    url = ""
    for _ in range(40):
        t = cdp_wait_page(METAMASK + "/home.html", 20)
        if t is None:
            trace.append("no MetaMask page")
            break
        url = t.get("url", "")
        if "onboarding" not in url and "#" in url:
            break
        try:
            step = cdp_eval(t, ONBOARD_JS)
            if isinstance(step, dict) and step.get("type"):
                cdp_send(t, [("Input.insertText", {"text": "Resolute-e2e-Test-1!"})])
                step = "typed password"
        except Exception as e:  # noqa: BLE001 page reloaded between steps
            step = f"retry: {e}"[:120]
        trace.append(step)
        time.sleep(3)
    (OUT / "09-onboarding.json").write_text(json.dumps(trace, indent=1))
    png = shot("09-wallet")
    done = "onboarding" not in url and METAMASK in url
    clicks = [x["clicked"] for x in trace if isinstance(x, dict) and x.get("clicked")]
    last = trace[-1] if trace else None
    return done, (f"ended on {url.split('#')[-1] if url else 'none'}; clicked: {clicks}; "
                  f"last screen buttons: {last.get('texts') if isinstance(last, dict) else last}"), png


APPROVE_JS = r"""(() => {
  const visible = [...document.querySelectorAll('button,[role=button]')]
    .filter(b => b.offsetParent !== null && !b.disabled);
  const b = visible.find(b => /^(Connect|Confirm|Next|Approve)$/i.test((b.innerText || '').trim()));
  if (b) { b.click(); return b.innerText.trim(); }
  return 'buttons: ' + visible.map(b => (b.innerText || '').trim()).filter(Boolean).join(' | ');
})()"""


@test("10-wallet-approve")
def t_wallet_approve():
    """The real dApp flow with a set-up wallet: tap Connect, MetaMask's
    approval window must appear on screen, approve it, the dApp gets an
    account. This is the bug seen on real phones (2026-11-13)."""
    with DappServer():
        info = dapp_connect("10", wait=15)
        if info is None:
            return False, "test page did not load", shot("10-page")
        approved = []
        if info["popup"]:
            for _ in range(5):
                r = cdp_on_page("notification.html", lambda t: cdp_eval(t, APPROVE_JS), 3)
                approved.append(r)
                time.sleep(3)
                if cdp_wait_page("notification.html", 2) is None:
                    break
        time.sleep(4)
        result = cdp_on_page(DAPP, lambda t: cdp_eval(t, "document.getElementById('result').textContent"), 3)
        png = shot("10-after")
        ok = bool(result) and "accounts" in result
        return ok, (f"popup: {info['popup'] or 'never opened'}; screens: {' > '.join(info['top'])}; "
                    f"approve clicks: {approved}; dApp: {result}"), png


@test("11-wallet-after-cleanup")
def t_wallet_cleanup():
    """Experiment: close leftover empty-URL pages and MetaMask's own tabs,
    reload the dApp, connect again. If this works while 10 doesn't, the
    leftover page (closed popup still running) is what blocks MetaMask."""
    closed = []
    for t in cdp_targets():
        u = t.get("url", "")
        if t.get("type") == "page" and (u == "" or (METAMASK in u and "home.html" in u)):
            closed.append(u or "(empty)")
            try:
                cdp_on_page(DAPP, lambda d: cdp_send(d, [("Target.closeTarget", {"targetId": t["id"]})]), 2)
            except Exception:  # noqa: BLE001
                pass
    time.sleep(3)
    cdp_on_page(DAPP, lambda d: cdp_send(d, [("Page.reload", {})]), 3)
    time.sleep(6)
    with DappServer():
        info = dapp_connect("11", wait=15)
        if info is None:
            return False, "test page did not load", shot("11-page")
        approved = []
        if info["popup"]:
            for _ in range(5):
                r = cdp_on_page("notification.html", lambda t: cdp_eval(t, APPROVE_JS), 3)
                approved.append(r)
                time.sleep(3)
                if cdp_wait_page("notification.html", 2) is None:
                    break
        time.sleep(4)
        result = cdp_on_page(DAPP, lambda t: cdp_eval(t, "document.getElementById('result').textContent"), 3)
        png = shot("11-after")
        return bool(result) and "accounts" in result, (
            f"closed first: {closed}; popup: {info['popup'] or 'never opened'}; "
            f"approve clicks: {approved}; dApp: {result}"), png


@test("12-open-extension-from-toolbar")
def t_open_extension():
    """Patch 0005: the extensions button (puzzle piece) is on the phone
    toolbar; tapping it lists extensions and tapping MetaMask opens its popup,
    like Mises and Kiwi (owner request 2026-11-14)."""
    open_url("https://example.com")
    time.sleep(6)
    xml = ui_dump("12-toolbar")
    btn = find(xml, r"^Extensions")
    if btn is None:
        return False, "no Extensions button on the toolbar", shot("12-toolbar")
    before = {t.get("id") for t in cdp_targets()}
    tap(btn)
    time.sleep(3)
    xml = ui_dump("12-menu")
    shot("12-menu")
    mm = find(xml, r"^MetaMask")
    if mm is None:
        return False, "Extensions button opened, but MetaMask not listed", shot("12-menu")
    tap(mm)
    time.sleep(6)
    png = shot("12-popup")
    ui_dump("12-popup")
    new = [t.get("url", "") for t in cdp_targets() if t.get("id") not in before]
    (OUT / "12-targets.json").write_text(json.dumps(cdp_targets(), indent=1))
    popup = [u for u in new if METAMASK in u]
    return bool(popup), f"MetaMask pages opened: {popup or 'none'}; other new: {new[:3]}", png


RESOLUTE_HOME = "aaddcaaaojbkjailacplbnladfhcnabm"  # from the key in chromium/resolute_home/manifest.json


@test("13-resolute-home")
def t_home():
    """Patch 0008: a new tab shows Resolute Home (player card, quests, Picks)
    instead of Chromium's new tab page."""
    base = cdp_targets()
    first = next((t for t in base if t.get("type") == "page"), None)
    if first is not None:
        try:
            cdp_send(first, [("Target.createTarget", {"url": "chrome://newtab/"})])
        except Exception as e:  # noqa: BLE001
            print(f"createTarget: {e}", flush=True)
    time.sleep(8)
    targets = cdp_targets()
    (OUT / "13-targets.json").write_text(json.dumps(targets, indent=1))
    home = next((t for t in targets if RESOLUTE_HOME in t.get("url", "")
                 or t.get("url", "").startswith("chrome://newtab")), None)
    png = shot("13-home")
    toolbar = ui_dump("13-toolbar")  # which toolbar views show on Resolute Home
    # Toolbar buttons must sit on one line (owner, 2026-11-22: the extensions button
    # was higher than the others; patch 0015). Compare vertical centres.
    centres = {}
    for rid in ("home_button", "extensions_menu_button", "tab_switcher_button", "menu_button"):
        m = re.search(r'resource-id="[^"]*:id/%s"[^>]*bounds="\[\d+,(\d+)\]\[\d+,(\d+)\]"' % rid, toolbar)
        if m:
            centres[rid] = (int(m.group(1)) + int(m.group(2))) / 2
    lined_up = len(centres) >= 3 and max(centres.values()) - min(centres.values()) <= 3
    # Wallet button (patch 0021): MetaMask (installed by test 06) has its own button in the
    # toolbar, inside the extension action list.
    wallet_in_bar = bool(re.search(r'resource-id="[^"]*:id/extension_action_list".*?content-desc="[^"]*MetaMask', toolbar, re.S))
    # Quick menu (patch 0019): the menu opened from the bottom bar spans the screen.
    menu_width = None
    default_item = None
    m = re.search(r'resource-id="[^"]*:id/menu_button"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', toolbar)
    if m:
        x1, y1, x2, y2 = map(int, m.groups())
        adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
        time.sleep(2)
        menu = ui_dump("13-app-menu")
        shot("13-app-menu")
        lm = re.search(r'resource-id="[^"]*:id/app_menu_list"[^>]*bounds="\[(\d+),\d+\]\[(\d+),\d+\]"', menu)
        if lm:
            menu_width = int(lm.group(2)) - int(lm.group(1))
        # Patch 0026: "Make Resolute default" (report only: it may sit below the fold).
        default_item = "Make Resolute default" in menu
        adb("shell", "input", "keyevent", "BACK")
        time.sleep(1)
    if home is None:
        return False, "no new tab page target found", png
    try:
        info = cdp_eval(home, "JSON.stringify({rank: (document.getElementById('rank')||{}).textContent,"
                              " quests: document.querySelectorAll('.quest').length, tour: !!(document.getElementById('tour') && !document.getElementById('tour').hidden),"
                              " picks: document.querySelectorAll('.pick').length, url: location.href})")
    except Exception as e:  # noqa: BLE001
        info = f"eval failed: {e}"
    ok = isinstance(info, str) and '"rank":"Level' in info and lined_up and wallet_in_bar
    return ok, f"new tab: {home.get('url')}; page: {info}; toolbar centres: {centres}; app menu width: {menu_width}; default-browser item visible: {default_item}; wallet in bar: {wallet_in_bar}", png


def focused_window():
    """The window Android sends taps to ('' when none, which is what freezes the app)."""
    out = adb("shell", "dumpsys", "window")
    m = re.search(r"mCurrentFocus=(.*)", out)
    return m.group(1).strip() if m else ""


@test("14-home-survives-rebuild")
def t_home_rebuild():
    """While Resolute Home is on screen, Android rebuilds the browser screen (here by a
    font size change, on phones also language/display changes), then the app is restarted.
    After each, the browser window must still get focus and Resolute Home must show.
    Runs 44487088816/44488598178/44491509069 froze ('isn't responding', no focused window)
    after such a rebuild."""
    steps = []
    adb("shell", "settings", "put", "system", "font_scale", "1.15")
    time.sleep(12)
    steps.append(("font bigger", focused_window()))
    shot("14-rebuild-1")
    adb("shell", "settings", "put", "system", "font_scale", "1.0")
    time.sleep(12)
    steps.append(("font normal", focused_window()))
    shot("14-rebuild-2")
    adb("shell", "am", "force-stop", PKG)
    time.sleep(2)
    adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(20)
    steps.append(("restart", focused_window()))
    png = shot("14-restart")
    ok = all(PKG in w for _, w in steps)
    return ok, "; ".join(f"{n}: {w or 'NO FOCUSED WINDOW'}" for n, w in steps), png


@test("15-tabs-and-workspaces")
def t_tabs():
    """Opens the tab switcher (screenshot for the design check) and its menu. The menu text is
    checked for "workspace" (branding step 5 renames tab groups to Workspaces): report only."""
    open_url("https://example.com/")
    # Runs before test 14 (which restarts the app): after that restart the emulator stays on
    # the start-up screen (runs 45024187419, 45025351418). Still waits for the toolbar.
    rx = r'resource-id="[^"]*:id/tab_switcher_button"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
    m, xml = None, ""
    for _ in range(20):
        xml = ui_dump()
        m = re.search(rx, xml)
        if m:
            break
        dismiss_popups(xml)
        time.sleep(3)
    (OUT / "15-toolbar.xml").write_text(xml)
    time.sleep(3)
    if not m:
        return False, "no tab switcher button on the toolbar", shot("15-toolbar")
    x1, y1, x2, y2 = map(int, m.groups())
    adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
    time.sleep(4)
    hub = ui_dump("15-tabs")
    png = shot("15-tabs")
    opened = ":id/tab_list_recycler_view" in hub or ":id/hub_" in hub
    menu_text = ""
    more = find(hub, r"^(More options|Customize and control)")
    if more is not None:
        tap(more)
        time.sleep(2)
        menu = ui_dump("15-tabs-menu")
        shot("15-tabs-menu")
        menu_text = "; ".join(sorted({n.get("text") for n in nodes(menu) if n.get("text")}))
        adb("shell", "input", "keyevent", "BACK")
        time.sleep(1)
    adb("shell", "input", "keyevent", "BACK")
    time.sleep(2)
    workspace = "orkspace" in (hub + menu_text)
    return opened, f"switcher opened: {opened}; says Workspace: {workspace}; menu: {menu_text[:300]}", png


def main():
    adb("wait-for-device")
    adb("logcat", "-c")
    adb("shell", "settings", "put", "global", "window_animation_scale", "0")
    adb("shell", "settings", "put", "global", "transition_animation_scale", "0")
    adb("shell", "settings", "put", "global", "animator_duration_scale", "0")
    for t in (t_install, t_launch, t_example, t_wiki, t_ublock, t_metamask, t_listed,
              t_wallet_opens, t_wallet_setup, t_wallet_approve, t_wallet_cleanup, t_open_extension, t_home, t_tabs, t_home_rebuild):
        t()
    (OUT / "logcat.txt").write_text(adb("logcat", "-d", "-v", "time", timeout=300))
    # "App isn't responding" and crash reports, with the stack of every thread. Android keeps
    # them in its dropbox; reading them needs no root.
    for tag in ("data_app_anr", "data_app_crash", "data_app_native_crash"):
        report = adb("shell", "dumpsys", "dropbox", "--print", tag, timeout=120)
        if "resolute" in report:
            (OUT / f"{tag}.txt").write_text(report)
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
