# Resolute E2E: 2/15 passed

| Test | Result | Detail | Screenshot |
|---|---|---|---|
| 01-install | ✅ | Success |  |
| 02-launch | ❌ | process id 4375; first window: Window{35fecb2 u0 com.resolute.browser/org.chromium.chrome.browser.firstrun.FirstRunActivity}; rebuilt with: com.android.internal.display.cutout.emulation.corner; says Chrome: ['By continuing, you agree to the Terms of Service. To help improve the app, Chrome sends usage and crash data to Google. Manage', 'By continuing, you agree to the Terms of Service. To help improve the app, Chrome sends usage and crash data to Google. Manage usage and crash data settings', 'Make Chrome your own'] | 02-launch.png |
| 03-load-example | ❌ | page title: None | 03-example.png |
| 04-load-wikipedia | ❌ | page text not found | 04-wikipedia.png |
| 05-store-install-ublock-lite | ❌ | store page not found through DevTools | 05-ublock-store.png |
| 06-store-install-metamask | ❌ | store page not found through DevTools | 06-metamask-store.png |
| 07-extensions-listed | ❌ | uBlock Origin Lite page opens: False; MetaMask running: False |  |
| 08-wallet-opens | ❌ | test page did not load | 08-page.png |
| 09-wallet-setup | ❌ | ended on none; clicked: []; last screen buttons: no MetaMask page | 09-wallet.png |
| 10-wallet-approve | ❌ | test page did not load | 10-page.png |
| 11-wallet-after-cleanup | ❌ | test page did not load | 11-page.png |
| 12-open-extension-from-toolbar | ❌ | no Extensions button on the toolbar | 12-toolbar.png |
| 13-resolute-home | ❌ | no new tab page target found | 13-home.png |
| 15-tabs-and-workspaces | ❌ | no tab switcher button on the toolbar | 15-toolbar.png |
| 14-home-survives-rebuild | ✅ | font bigger: Window{a2af3da u0 com.resolute.browser/org.chromium.chrome.browser.firstrun.FirstRunActivity}; font normal: Window{a2af3da u0 com.resolute.browser/org.chromium.chrome.browser.firstrun.FirstRunActivity}; restart: Window{8b2b5e9 u0 com.resolute.browser/org.chromium.chrome.browser.firstrun.FirstRunActivity}; still on start-up screen: False; no Resolute Home tab | 14-restart.png |
