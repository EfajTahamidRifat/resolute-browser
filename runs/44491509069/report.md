# Resolute E2E: 5/13 passed

| Test | Result | Detail | Screenshot |
|---|---|---|---|
| 01-install | ✅ | Success |  |
| 02-launch | ✅ | process id 4377 | 02-launch.png |
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
| 13-resolute-home | ✅ | new tab: chrome://newtab/; page: {"rank":"Level 1 · Explorer","quests":5,"picks":6,"url":"chrome-extension://aaddcaaaojbkjailacplbnladfhcnabm/index.html"} | 13-home.png |
