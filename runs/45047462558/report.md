# Resolute E2E: 5/15 passed

| Test | Result | Detail | Screenshot |
|---|---|---|---|
| 01-install | ✅ | Success |  |
| 02-launch | ✅ | process id 4358; first window: Window{1669366 u0 com.resolute.browser/com.google.android.apps.chrome.Main}; rebuilt with: com.android.internal.display.cutout.emulation.corner | 02-launch.png |
| 03-load-example | ✅ | page title: Example Domain | 03-example.png |
| 04-load-wikipedia | ✅ | page text found | 04-wikipedia.png |
| 05-store-install-ublock-lite | ❌ | clicked 'Add to Chrome' (Desktop site item not found) but no install dialog appeared | 05-ublock-store.png |
| 06-store-install-metamask | ❌ | clicked 'Add to Chrome' (menu button not found) but no install dialog appeared | 06-metamask-store.png |
| 07-extensions-listed | ❌ | uBlock Origin Lite page opens: True; MetaMask running: False |  |
| 08-wallet-opens | ❌ | provider: none; result: no provider; screens: com.google.android.apps.chrome.Main; MetaMask pages opened: none | 08-after.png |
| 09-wallet-setup | ❌ | ended on none; clicked: []; last screen buttons: no MetaMask page | 09-wallet.png |
| 10-wallet-approve | ❌ | popup: never opened; screens: com.google.android.apps.chrome.Main; approve clicks: []; dApp: result: no provider | 10-after.png |
| 11-wallet-after-cleanup | ❌ | closed first: []; popup: never opened; approve clicks: []; dApp: result: no provider | 11-after.png |
| 12-open-extension-from-toolbar | ❌ | no Extensions button on the toolbar | 12-toolbar.png |
| 13-resolute-home | ❌ | new tab: chrome://newtab/; page: {"rank":"Level 1 · Explorer","quests":7,"tour":true,"picks":6,"url":"chrome-extension://aaddcaaaojbkjailacplbnladfhcnabm/index.html"}; toolbar centres: {}; app menu width: None; default-browser item visible: None; wallet in bar: False | 13-home.png |
| 15-tabs-and-workspaces | ❌ | no tab switcher button on the toolbar | 15-toolbar.png |
| 14-home-survives-rebuild | ✅ | font bigger: Window{1669366 u0 com.resolute.browser/com.google.android.apps.chrome.Main}; font normal: Window{1669366 u0 com.resolute.browser/com.google.android.apps.chrome.Main}; restart: Window{1669366 u0 com.resolute.browser/com.google.android.apps.chrome.Main}; still on start-up screen: False; Resolute Home tab title: 'New tab' | 14-restart.png |
