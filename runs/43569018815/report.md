# Resolute E2E: 4/8 passed

| Test | Result | Detail | Screenshot |
|---|---|---|---|
| 01-install | ✅ | Success |  |
| 02-launch | ✅ | process id 4272 | 02-launch.png |
| 03-load-example | ✅ | page title: Example Domain | 03-example.png |
| 04-load-wikipedia | ✅ | page text found | 04-wikipedia.png |
| 05-store-install-ublock-lite | ❌ | error: Handshake status 500 Internal Server Error -+-+- {'content-length': '20', 'content-type': 'text/html'} -+-+- No such target id: 3 | 05-store-install-ublock-lite-error.png |
| 06-store-install-metamask | ❌ | error: Handshake status 500 Internal Server Error -+-+- {'content-length': '20', 'content-type': 'text/html'} -+-+- No such target id: 4 | 06-store-install-metamask-error.png |
| 07-extensions-listed | ❌ | running/listed: none | 07-extensions.png |
| 08-wallet-connect | ❌ | error: Handshake status 500 Internal Server Error -+-+- {'content-length': '20', 'content-type': 'text/html'} -+-+- No such target id: 5 | 08-wallet-connect-error.png |
