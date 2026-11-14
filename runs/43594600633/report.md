# Resolute E2E: 11/12 passed

| Test | Result | Detail | Screenshot |
|---|---|---|---|
| 01-install | ✅ | Success |  |
| 02-launch | ✅ | process id 4339 | 02-launch.png |
| 03-load-example | ✅ | page title: Example Domain | 03-example.png |
| 04-load-wikipedia | ✅ | page text found | 04-wikipedia.png |
| 05-store-install-ublock-lite | ✅ | clicked 'Add to Chrome', install confirmed | 05-ublock-installed.png |
| 06-store-install-metamask | ✅ | clicked 'Add to Chrome', install confirmed | 06-metamask-installed.png |
| 07-extensions-listed | ✅ | uBlock Origin Lite page opens: True; MetaMask running: True |  |
| 08-wallet-opens | ✅ | provider: yes (isMetaMask=true); result: error 4001 User rejected the request.; screens: com.google.android.apps.chrome.Main; MetaMask pages opened: ['chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/onboarding/welcome'] | 08-after.png |
| 09-wallet-setup | ✅ | ended on /; clicked: ['Create a new wallet', 'Use Secret Recovery Phrase', 'Create password', 'Remind me later', 'Continue', 'Open wallet']; last screen buttons: ['Open wallet', 'Manage default settings'] | 09-wallet.png |
| 10-wallet-approve | ✅ | popup: chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/notification.html#/connect/o5GhdQ8zaFaKrWDDAlLX_; screens: org.chromium.chrome.browser.customtabs.TranslucentCustomTabActivity; approve clicks: ['Connect']; dApp: result: accounts 1 | 10-after.png |
| 11-wallet-after-cleanup | ✅ | closed first: ['(empty)', 'chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/', 'chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/']; popup: never opened; approve clicks: []; dApp: result: accounts 1 | 11-after.png |
| 12-open-extension-from-toolbar | ❌ | MetaMask pages opened: none; other new: [] | 12-popup.png |
