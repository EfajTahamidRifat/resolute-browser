# Resolute E2E: 4/8 passed

| Test | Result | Detail | Screenshot |
|---|---|---|---|
| 01-install | ✅ | Success |  |
| 02-launch | ✅ | process id 4391 | 02-launch.png |
| 03-load-example | ✅ | page title: Example Domain | 03-example.png |
| 04-load-wikipedia | ✅ | page text found | 04-wikipedia.png |
| 05-store-install-ublock-lite | ❌ | clicked 'Add to Desktop' (menu button not found) but no install dialog appeared | 05-ublock-store.png |
| 06-store-install-metamask | ❌ | clicked 'Add to Desktop' (menu button not found) but no install dialog appeared | 06-metamask-store.png |
| 07-extensions-listed | ❌ | running/listed: MetaMask | 07-extensions.png |
| 08-wallet-connect | ❌ | provider: none; result: no provider; new MetaMask pages: none; other new targets: []; MetaMask visible on screen=False | 08-after.png |
