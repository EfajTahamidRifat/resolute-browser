# Market research: Android browsers with extensions and Web3

Researched 2026-11-10. Update this file when the market changes.

## 1. The landscape

### A. Chromium browsers that run Chrome extensions on Android (direct competitors)

| Browser | Who | Open source | Status | Notes |
|---|---|---|---|---|
| **Kiwi** | Geometry OU (1 developer) | Yes (BSD) | **Dead since Jan 2025** | Millions of users. Died from maintenance burden; stuck on old Chromium. Code went to Edge Canary. |
| **Microsoft Edge Canary** | Microsoft | No | Experimental | Extensions hidden behind developer options, install by ID. Not for daily use. |
| **Chrome** | Google | No | No extensions on phones | Google builds extensions for "desktop Android" devices (tablets, laptops). If this reaches phones, "has extensions" stops being special. **Biggest long-term threat.** |
| **Quetta** | Company (Quetta.net) | Not clear | Active | MV3 extensions, privacy marketing, positions itself as the Kiwi replacement. |
| **Titanium** (was "Helium" on Android) | jqssun | **Yes, GPL-2.0** (~770 stars) | Active, Chromium 150 | MV2 + MV3, Chrome Web Store via desktop-site mode, builds on GitHub Actions. Closest to Resolute's technical approach. Study only (GPL). |
| **Bare Browser** | 3-person team | Yes | New (Oct 2026) | MV2, uBlock bundled, CRX install, dev tools, background media, AMOLED. Store installs awkward on mobile. |
| **Mises** | Mises Network | Partly | Updates slowing (last Play update seen June 2025) | Web3 angle (DApp list), extensions. **Shows ads (AdMob / Facebook) and Firebase analytics.** Stock Chrome UI. |
| **Lemur**, **Yandex** | Companies (China / Russia) | No | Active | Extensions work; trust/privacy concerns for many users. |

### B. Privacy browsers without Chrome extensions

| Browser | Notes |
|---|---|
| **Brave** | Open source (MPL-2.0). ~121M monthly users, ~51M daily (June 2026). Built-in wallet, ad/tracker blocking. Revenue: search ads, privacy ads, API, crypto deals, premium. No Chrome extensions on Android. The benchmark for "privacy browser that makes money". |
| **Cromite** | Open source (GPL). Successor of Bromite. Strong privacy patches, built-in ad blocker. No extensions. |
| **Firefox / IronFox / Iceraven** | Gecko engine. Firefox add-ons on Android officially. Not Chrome Web Store. |

### C. Web3 apps with a DApp browser

MetaMask Mobile, Trust Wallet, Phantom, OKX Wallet, Rabby Mobile: a wallet with a
basic in-app browser. Good for one wallet, poor as a real browser (no extensions,
weak tabs, no desktop mode).

**Opera Crypto Browser** (a dedicated crypto browser from a big company) was
**delisted in Feb 2024**. Lesson: "crypto browser" alone was not enough for Opera.

## 2. What this means for Resolute

1. **Demand is proven.** Kiwi had millions of users, and several small projects
   appeared after it died. People want extensions on their phone.
2. **"Extensions on Android" alone is no longer a moat.** Quetta, Titanium, Bare,
   Edge Canary all do it, and Google may bring it to Chrome. Resolute must win on
   what the others lack:
   - **Design and speed**: nearly all of them use the stock Chrome UI.
   - **Web3 safety** (trust badge, Transaction X-ray, scam blocking): none of the
     extension browsers have it; wallets only protect inside their own app.
   - **Desktop environment** (workspaces, tab strip, split view, DeX).
   - **No ads, no tracking**, open source: a clear contrast with Mises (AdMob,
     Facebook ads) and closed browsers (Lemur, Yandex, Quetta).
3. **Don't be "only a crypto browser".** Opera's crypto browser failed. Position
   Resolute as *the power-user browser with the best Web3 safety*: useful to
   everyone, essential for crypto users.
4. **Revenue model is validated.** Brave earns from search, ads and crypto deals
   at scale. Resolute's model (swap/perps fees, disclosed partners, Pro, grants)
   is similar but without ads in pages.
5. **Maintenance is the killer.** Every small project here faces the same test as
   Kiwi: keeping Chromium updated. Monthly updates are Resolute's survival rule.

## 3. Open decision: Manifest V2

Titanium and Bare advertise **MV2 support** (full uBlock Origin), which users
love. Chromium upstream is removing MV2, so keeping it means extra patches every
update. Current plan: **MV3 first** (uBlock Origin Lite works), revisit MV2 once
the base browser is stable and updates are routine.

## 4. Open-source projects worth studying (never copy GPL code)

| Project | License | Learn from |
|---|---|---|
| Titanium (jqssun/android-titanium-browser) | GPL-2.0 | Chromium-on-Android extension build, CI setup, MV2 handling |
| Cromite (uazo/cromite) | GPL | Privacy patches, built-in ad blocking, patch maintenance across versions |
| Brave (brave/brave-core) | MPL-2.0 | Wallet integration, ad blocking engine, business model |
| Bare Browser | Open source | Mobile dev tools, background media, downloader integration |
| MetaMask Mobile | see repo | DApp connection and signing UX |
| ungoogled-chromium | BSD | Removing Google services, chained CI builds |

## Sources

- https://extensionbooster.net/blog/chrome-extensions-android-2026-what-works-guide/
- https://piunikaweb.com/2026/07/16/helium-browser-now-called-titanium-android/
- https://awesome.ecosyste.ms/projects/github.com%2Fjqssun%2Fandroid-helium-browser
- https://piunikaweb.com/2026/10/20/bare-browser-android-review-extension-support/
- https://piunikaweb.com/2026/07/02/brave-nears-121m-monthly-users-search-hits-new-all-time-high/
- https://appgoblin.info/apps/site.mises.browser
- https://blogs.opera.com/news/2024/02/opera-delists-the-experimental-crypto-browser/
- https://www.androidcentral.com/apps-software/chrome-for-android-is-getting-extensions-but-not-like-youd-expect
- https://androidauthority.com/kiwi-browser-shutting-down-3519510
