# Resolute E2E: 6/8 passed

| Test | Result | Detail | Screenshot |
|---|---|---|---|
| 01-install | ✅ | Success |  |
| 02-launch | ✅ | process id 4142 | 02-launch.png |
| 03-load-example | ✅ | page title: Example Domain | 03-example.png |
| 04-load-wikipedia | ✅ | page text found | 04-wikipedia.png |
| 05-store-install-ublock-lite | ✅ | clicked 'Add to Chrome', install confirmed | 05-ublock-installed.png |
| 06-store-install-metamask | ✅ | clicked 'Add to Chrome', install confirmed | 06-metamask-installed.png |
| 07-extensions-listed | ❌ | running/listed: MetaMask | 07-extensions.png |
| 08-wallet-connect | ❌ | provider: yes (isMetaMask=true); result: error 4001 User rejected the request.; new MetaMask pages: ['chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#/onboarding/welcome']; other new targets: ['', 'https://metamask.github.io/phishing-warning/v5.1.0/service-worker.js']; MetaMask visible on screen=False | 08-after.png |
