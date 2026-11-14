# Resolute Browser: brief for AI assistants

Read `docs/MAINTAINING.md` before doing anything. It has the architecture, build
pipeline, update procedure, patch workflow, secrets list and roadmap.

Essentials:

- The product is the **Chromium-based browser in `chromium/`** (Chromium version
  in `chromium/VERSION`, GN args in `chromium/args.gn`, Resolute changes as
  patches in `chromium/patches/`). `app/` is an old GeckoView prototype.
- Builds run on free GitHub Actions as chained stages (`.github/workflows/chromium.yml`).
  A full build takes about a day. **Pushing to `chromium/**` cancels a running
  build**: check `gh run list --workflow chromium.yml` first and warn the owner.
- Extensions come from upstream `is_desktop_android = true`. Never re-introduce a
  Kiwi-style mega patch.
- Code reuse (owner delegated the decision, 2026-11-13): write Resolute code
  ourselves by default. Small, targeted reuse of phone-specific pieces from
  Kiwi (BSD-3) or Mises (MPL-2.0) is allowed when it saves real time: adapt it
  to the current Chromium, keep their licence and copyright notices, credit
  them in NOTICE, and MPL files stay MPL. Never port Kiwi's whole extensions
  patch. No GPL code, no Edge code.
- Keep Chromium updated at least monthly; security updates come before features.
- Licence: **proprietary, all rights reserved** since 2026-11-14 (LICENSE; third-party
  notices in NOTICE). The repo is public only so builds run free. Never add an
  open-source licence or licence headers that grant rights; keep Chromium's BSD
  notices.
- Never commit secrets (RPC keys, API keys, keystores, seed phrases). Keys are
  GitHub Actions secrets; names are listed in `docs/MAINTAINING.md` section 8.
- No Resolute server: config lives in `config/*.json` on GitHub.
- **Keep `docs/MAINTAINING.md` current in the same commit as every change**:
  new patches, args, workflow or script changes, new secrets or accounts,
  decisions, roadmap progress. After each build or release, add a line to the
  status log (section 11). The owner relies on this file to continue from any
  account.
- The owner is not a Chromium expert: explain changes in plain language.
