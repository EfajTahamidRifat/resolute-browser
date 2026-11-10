# Resolute Browser: Maintainer Handbook

Everything needed to keep building, updating and releasing Resolute, written so
that anyone (you on another account, a new contributor, or a new AI session) can
pick up the work without the original conversation.

Last updated: 2026-11-10. Owner: Efaj Tahamid Rifat (GitHub `EfajTahamidRifat`).

---

## 1. What Resolute is

A free, open-source **Android browser built on Chromium** for crypto and power
users:

- Real **Chrome Web Store extension** support (MetaMask, Phantom, uBlock, ...)
- A **desktop-like environment**: tab strip, workspaces, split view, keyboard and
  mouse, external monitor / Samsung DeX
- **Web3 safety**: trust score in the address bar, scam-site blocking,
  "Transaction X-ray" (plain-language warning before signing)
- **No injected ads, no data selling, no Resolute server.** Configuration is
  served from this repo; every Web3 service is called directly from the phone.

### Key decisions (and why)

| Decision | Why |
|---|---|
| **Chromium engine** (not GeckoView/WebView) | Only way to get real Chrome Web Store extensions on Android. |
| **`is_desktop_android = true`** | Chromium's official, upstream extension support for Android. We do NOT carry a giant extension patch like Kiwi did; that is what made Kiwi impossible to maintain. |
| **Small, separate patches** in `chromium/patches/` | Each Resolute feature is its own patch, so a Chromium update breaks at most a few, which are quick to fix. |
| **Build on free GitHub Actions** (chained stages) | No credit card / no paid server. Cost: a full build takes about a day. |
| **No runtime server** | Config files on GitHub (signed), Web3 via LI.FI / Jupiter / RPC providers. |
| **Do not copy Kiwi / Mises / Edge code** | Resolute is written by us. Kiwi's extension patches are GPL-3; Kiwi's icon pipeline used paid Font Awesome Pro icons. We only learn from how they work. |

---

## 2. Repository layout

```
chromium/                     THE MAIN BROWSER (Chromium-based)
  VERSION                     Chromium version to build, e.g. 156.0.8078.47
  args.gn                     GN build arguments (package name, extensions, codecs, ...)
  patches/                    Resolute's own changes, applied in filename order
  scripts/sync.sh             Downloads Chromium source (no history, skips test deps)
  scripts/build.sh            Applies patches, builds chrome_public_apk, resumable
.github/actions/chromium-stage/action.yml   One build stage (sync, restore, build, save)
.github/workflows/chromium.yml              Up to 8 chained stages -> APK

app/                          OLD GeckoView prototype (v0.0.1). Kept for reference only.
.github/workflows/build.yml   Builds the GeckoView prototype (minutes, not Chromium).

config/partners.json          Partner links on the Explore page (to be signed)
config/revenue.json           Swap fee settings (public wallet addresses only)
branding/                     Icons: helmet logo, Play Store icon, Android icon set
docs/MAINTAINING.md           This file
docs/MARKET.md                Competitors, market lessons, open decisions (e.g. MV2)
CLAUDE.md                     Short brief for AI assistants working in this repo
```

---

## 3. How the Chromium build works

Chromium is too big to compile in one GitHub job (6-hour limit, 4 CPU cores), so
the workflow runs as **chained stages**:

1. **Stage 1:** frees disk space on the runner, installs build tools, downloads
   Chromium (about 25 min), applies `chromium/patches/`, compiles until about
   4h50m, then compresses the build output (`out/`) and uploads it as the
   artifact `chromium-state-arm64`.
2. **Stages 2 to 8:** each downloads Chromium again, restores the previous
   stage's `out/`, and **continues compiling where it stopped**.
3. **Final stage:** finishes, produces the APK and uploads the artifact
   **`resolute-chromium-arm64`**. Remaining stages are skipped automatically.
4. If 8 stages are not enough, the `not-finished` job fails. Add more stages in
   `.github/workflows/chromium.yml` (copy a stage block, chain `needs`).

Numbers from the first build (Chromium 156, arm64):

- About **91,000 build steps**; about **6,100 steps per hour** on a free runner
- About **4 stages** for a full build from scratch (roughly a day)
- Disk: about 24 GB free after download, about 5 GB of build output per 30 %
  progress. Disk is the tightest resource.

### Triggering a build

