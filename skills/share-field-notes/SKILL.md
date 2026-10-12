---
name: share-field-notes
description: Turn a finished (or abandoned) Android modding session into a knowledge-base field note the next agent can repeat — exact versions, the route, what the engine really does, how you verified it, and numbered gotchas. Use at the end of any Android modding task, even a dead end. Covers `am kb new/index/check` and what belongs in a note (your own words and symbol names — never the game's code, assets or keys).
---

# Share field notes

Your `MODLOG.md` is the raw material; a field note is it, cleaned up for the next agent. A documented dead end
saves someone hours — write one even if the mod isn't finished.

## Write it
1. `am kb new --title "<what you built>" --game "<game>" --engine <key> --route <route>`
   — creates a note from the template under `knowledge/techniques/`.
2. Fill in every section (the template has them):
   - **Setup** — exact game build, store, device/emulator, Android version, tool versions. The versions that
     worked are the single most useful thing.
   - **Route and why** — which route, what else you considered. Call out if the game was open source or had an
     official modding surface.
   - **How the game works** — formats, key class/method names, save layout, limits. Your own words and the
     symbol names; never paste the game's code or data.
   - **Build steps** — the shortest path to reproduce.
   - **Verification** — the oracle (on-device test, logcat lines, screenshots you looked at), and what you did
     NOT verify.
   - **Gotchas** — numbered, each symptom → cause → fix. The most valuable section.
   - **Assets** — models, prompts, `am` commands, if any.
3. `am kb index` rebuilds `INDEX.md` + `index.json`; `am kb check --index` validates front matter and freshness.

## What belongs / never belongs
- **Belongs:** versions, routes, formats described in prose, symbol names, gotchas, verification method.
- **Never:** game files, extracted assets, decompiled source, signing keys, or anything about defeating a
  protection (those sessions shouldn't happen — see the safety reference).

## Then
With your human's OK, open a PR to the knowledge base. Keep the front matter intact; `am kb check` runs in CI.
