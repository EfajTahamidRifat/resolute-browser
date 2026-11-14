# Resolute E2E: 7/10 passed

| Test | Result | Detail | Screenshot |
|---|---|---|---|
| 01-install | ✅ | Success |  |
| 02-launch | ✅ | process id 4374 | 02-launch.png |
| 03-load-example | ✅ | page title: Example Domain | 03-example.png |
| 04-load-wikipedia | ✅ | page text found | 04-wikipedia.png |
| 05-store-install-ublock-lite | ✅ | clicked 'Add to Chrome', install confirmed | 05-ublock-installed.png |
| 06-store-install-metamask | ✅ | clicked 'Add to Chrome', install confirmed | 06-metamask-installed.png |
| 07-extensions-listed | ❌ | installed: none | 07-extensions.png |
| 08-wallet-opens | ✅ | provider: yes (isMetaMask=true); result: error 4001 User rejected the request.; screens: org.chromium.chrome.browser.customtabs.CustomTabActivity > com.google.android.apps.chrome.Main; MetaMask pages opened: ['chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/onboarding/welcome'] | 08-after.png |
| 09-wallet-setup | ❌ | ended on /onboarding/create-password; clicked: ['Create a new wallet', 'Use Secret Recovery Phrase']; last screen buttons: JS error: {"exceptionId": 38, "text": "Uncaught", "lineNumber": 14897, "columnNumber": 12, "scriptId": "3", "exception": {"type": "object", "subtype": "error", "className": "Error", "description": "Error: LavaMoat - property \"HTMLInputElement\" of globalThis is inaccessible under scuttling mode. To learn mor | 09-wallet.png |
| 10-wallet-approve | ❌ | popup: never opened; screens: com.google.android.apps.chrome.Main; approve clicks: []; dApp: result: error 4001 User rejected the request. | 10-after.png |