- Any push that changes `chromium/**`, `.github/actions/chromium-stage/**` or
  `.github/workflows/chromium.yml` starts a build.
- Or: GitHub, **Actions** tab, **Build Chromium APK**, **Run workflow**.
- **A new build cancels the one already running** (`cancel-in-progress`). Do not
  push to `chromium/` while a build you care about is running.

### Getting the APK

Actions tab, the finished run, artifact **`resolute-chromium-arm64`**. Unzip,
install on an arm64 phone. If an older Resolute with a different signing key is
installed, uninstall it first.

### Reading logs

Logs of a job are only visible after that job finishes. Useful lines:

- `[26603/91334]` = ninja progress (done / total steps)
- `/dev/root  72G  53G  19G` = disk usage (watch the free column)
- `stopped at deadline ... next stage resumes` = normal hand-over
- the `disk usage` group after sync = biggest folders, if disk runs out

With the GitHub CLI: `gh run list --workflow chromium.yml`,
`gh api repos/EfajTahamidRifat/resolute-browser/actions/jobs/<job-id>/logs`.

### Common failures and fixes

| Symptom | Fix |
|---|---|
| `no space left on device` during sync or build | Remove more preinstalled runner software in `action.yml` (first step), add test-only deps to `custom_deps` in `sync.sh`, or delete unused folders after sync. Check the `disk usage` group to see what is big. |
| Sync fails with HTTP 429 / timeout | googlesource rate limit. Re-run the workflow. Lower `--jobs` in `sync.sh` if it repeats. |
| A patch fails to apply (`git apply` error) | Chromium changed that file. Update the patch (section 5). |
| Compile error in a Resolute file | Fix the patch. The log line starting with `FAILED:` names the file. |
| Build too slow / more than 8 stages | Add stages, or reduce work in `args.gn`. |

---

## 4. Monthly Chromium update (DO NOT SKIP)

A browser that falls behind Chromium becomes unsafe within weeks: Chrome fixes
dozens of security holes every month, some already used by attackers. This is
what killed Kiwi. **Update at least once a month, and immediately for urgent
security releases.**

1. Find the latest **Stable** Chromium version for Android:
   <https://chromiumdash.appspot.com/releases?platform=Android>
2. Edit `chromium/VERSION` to that version (e.g. `157.0.xxxx.yy`). Commit and push.
3. The build starts. Watch the Actions tab. A version update is close to a full
   build (about a day).
4. If a patch fails to apply: update that patch (section 5). If a feature
   patch is hard to fix, **ship the security update without that feature**
   (move the patch out of `chromium/patches/` temporarily) and fix it later.
   Security first.
5. Test the APK (section 6), then release (section 7).

---

## 5. Adding or updating a Resolute patch

Patches are normal `git diff` files with paths relative to Chromium's `src/`
(e.g. `a/chrome/android/java/res/values/colors.xml`). They are applied in
filename order, so name them `0001-branding.patch`, `0002-toolbar.patch`, ...

Without a full Chromium checkout (the usual case here), for small changes:

1. Download the exact file at the pinned version:
   `https://chromium.googlesource.com/chromium/src/+/refs/tags/<VERSION>/<path>?format=TEXT`
   (the response is base64: decode it).
2. Copy it, edit the copy, and make a diff with `src`-relative paths:
   ```
   mkdir -p a/<dir> b/<dir>
   cp original a/<path>; cp edited b/<path>
   git diff --no-index a/<path> b/<path> > 0005-my-feature.patch
   ```
   Check the header lines read `a/<path>` and `b/<path>`.
3. New files: diff against `/dev/null`.
4. Put the patch in `chromium/patches/`, commit, push, watch the build.

Rules:

- One feature per patch. Keep patches small.
- Never copy code from Kiwi, Mises, Edge or any GPL project. Write our own.
- Prefer adding new files (new Java classes, new resources) over editing big
  existing Chromium files: new files almost never conflict on updates.
- Web-based features (new tab page, Explore, swap, X-ray screens) should live
  as web pages / a bundled extension so they can change without big rebuilds.

---

## 6. Testing checklist (every release)

- [ ] App installs and opens; no crash on start
- [ ] Browse 10 popular sites (news, X, YouTube, a DEX, a block explorer)
- [ ] Chrome Web Store opens; "Add to Chrome" installs uBlock Origin Lite
- [ ] MetaMask and Phantom install; popup opens; connect to a DApp; sign a message
- [ ] Back / forward / tabs / downloads / incognito work
- [ ] Desktop site toggle works
- [ ] About page shows the new Chromium version

