# Knowledge base

Field notes from agents who modded Android games, so the next agent starts from exact versions, the route that
worked, and the gotchas — instead of rediscovering them.

## Use it
- Search before you start: `am kb search "<game>"` and `am kb search "<engine>"`.
- Browse [INDEX.md](INDEX.md).

## Add to it
1. `am kb new --title "..." --game "..." --engine <key> --route <route>` creates a note from
   [TEMPLATE.md](TEMPLATE.md).
2. Fill it in as you work (your `MODLOG.md` is the raw material).
3. `am kb index` rebuilds `INDEX.md` + `index.json`; `am kb check --index` validates everything.
4. With your human's OK, open a PR. A documented dead end is worth as much as a success.

## What belongs here
- How a game stores saves/config, what engine and version, which route worked, numbered gotchas.
- Your own words and the symbol names — **not** the game's code, assets or data.

## What never belongs here
- Game files, extracted assets, decompiled source, or signing keys.
- Anything about defeating a protection (packer, anti-tamper, anti-cheat, integrity/licensing, DRM). Those are
  out of scope for this toolkit; see [../skills/mod-android-game/references/safety.md](../skills/mod-android-game/references/safety.md).
