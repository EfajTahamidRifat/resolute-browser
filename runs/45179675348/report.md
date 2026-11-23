# Resolute E2E: 13/15 passed

| Test | Result | Detail | Screenshot |
|---|---|---|---|
| 01-install | ✅ | Success |  |
| 02-launch | ✅ | process id 4438; first window: Window{7c1f2b7 u0 com.resolute.browser/com.google.android.apps.chrome.Main}; rebuilt with: com.android.internal.display.cutout.emulation.corner | 02-launch.png |
| 03-load-example | ✅ | page title: Example Domain | 03-example.png |
| 04-load-wikipedia | ✅ | page text found | 04-wikipedia.png |
| 05-store-install-ublock-lite | ✅ | clicked 'Add to Chrome', install confirmed | 05-ublock-installed.png |
| 06-store-install-metamask | ✅ | clicked 'Add to Chrome', install confirmed | 06-metamask-installed.png |
| 07-extensions-listed | ✅ | uBlock Origin Lite page opens: True; MetaMask running: True |  |
| 08-wallet-opens | ✅ | provider: yes (isMetaMask=true); result: waiting for wallet; screens: org.chromium.chrome.browser.customtabs.TranslucentCustomTabActivity > com.google.android.apps.chrome.Main; MetaMask pages opened: ['chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/onboarding/welcome'] | 08-after.png |
| 09-wallet-setup | ✅ | ended on /; clicked: ['Create a new wallet', 'Use Secret Recovery Phrase', 'Create password', 'Remind me later', 'Continue', 'Open wallet']; last screen buttons: ['Open wallet', 'Manage default settings'] | 09-wallet.png |
| 10-wallet-approve | ❌ | popup: never opened; screens: com.google.android.apps.chrome.Main; approve clicks: []; dApp: result: error -32002 Request of type 'wallet_requestPermissions' already pending for origin http://localhost:8765. Please wait. | 10-after.png |
| 11-wallet-after-cleanup | ❌ | closed first: ['(empty)', 'chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/', 'chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/']; popup: never opened; approve clicks: []; dApp: result: error -32002 Request of type 'wallet_requestPermissions' already pending for origin http://localhost:8765. Please wait. | 11-after.png |
| 12-open-extension-from-toolbar | ✅ | MetaMask pages opened: ['chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/popup.html#/connect/7fr1oKNjyjxsCxFfAh68I']; other new: ['chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/popup.html#/connect/7fr1oKNjyjxsCxFfAh68I'] | 12-popup.png |
| 13-resolute-home | ✅ | new tab: chrome://newtab/; page: {"rank":"Level 3 · Navigator","quests":7,"tour":true,"picks":6,"url":"chrome-extension://aaddcaaaojbkjailacplbnladfhcnabm/index.html"}; toolbar centres: {'home_button': 1783.5, 'extensions_menu_button': 1783.5, 'tab_switcher_button': 1783.5, 'menu_button': 1783.5}; app menu width: 984; default-browser item visible: True; wallet in bar: True | 13-home.png |
| 15-tabs-and-workspaces | ✅ | switcher opened: True; says Workspace: True; menu:  | 15-tabs.png |
| 14-home-survives-rebuild | ✅ | font bigger: Window{7c1f2b7 u0 com.resolute.browser/com.google.android.apps.chrome.Main}; font normal: Window{7c1f2b7 u0 com.resolute.browser/com.google.android.apps.chrome.Main}; restart: Window{6763353 u0 com.resolute.browser/com.google.android.apps.chrome.Main}; still on start-up screen: False; Resolute Home tab title: 'New tab' | 14-restart.png |