---

## 7. Releasing

Current state: builds are signed with Chromium's public **debug key**. Fine for
testing, **not for public release**.

Before the first public release:

1. Create a release keystore **on your own computer**:
   `keytool -genkey -v -keystore resolute-release.jks -alias resolute -keyalg RSA -keysize 4096 -validity 10000`
2. **Back it up in two safe places.** If this keystore is lost, you can never
   update the app on Google Play again. Never commit it.
3. Add it to GitHub secrets (base64 of the file + passwords) and wire the
   `android_keystore_*` GN args into the workflow (to do).
4. App ID is `com.resolute.browser` (`chromium/args.gn`). It becomes permanent
   once published on Google Play.
5. Publish APK on GitHub Releases; later Google Play ($25 account) and F-Droid.

---

## 8. Secrets, keys and accounts

**Never commit secrets.** Keys live in GitHub: repo **Settings, Secrets and
variables, Actions**. Required names:

| Secret | What |
|---|---|
| `HELIUS_RPC_URL` | Solana RPC URL incl. key (helius.dev dashboard) |
| `ALCHEMY_RPC_URL` | EVM RPC URL incl. key (alchemy.com dashboard) |
| `LIFI_API_KEY` | LI.FI partner portal (portal.li.fi) |
| `REOWN_PROJECT_ID` | WalletConnect / Reown dashboard |

Public values (safe in the repo): EVM fee wallet in `config/revenue.json`.
Still needed: LI.FI **integrator string** (portal.li.fi), Solana fee address.

Never put in the repo or in the app: seed phrases, wallet private keys, the
config-signing private key, the release keystore or its passwords.

Accounts used: GitHub (code, builds, config hosting), Helius, Alchemy, LI.FI
partner portal, Reown (WalletConnect). Later: Google Play Console, F-Droid.

---

## 9. Config files (no server)

- `config/partners.json`: Explore page partner links, groups, on/off per
  partner, the "never DM you first" notice. Edit, (sign), push: users get it
  without an app update.
- `config/revenue.json`: swap fee settings.
- **To do:** sign both files with an Ed25519 key kept only on the owner's
  computer; the app must reject unsigned files (protects fee wallets if the
  GitHub account is ever compromised).

---

## 10. Design and roadmap

The UI design is a canvas in the owner's Claude account ("Resolute Browser UI"):
new tab, browsing with trust badge, Transaction X-ray, tabs and workspaces,
command menu, extensions, connect-wallet flow, desktop mode. Colours: background
`#0D0D0F`, surfaces `#17171B`, red `#E10600`; fonts Space Grotesk (headings) and
Inter. Share or export it if working from another account.

Roadmap after the first working APK:

1. Branding (name, helmet icon, colours) + own icon set via resource overlay
2. New bottom toolbar UI
3. Wallet popup as a Resolute bottom sheet + trust strip
4. Trust badge + scam-site blocking (public phishing lists, on device)
5. Transaction X-ray
6. Workspaces and new tab switcher
7. Desktop mode polish (tab strip, split view, shortcuts)
8. Faster rebuilds (compiler cache), release signing, automated emulator tests
9. Explore page, LI.FI + Jupiter swap with visible fees, signed config
10. Encrypted sync through the user's own storage (no server)

Business model: swap/perps integrator fees, partner links (disclosed),
Resolute Pro (one-time), grants, white-label builds. No injected ads.

---

## 11. Status log

- 2026-11-10: GeckoView prototype v0.0.1 built and installed (`app/`).
  Switched to Chromium for Chrome Web Store support. First Chromium build
  (Chromium 156, run 42754882920): stage 1 reached 29 % (26,603 / 91,334
  steps), stage 2 running. Expected APK in stage 4.

- 2026-11-10: Market research added (`docs/MARKET.md`). Positioning: power-user
  browser with the best Web3 safety, not "only a crypto browser". MV3 first.

Add a line here after every build or release.

---

## 12. Continuing with an AI assistant (any account)

1. Give it access to this repo (or upload a zip of it).
2. Ask it to read `CLAUDE.md` and this file first.
3. Tell it the current task, e.g. "do the monthly Chromium update" or "add the
   branding patch", and paste the latest build log line if something failed.
