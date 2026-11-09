# Resolute Browser

The safe browser for Web3. Free, open-source, no injected ads, no tracking.

Resolute is an Android browser built on **GeckoView** (Firefox's engine) with extension
support, built-in Web3 safety features and no Resolute server: configuration is served
from this repository and every Web3 service is called directly from the phone.

## Status: v0.0.1 (first proof of concept)

- [x] GeckoView browsing with address bar, search (DuckDuckGo), back, reload
- [x] Install Firefox add-ons from an addons.mozilla.org link, with a permission prompt
- [x] List and remove installed extensions
- [x] Opens links from other apps
- [ ] Extension toolbar buttons and popups (wallet popups as a bottom sheet)
- [ ] Tabs, bookmarks, history, downloads
- [ ] Tracker and ad blocking, phishing protection
- [ ] Chrome extension (.crx) compatibility layer
- [ ] WalletConnect, swap (LI.FI / Jupiter), partner Explore page
- [ ] Signed remote config

## Build

Every push to `main` builds a debug APK in GitHub Actions. Download it from the
**Actions** tab, open the latest run, then the `resolute-debug-apk` artifact.

Local build: open the project in Android Studio, or run `./gradlew assembleDebug`.

### Keys

Keys are never committed. CI reads them from repository secrets; local builds read
them from `local.properties`:

```
HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=...
ALCHEMY_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/...
LIFI_API_KEY=...
REOWN_PROJECT_ID=...
```

## Config

- `config/partners.json`: partner links on the Explore page
- `config/revenue.json`: swap fee settings (public wallet addresses only)

Both files will be signed; the app will reject unsigned changes.

## Security

Resolute never asks for, stores or transmits seed phrases or private keys. Wallet
extensions keep full control of signing.

**The Resolute team will never DM you first.**
