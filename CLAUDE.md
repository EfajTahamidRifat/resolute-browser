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
- Write all Resolute code ourselves. Do not copy code from Kiwi, Mises, Edge or
  any GPL project; studying how they work is fine.
- Keep Chromium updated at least monthly; security updates come before features.
- Never commit secrets (RPC keys, API keys, keystores, seed phrases). Keys are
  GitHub Actions secrets; names are listed in `docs/MAINTAINING.md` section 8.
- No Resolute server: config lives in `config/*.json` on GitHub.
- After each build or release, add a line to the status log in
  `docs/MAINTAINING.md` section 11.
- The owner is not a Chromium expert: explain changes in plain language.
