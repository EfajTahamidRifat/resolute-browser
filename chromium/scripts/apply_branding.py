#!/usr/bin/env python3
"""Puts Resolute's name and icon into the Chromium tree (run after the patches).

Usage: apply_branding.py <chromium src dir> <resolute chromium/ dir>

Chromium's non-Google builds take their name and launcher icons from
chrome/android/java/res_chromium_base. Instead of a patch with binary images
(which would break whenever Chromium redraws its icons), this script:
  * renames "Chromium" to "Resolute" in values/channel_constants.xml
  * finds every launcher icon PNG there and replaces it with Resolute's icon
    of the same pixel size, from chromium/branding/<kind>_<size>.png
  * calls tab groups "Workspaces" in the phone UI text (step 5)
  * replaces "Chromium" with "Resolute" in Chromium's English UI text
    (chrome/app/*chromium_strings*, components/*chromium_strings*), keeping
    "The Chromium Authors" in the copyright line
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

# 3. Text: "Chromium" -> "Resolute" in Chromium's English UI text (settings,
# chrome:// pages, dialogs). Keeps "The Chromium Authors" (the copyright line
# must credit Chromium). Other languages fall back to English for changed
# messages until translated.
STRING_FILES = sorted(
    set((src / "chrome/app").rglob("*chromium_strings*.grd*"))
    | set((src / "components").glob("*chromium_strings*.grd*"))
)
WORD = re.compile(r"(?<!The )\bChromium\b(?! Authors)")
total = 0
for f in STRING_FILES:
    text = f.read_text(encoding="utf-8")
    new, n = WORD.subn("Resolute", text)
    if n:
        f.write_text(new, encoding="utf-8")
        print(f"text: {f.relative_to(src)} ({n} x Chromium -> Resolute)")
        total += n
print(f"text done: {total} replacements in {len(STRING_FILES)} files")
if total == 0:
    sys.exit("no Chromium strings found: Chromium moved them, update apply_branding.py")

# 4. Text: "Chrome" -> "Resolute" in the phone UI text. Chromium's Android
# strings say "Chrome" directly (not the product name), e.g. "Chrome
# notifications make things easier", "Customize and control Google Chrome".
# Only the text shown to people (between <message ...> and </message>) changes,
# never message names or descriptions. "Chrome Web Store" (the real store's
# name), "Chrome OS" and "Chromebook" stay.
ANDROID_STRING_FILES = sorted(
    f
    for root in ("chrome", "components", "ui")
    for pattern in ("*.grd", "*.grdp")
    for f in (src / root).rglob(pattern)
    if "/android/" in f.as_posix() and "/test/" not in f.as_posix()
)
MESSAGE = re.compile(r"(<message\b[^>]*>)(.*?)(</message>)", re.S)
CHROME = re.compile(r"\b(?:Google )?Chrome\b(?! Web Store| OS)")


def rename_chrome(m):
    return m.group(1) + CHROME.sub("Resolute", m.group(2)) + m.group(3)


android_total = 0
for f in ANDROID_STRING_FILES:
    text = f.read_text(encoding="utf-8")
    n = sum(len(CHROME.findall(m.group(2))) for m in MESSAGE.finditer(text))
    if n:
        f.write_text(MESSAGE.sub(rename_chrome, text), encoding="utf-8")
        print(f"text: {f.relative_to(src)} ({n} x Chrome -> Resolute)")
        android_total += n
print(f"android text done: {android_total} replacements in {len(ANDROID_STRING_FILES)} files")
if android_total == 0:
    sys.exit("no Chrome strings found in Android UI text: update apply_branding.py")

# 5. Text: tab groups are called "Workspaces" in Resolute (design canvas board 4).
# Same rule as step 4: only the text people see, outside <ph> placeholders. "Tab
# group(s)" becomes "Workspace(s)" in every Android UI file. The bare noun "group" is
# renamed too where it always means a tab group: the tab UI files, messages whose
# name has GROUP in it, and the shared-group (COLLABORATION) messages. The few
# messages that use "group" as a verb get their own wording.
TAB_GROUP = [
    (re.compile(r"\b[Ss]hared [Tt]ab [Gg]roups\b"), "shared workspaces"),
    (re.compile(r"\b[Ss]hared [Tt]ab [Gg]roup\b"), "shared workspace"),
    (re.compile(r"\bTab [Gg]roups\b"), "Workspaces"),
    (re.compile(r"\btab groups\b"), "workspaces"),
    (re.compile(r"\bTab [Gg]roup\b"), "Workspace"),
    (re.compile(r"\btab group\b"), "workspace"),
]
BARE_GROUP = [
    (re.compile(r"\bgroups\b"), "workspaces"),
    (re.compile(r"\bGroups\b"), "Workspaces"),
    (re.compile(r"\bgroup\b"), "workspace"),
    (re.compile(r"\bGroup\b"), "Workspace"),
]
# Messages where "group" is a verb (whole visible text, placeholders kept as they are).
VERB_MESSAGES = {
    "IDS_UNDO_BAR_GROUP_TAB_MESSAGE": [("tab grouped", "tab added to workspace")],
    "IDS_UNDO_BAR_GROUP_TABS_MESSAGE": [("tabs grouped", "tabs added to workspace")],
    "IDS_TAB_GROUP_SUGGESTION_MESSAGE": [("Group ", "Put "), (" tabs to work faster?", " tabs in a workspace?")],
    "IDS_TAB_GROUP_SUGGESTION_MESSAGE_ACTION_TEXT": [("Group", "Create")],
    "IDS_IPH_DRAG_AND_DROP_INTRODUCTION": [("Drag tabs to group them", "Drag tabs onto each other to make a workspace")],
    "IDS_TAB_SUGGESTION_GROUP_TABS_MESSAGE": [("Group them?", "Put them in a workspace?")],
    "IDS_ACCESSIBILITY_TAB_SUGGESTION_GROUP_TABS_MESSAGE": [("Group them?", "Put them in a workspace?")],
    "IDS_TAB_SELECTION_EDITOR_UNGROUP_TABS": [("Ungroup tab}", "Remove tab from workspace}"), ("Ungroup tabs}", "Remove tabs from workspace}")],
    "IDS_ACCESSIBILITY_TAB_SELECTION_EDITOR_UNGROUP_TABS": [("Ungroup ", "Remove ")],
    "IDS_UNGROUP_TAB_GROUP_DIALOG_TITLE": [("Ungroup tab group?", "Unpack workspace?")],
    "IDS_UNGROUP_TAB_GROUP_ACTION": [("Ungroup", "Unpack")],
    "IDS_UNGROUP_TAB_GROUP_MENU_ITEM": [("Ungroup", "Unpack workspace")],
    "IDS_TAB_GROUP_SUGGESTION_ACTION_CHIP_LABEL": [("Group tabs", "Make a workspace")],
}
TAB_UI_FILES = ("android_chrome_tab_ui_strings.grd", "android_tab_ui_strings.grd")
PH = re.compile(r"(<ph\b.*?</ph>)", re.S)
NAMED = re.compile(r'(<message\b[^>]*\bname="([^"]+)"[^>]*>)(.*?)(</message>)', re.S)


def rename_groups(body, name, in_tab_ui):
    bare = in_tab_ui or "GROUP" in name or name.startswith("IDS_COLLABORATION_")
    for old, new in VERB_MESSAGES.get(name, []):
        body = body.replace(old, new)
    parts = PH.split(body)
    for i in range(0, len(parts), 2):  # even parts are outside <ph>
        rules = TAB_GROUP + (BARE_GROUP if bare else [])
        for rx, new in rules:
            parts[i] = rx.sub(new, parts[i])
    return "".join(parts)


group_total = 0
for f in ANDROID_STRING_FILES:
    text = f.read_text(encoding="utf-8")
    in_tab_ui = f.name in TAB_UI_FILES
    new = NAMED.sub(lambda m: m.group(1) + rename_groups(m.group(3), m.group(2), in_tab_ui) + m.group(4), text)
    if new != text:
        n = sum(a != b for a, b in zip(NAMED.findall(text), NAMED.findall(new)))
        f.write_text(new, encoding="utf-8")
        print(f"text: {f.relative_to(src)} ({n} messages: tab group -> workspace)")
        group_total += n
print(f"workspace text done: {group_total} messages")
if group_total == 0:
    sys.exit("no tab group strings found: update apply_branding.py step 5")

for m in missing:
    # Not fatal: the icon simply stays Chromium's until we add that size.
    print(f"WARNING no Resolute icon, left Chromium's: {m}")
if changed == 0:
    sys.exit("no launcher icons found: Chromium moved them, update apply_branding.py")
