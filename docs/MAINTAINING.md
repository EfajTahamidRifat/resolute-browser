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
.github/workflows/chromium-update.yml       Daily check for new Chromium; bumps VERSION, starts the build

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
3. **Final stage:** finishes, produces the APK **and the Play bundle (.aab)**
   and uploads them as the artifact **`resolute-chromium-arm64`**. It also
   saves the finished `out/` as `chromium-state-arm64` (kept 14 days).
   Remaining stages are skipped automatically.
4. If 8 stages are not enough, the `not-finished` job fails. **Continue it
   instead of starting over:** Actions tab, Build Chromium APK, Run workflow,
   and enter the unfinished run's ID (the number in its URL) as
   `resume_run_id`. The new run picks up that run's saved progress (kept for
   2 days). You can also add more stages in `.github/workflows/chromium.yml`.
   Note: the workflow file a run uses is fixed when it starts, so edits to it
   only affect later runs.

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

### Fast rebuilds for small changes

After a finished build, a change to patches or branding doesn't need a day:
Actions tab, Build Chromium APK, Run workflow, and enter the **finished** run's
ID as `resume_run_id` (within 14 days). Ninja only rebuilds what the patches
touch (`build.sh` marks patched files as new). This does **not** help after a
Chromium version change or an `args.gn` change: those rebuild nearly everything.

### App size

The first APK (2026-11-12) was 552 MB: `libchrome.so` 407 MB (317 MB of it code),
all 55 MB of languages, 35 MB of resources. Cause: a developer build (DCHECK
self-checks on, no release optimisations). Fixes in `args.gn`:
`is_official_build = true` (link-time optimisation, identical-code folding, no
DCHECKs), `chrome_pgo_phase = 0`, VR/AR/XR off. And the Play bundle: Google Play
sends each phone only its own language and screen density, and compresses the
download. The APK on GitHub stays bigger than the Play download because it
holds every language. Check a new APK's breakdown before release.

Official builds end with one big **ThinLTO link** of `libchrome.so` that can run
for hours on 4 cores. It keeps finished pieces in `out/android-arm64/thinlto-cache`,
which is saved with the stage, so a link cut off at a stage deadline continues
in the next stage instead of starting over.

### Getting the APK

Actions tab, the finished run, artifact **`resolute-chromium-arm64`**. Unzip,
install on an arm64 phone. If an older Resolute with a different signing key is
installed, uninstall it first.

### Sharing a test APK

Actions tab, **Publish test APK**, Run workflow: enter the build's run ID and a
tag (e.g. `test-2026-11-12`). It creates a GitHub pre-release with the APK
attached: a direct download link that works on a phone without logging in.

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
| `Unable to locate package ...:i386` / `Temporary failure resolving 'azure.archive.ubuntu.com'` in "Install build dependencies" | The runner could not reach Ubuntu's package servers. The stage now enables i386, tries four Ubuntu mirrors, retries 3 times, and in resumed stages continues with a warning if it still fails. Re-run with `resume_run_id` to continue. |
| The final link (`libchrome.so`) runs into every stage deadline and never finishes | ThinLTO is too slow for the runner. Check `thinlto-cache` is growing between stages. If not, set `use_thin_lto = false` in `args.gn` (bigger app, but builds). |
| A resumed stage starts from zero (progress total close to a full build, e.g. `[25086/92350]` in stage 2) | The saved progress was ignored. Builds must use Ninja: keep `use_siso = false` in `chromium/args.gn`. |

---

## 4. Monthly Chromium update (DO NOT SKIP)

A browser that falls behind Chromium becomes unsafe within weeks: Chrome fixes
dozens of security holes every month, some already used by attackers. This is
what killed Kiwi. **Update at least once a month, and immediately for urgent
security releases.**

