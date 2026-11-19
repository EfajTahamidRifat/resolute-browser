# Resolute E2E: 14/14 passed

| Test | Result | Detail | Screenshot |
|---|---|---|---|
| 01-install | ✅ | Success |  |
| 02-launch | ✅ | process id 4296 | 02-launch.png |
| 03-load-example | ✅ | page title: Example Domain | 03-example.png |
| 04-load-wikipedia | ✅ | page text found | 04-wikipedia.png |
| 05-store-install-ublock-lite | ✅ | clicked 'Add to Chrome', install confirmed | 05-ublock-installed.png |
| 06-store-install-metamask | ✅ | clicked 'Add to Chrome', install confirmed | 06-metamask-installed.png |
| 07-extensions-listed | ✅ | uBlock Origin Lite page opens: True; MetaMask running: True |  |
| 08-wallet-opens | ✅ | provider: yes (isMetaMask=true); result: error 4001 User rejected the request.; screens: org.chromium.chrome.browser.customtabs.TranslucentCustomTabActivity > com.google.android.apps.chrome.Main; MetaMask pages opened: ['chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/onboarding/welcome'] | 08-after.png |
| 09-wallet-setup | ✅ | ended on /; clicked: ['Create a new wallet', 'Use Secret Recovery Phrase', 'Create password', 'Remind me later', 'Continue', 'Open wallet']; last screen buttons: ['Open wallet', 'Manage default settings'] | 09-wallet.png |
| 10-wallet-approve | ✅ | popup: chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/notification.html; screens: org.chromium.chrome.browser.customtabs.TranslucentCustomTabActivity; approve clicks: ['Connect']; dApp: result: accounts 1 | 10-after.png |
| 11-wallet-after-cleanup | ✅ | closed first: ['(empty)', 'chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/', 'chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/']; popup: never opened; approve clicks: []; dApp: result: accounts 1 | 11-after.png |
| 12-open-extension-from-toolbar | ✅ | MetaMask pages opened: ['chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/popup.html']; other new: ['chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/popup.html', 'https://metamask.github.io/phishing-warning/v5.1.0/service-worker.js'] | 12-popup.png |
| 13-resolute-home | ✅ | new tab: chrome://newtab/; page: {"rank":"Level 3 · Navigator","quests":5,"picks":6,"url":"chrome-extension://aaddcaaaojbkjailacplbnladfhcnabm/index.html"} | 13-home.png |
| 14-home-survives-rebuild | ✅ | font bigger: Window{c8c888e u0 com.resolute.browser/com.google.android.apps.chrome.Main}; font normal: Window{c8c888e u0 com.resolute.browser/com.google.android.apps.chrome.Main}; restart: Window{91606ee u0 com.resolute.browser/com.google.android.apps.chrome.Main} | 14-restart.png |
