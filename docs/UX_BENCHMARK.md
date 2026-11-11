# UX benchmark: Kiwi and Mises vs Resolute

What their interfaces do well, what they do badly, and what Resolute does about
it. This is a study of behaviour only: **no code, layouts or assets are copied**
(see `CLAUDE.md`). Sources: the Kiwi source (Chromium 105, BSD-3), read for
mechanism; the owner's screen recording of Mises (2026-11); and public reviews.
Design screens: the "Resolute Browser UI" design canvas (screens 1-10).

## 1. Kiwi: what people loved

Kiwi's power came from **settings layered on stock Chrome**, not from a new
design. From its settings screens and menu:

| Kiwi feature | Why users liked it | Resolute version |
|---|---|---|
| Bottom address bar (optional) | One-hand use on big phones | Bottom bar is the **default**, top bar optional |
| Menu shortcuts: desktop site, ad-block, night mode, DevTools, extensions | Common switches one tap away | **Quick menu** (screen 10): 8 big toggles, hold to pin your own |
| Night mode with contrast and grayscale controls | Real dark pages everywhere | "Dark pages" toggle plus per-site off switch |
| Swipe gestures (side swipe, up swipe, overscroll button) | Fast tab switching | Swipe on the bottom bar for tabs; swipe up for Quick menu |
| "Show extensions first" in the menu | Extensions felt first-class | Pinned extensions row inside the Quick menu, per site |
| Text reflow, force zoom, open in external app | Reading comfort | Text-size slider in the Quick menu; reader mode toggle |
| Chrome Web Store "mobile friendly" mode | Store usable on a phone | Same goal: store pages readable on a phone (patch later) |
| Background video play | YouTube with screen off | "Background play" toggle, Play-accepted media service |

## 2. Kiwi: where it failed

- **Looked like 2018 Chrome.** Grey menus, long settings lists, no motion.
- **Features buried** in Settings > Accessibility, where few users found them.
- **Extension popups were awkward**: full-screen pages, hard to get back to the site.
- **One mega patch** on old Chromium made updates impossible, so the browser
  fell years behind on security and died (see `docs/MARKET.md`).

## 3. Mises: what it does

From the recording: stock Chrome layout with a **beige light theme**; a bottom
bar with six buttons (home, bookmark, search, extensions, tabs, menu); a
separate DApps directory page; an extension manager (store plus zip/crx
install); MetaMask opens as a sheet over the page. It shows **ads** (AdMob /
Facebook).

| Mises weakness | Resolute answer |
|---|---|
| Six crowded bottom buttons | Four: back, address/search, tabs, menu; the rest in Quick menu |
| Beige theme, stock Chrome fonts | Dark-first `#0D0D0F` with red `#E10600`, Space Grotesk + Inter, light theme as an option |
| DApps on a separate page nobody opens | **Resolute Picks** on every new tab, plus Explore (screen 9) |
| Plain extension list | Cards with on/off switches, permission line, pinning (screen 6) |
| No help judging what a wallet signs | **Transaction X-ray** before signing (screen 3) and trust badge (screen 2) |
| Ads in the browser | No ads; revenue from swap fees and opt-in referrals |
| Wallet sheet is just the raw popup | Connect sheet shows site trust, the account, and what is shared (screen 8) |

## 4. Resolute UI rules (from this benchmark)

1. **Every common switch within two taps**, never only in Settings.
2. **Bottom-first, one hand.** Nothing important in the top 30 % of the screen.
3. **Extensions are first-class**: pinned per site, popups as sheets over the page.
4. **Safety is visible**: site trust, trackers blocked and the transaction meaning
   shown before the user acts.
5. **Motion with purpose**: sheets slide, toggles animate, 150-500 ms, and always
   respect "reduce motion".
6. **No ads, no clutter**: at most four buttons in the bottom bar.
7. **Small patches only**, so each Chromium update stays easy (`docs/MAINTAINING.md` section 5).

## 5. Build order for these UI changes

These need Chromium patches, so they come after the branding build (#2):

1. Branding (name, helmet icon, red colours), done as resource overlays.
2. Bottom toolbar on by default (upstream Chromium already has a bottom-bar
   option on Android; a small flag/default patch).
3. Quick menu sheet replacing the long app menu.
4. Pinned extension row and extension popups as bottom sheets.
5. Dark theme colours and fonts.
6. New tab page with Resolute Picks (reads `config/partners.json`).
7. Trust badge and Transaction X-ray.