**This is automatic now.** `.github/workflows/chromium-update.yml` checks every
day (03:17 Bangladesh time) for a newer Stable Chromium for Android (Google's
version feed, Chromium Dash as fallback). If there is one and its source tag
exists, it writes it to `chromium/VERSION`, adds a status-log line here, commits
as `resolute-bot`, and starts "Build Chromium APK". If a build is already
running it does nothing and tries again the next day, so it never cancels a
build. Run it by hand from the Actions tab ("Chromium auto-update"); the
optional `version` box forces an exact version. It does **not** publish to Play:
you still test the APK and upload the update (step 5).

Doing it by hand instead:

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

Current patches:

| Patch | What it does | Why |
|---|---|---|
| `0001-gpu-no-forced-angle-vulkan.patch` | Removes three desktop-Android graphics overrides in `chrome/browser/chrome_browser_field_trials.cc` (SkipVulkanBlocklist, DefaultANGLEVulkan, VulkanFromANGLE) | The desktop-Android config forces ANGLE on Vulkan and ignores the Vulkan blocklist. On phones with older Vulkan drivers (owner's OnePlus CPH2473, Adreno, Vulkan 1.1) that gives only GLES 2.0, the GPU process fails 3 times and the browser exits: `GPU process isn't usable. Goodbye.` Without the overrides it uses Chrome for Android's normal graphics setup. On each Chromium update, check this block still exists; drop the patch if upstream adds proper runtime checks (crbug.com/376280554). |

Rules:

- One feature per patch. Keep patches small.
- Never copy code from Kiwi, Mises, Edge or any GPL project. Write our own.
- Prefer adding new files (new Java classes, new resources) over editing big
  existing Chromium files: new files almost never conflict on updates.
- Web-based features (new tab page, Explore, swap, X-ray screens) should live
  as web pages / a bundled extension so they can change without big rebuilds.

---

## 6. Testing checklist (every release)

**Automated E2E test:** Actions tab, **E2E test**, Run workflow with the APK's
direct URL (e.g. from **Publish test APK**). It boots an Android 14 emulator
(x86_64; the arm64 APK runs through Android's built-in ARM translation, so it
is slow), installs the APK and runs `.github/e2e/run_tests.py`: launch, load
example.com and wikipedia.org, install uBlock Origin Lite and MetaMask from the
Chrome Web Store, check they appear in chrome://extensions, and fail on any
crash in logcat. Report, screenshots, UI dumps and logcat go to the job
summary, an artifact, and the `e2e-results` branch (`runs/<run id>/`).

**Known limitation (2026-11-12):** the arm64 APK crashes at start on the
x86_64 emulator (native library load fails under Android's ARM translation,
then SIGSEGV). This is the emulator, not the app. For full emulator tests the
pipeline needs an x86_64 build (`target_cpu = "x64"`) built in parallel with
arm64. Until then, real-phone testing is the reference.

Manual checks on a real phone:

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
5. **Distribution decision (2026-11-10, final): one build, published on
   Google Play first.** Everything must pass Play review. Updates go through
   Play (no self-updater). Use Play App Signing; keep the upload key backed up.
6. **Publisher (2026-11-10): The Code Bros' Google Play Console.** The app can
   be moved later with Play's app transfer (users, reviews, installs, app ID
   and Play App Signing key all move; both accounts must be in good standing).
   If The Code Bros' account is an organization account, the 12-testers /
   14-days closed-test rule does not apply.
7. Google Play checklist:
   - Developer account: $25 one-time, needs a card (dual-currency debit card or
     a virtual card works); identity and address verification.
   - New personal accounts must run a **closed test with at least 12 testers
     for 14 days** before production. Collect testers early.
   - Privacy policy page (host on efajtahamid.monster), Data safety form
     (Resolute collects nothing), content rating, store listing and screenshots.
   - Crypto features: check Play's current crypto exchange / wallet policy
     before shipping swap. Play v1 ships without swap.
   - Background features limited to the Play-accepted list in the roadmap
     (media playback, PiP, downloads, scheduled list refresh, notifications).
     Node Mode is postponed.

---

### After launch (checklist)

First week:
- Play Console daily: Android vitals (crashes, ANRs; fix the top one first),
  ratings and reviews (reply to every review).
- Test on several real phones (Samsung, Xiaomi, budget models).
- Launch posts with a short demo video: X, Facebook (Bangla + English), Reddit
  (r/Android, r/androidapps, r/kiwibrowser), Product Hunt, Show HN.
- Open the Telegram community and enable its link in `config/partners.json`.

First month:
- Bug-fix update (1.0.1) before new features.
- Store listing: better screenshots, video, keywords ("extensions browser",
  "Kiwi alternative", "Web3 browser"), translations (Bangla, Hindi, Spanish,
  Indonesian).
- First routine monthly Chromium update (section 4).
- Weekly numbers in Play Console: installs, uninstalls, daily users,
  day-7 / day-30 retention.
- Confirm Resolute Picks referrals register in partner dashboards; enable
  referral prompts only for partners whose terms allow it.

Months 2-6:
- Roadmap in order, guided by user requests (X-ray, workspaces, swap after the
  Play policy check, background media).
- Grants: Gitcoin, Solana Foundation, Optimism and similar.
- Case study on portfolio / agency site; white-label offers to crypto projects.
- Find a second maintainer as soon as revenue or grants allow.

Always: monthly security updates + emergency fixes within days; report fake
"Resolute" apps to Google; keep this handbook updated.

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
  partner, the "never DM you first" notice, and `official` (owner's social
  accounts and "Hire us" link shown in About, new-tab footer and Explore footer;
  Telegram is a placeholder, set the URL and `enabled: true`). `labels` sets
  the words shown (section title, "See all", badge); the `disclosure` line must
  always stay visible because Resolute earns commission from these links.
- Referral prompt (`referral_prompt` in `partners.json`): when a user opens a
  Pick's **sign-up page** on their own, Resolute may offer once: "Use Resolute
  link / No thanks". Never shown if the page already carries someone's referral
  code, max once per site, global off switch in Settings, always discloses the
  commission. **Off for every partner by default**: read that partner's
  affiliate terms (some ban browser/software prompts), then set
  `terms_checked: true` and `enabled: true`. Fill `user_benefit` if the referral
  gives the user something (e.g. a fee discount).
- Pick icons: `.github/workflows/pick-icons.yml` runs
  `config/scripts/fetch_icons.py` (on partners.json changes, weekly, or by
  hand). It visits each partner site, keeps its best icon as a 128 px PNG in
  `config/icons/<id>.png` and sets the partner's `icon` field. Sites that block
  it keep their previous icon; the app falls back to a letter tile. Optional
  `icon_site` on a partner sets which site the icon is taken from. To use an
  official brand-kit icon instead, replace the PNG by hand (same file name). Edit, (sign), push: users get it
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
Inter. Share or export it if working from another account. Screen 10 is the
Quick menu. `docs/UX_BENCHMARK.md` compares Kiwi's and Mises' UI with Resolute
and sets the UI rules (two-tap switches, bottom-first, no ads, small patches).
The full UI plan (18 screens, design tokens, Web3 safety UI, 5 build phases,
quality targets) is the Claude Doc "Resolute Browser: UI plan" in the owner's
account: https://claude.ai/artifact/66CRSmaYDQZg3kxjUvBXNT (export it to keep a
copy). Phases 1-3 (brand, core shell, safety/Web3) come before the Play launch.

Roadmap after the first working APK:

1. Branding (name, helmet icon, colours) + own icon set via resource overlay
2. New bottom toolbar UI
3. Wallet popup as a Resolute bottom sheet + trust strip
4. Trust badge + scam-site blocking (public phishing lists, on device)
5. Transaction X-ray
6. Workspaces and new tab switcher
7. Desktop mode polish (tab strip, split view, shortcuts)
8. Faster rebuilds (compiler cache), release signing, automated emulator tests
9. Partners: a "Resolute Picks" row on every new tab (tiles with `newtab_tile: true`
   in `config/partners.json`, "See all" opens Explore) + full Explore page
   (groups, risk labels, disclosure, official accounts, Hire us); LI.FI +
   Jupiter swap with visible fees; signed config
10. Encrypted sync through the user's own storage (no server)
11. **Background features Play accepts** (each uses a standard, declared
    Android mechanism):
    - Background audio/video playback with screen off + media notification
      (foreground service type `mediaPlayback`)
    - Picture-in-picture video
    - Downloads that continue in the background (Chromium download service,
      `dataSync`), pause/resume, Wi-Fi-only option
    - Daily background refresh of scam/phishing lists, filter lists and
      `config/*.json` via WorkManager (no server, battery-friendly)
    - Local notifications: download done, reminders
    - Web push notifications from sites (needs a free Firebase project; later)
    Declare every foreground service type in the Play Console declaration form.
12. **PWA / web apps**: "Install app" for sites with a web app manifest
    (address-bar install button + menu item). Installed apps open standalone
    (no browser UI), with the site's icon, name, theme colour and splash
    screen, and work offline through service workers. Also an "Apps" section
    on the new tab and in Settings to manage them.
    Limitation: Chrome installs PWAs as real apps ("WebAPKs") using Google's
    WebAPK server, which other Chromium browsers can't use. Resolute installs
    them as home-screen shortcuts that open standalone: same look and feel,
    but they don't appear in the app drawer list or as share targets.
    A Resolute WebAPK service would need a server: not planned.
13. Node Mode (always-on extension nodes): **postponed** (2026-11-10).
14. **Windows version (phase 2, after Android v1 launches).** Same Chromium
    version and config; desktop Chromium supports Chrome Web Store extensions
    natively. Needs: a separate chained build on GitHub's free Windows runners
    (first build roughly 2-3 days), Resolute's desktop UI patches (C++ Views /
    WebUI, same design), an updater (GitHub Releases check, or Microsoft Store),
    and code signing (SignPath Foundation for open source, or Microsoft Store).
    Node Mode returns here as the headline desktop feature.

**Rule from now on:** build Resolute features (new tab, Resolute Picks, Explore,
Transaction X-ray, trust/scam protection, swap) as **web pages or a built-in
extension**, not Android-only Java, wherever possible, so Android and Windows
share the same code.

Business model: swap/perps integrator fees, partner links (disclosed),
Resolute Pro (one-time), grants, white-label builds. No injected ads.

---

## 11. Status log

- 2026-11-10: GeckoView prototype v0.0.1 built and installed (`app/`).
  Switched to Chromium for Chrome Web Store support. First Chromium build
  (Chromium 156, run 42754882920): stage 1 reached 29 % (26,603 / 91,334
  steps), stage 2 running. Expected APK in stage 4.

- 2026-11-10: Run 42754882920 stages 1-2 each compiled ~27% but stage 2 started
  from zero: Chromium's default Siso builder ignored the restored progress.
  Fixed with `use_siso = false` (Ninja); build restarted.
- 2026-11-11: Run 42831322427 (Ninja): stage 1 [23939/63109]; stage 2 resumed
  correctly at [1/39170] (resume works) but only reached 6,054 steps (V8 and
  Blink are slow). Added `resume_run_id` so an unfinished run can be continued
  by a new run.
- 2026-11-11: Run 42831322427 stage 3 resumed at [1/33116], reached 5,168
  (Blink is slow, ~1,200 steps/hour). ~28,000 steps left: likely needs a
  follow-up run with `resume_run_id=42831322427` after stage 8.
- 2026-11-11: Repo made **public** (Apache-2.0 LICENSE + NOTICE). Private repos
  only get 2,000 free Actions minutes/month and 500 MB artifact storage; the
  Chromium build used them up. Public repos get free unlimited standard
  runners. History was scanned: no keys were ever committed.
- 2026-11-11: Stage 4 resumed at [1/27948], reached 8,706 (faster, ~2,000
  steps/hour). ~19,200 steps left; expected to finish in stage 6 or 7.
- 2026-11-11: Stage 5 reached [9726/19242] (~9,500 steps left). Stage 6 failed
  in setup (apt could not find i386 packages). Added i386 + apt retry; continued
  with run 43040211122 (`resume_run_id=42831322427`).
- 2026-11-11: Resume run 43040211122 failed in setup too: the runner could not
  resolve Ubuntu's mirrors (DNS). Added fallback mirrors and made the deps step
  non-fatal for resumed stages; re-dispatched with `resume_run_id=42831322427`.
- 2026-11-12: **First Chromium APK built** (run 43070434004, resumed from run
  42831322427): last 9,516 steps in ~2 h. Artifact `resolute-chromium-arm64`,
  APK 552 MB (non-official build, no size optimisation yet). Plain Chromium UI;
  next: install test (Chrome Web Store, MetaMask, Phantom), then save build
  output for fast incremental builds, branding, size reduction.
- 2026-11-12: E2E emulator workflow added and run (43111818432): install OK,
  arm64 APK crashes under the emulator's ARM translation. Plan: x86_64 test
  build in parallel; real-phone test now.
- 2026-11-10: Market research added (`docs/MARKET.md`). Positioning: power-user
  browser with the best Web3 safety, not "only a crypto browser". MV3 first.

- 2026-11-10: Decided one build only, **Google Play first**. Play v1: browser,
  Chrome Web Store extensions, Resolute UI, Resolute Picks, trust/scam
  protection. Later: X-ray, workspaces, swap (after policy check).
- 2026-11-10: Node Mode postponed. Added Play-accepted background features
  (background media + PiP, background downloads, daily list refresh,
  notifications) to the roadmap.
- 2026-11-10: PWA install (standalone home-screen web apps) added to the roadmap.
- 2026-11-10: Windows version planned as phase 2; features to be built as
  shared web code.
- 2026-11-12: UI benchmark of Kiwi and Mises written (`docs/UX_BENCHMARK.md`,
  study only, no code copied). Added screen 10 "Quick menu" to the design canvas.
- 2026-11-12: Added daily Chromium auto-update workflow (`chromium-update.yml`).
- 2026-11-12: Auto-update: Chromium 156.0.8078.47 -> 158.0.8127.22 (chromium-update workflow). Build started.
- 2026-11-12: App size work. Measured the first APK (552 MB; libchrome.so 407 MB).
  args.gn: official build, no DCHECKs, no PGO, VR/AR/XR off. Build now also
  makes the Play bundle (.aab) and saves the finished build for fast rebuilds.
  This restarted the Chromium 158 build (it had run about 45 min).
- 2026-11-12: First real-phone test of the 156 test APK: installs and opens,
  loads google.com, then closes by itself after a few seconds (crash), twice.
  Likely a DCHECK self-check failing (the test build had them on and they stop
  the app); the official build in progress turns them off. Asked owner for an
  Android bug report to confirm.
- 2026-11-12: Owner's bug report (OnePlus CPH2473, Android 13) showed the real
  crash: `GPU process isn't usable. Goodbye.` The desktop-Android config forces
  ANGLE on Vulkan; this phone's Vulkan driver only gives GLES 2.0. Added patch
  0001 (normal Android graphics setup). Also seen: the 410 MB libchrome.so was
  too big for Android's shared-memory reservation (208 MB); the official build
  should fix that. Restarted the Chromium 158 build with the patch.
- 2026-11-12: Full UI plan written (Claude Doc, linked in section 10).

Add a line here after every build or release.

---

## 12. Continuing with an AI assistant (any account)

1. Give it access to this repo (or upload a zip of it).
2. Ask it to read `CLAUDE.md` and this file first.
3. Tell it the current task, e.g. "do the monthly Chromium update" or "add the
   branding patch", and paste the latest build log line if something failed.
