# Safety, legality, etiquette

These rules keep the user's accounts, device and data safe, and keep their mod shareable. None of this is legal
advice. When a game's EULA or mod policy matters, read it (search "<publisher> mod policy").

## The bright line: protections and online play
- **Only single-player/offline games, or servers the user runs.** Modding an online client, or building any
  advantage against other players (aimbots, ESP, speed/teleport, auto-clickers for competitive play), is out of
  scope — refuse it whatever the framing.
- **Protections are a stop sign, not a puzzle.** If `am scan` reports any of these, do not try to repackage,
  patch past, or otherwise defeat them:
  - **Anti-cheat** (e.g. Tencent ACE/TP, NetEase, XIGNCODE, nProtect, EAC).
  - **Packers / app protectors** (e.g. Jiagu, Bangcle, SecNeo/DexHelper, Legu, AppSealing, Promon).
  - **Integrity / attestation**: Play Integrity API, SafetyNet, pairip (Play automatic integrity).
  - **Licensing**: Play Licensing (LVL).
  - **In-app billing**: Google Play Billing.
  - **DRM / ownership checks.**
  `am apk` refuses to repackage an app that `am scan` flags with a packer, anti-tamper, anti-cheat or integrity
  check. That refusal is the intended behaviour; don't work around it.
- **If the only route runs through a protection, stop and tell the user.** Offer legitimate alternatives:
  - the game's own modding surface (map/level editor, content packs, an official API or SDK);
  - an open-source build you compile from source;
  - the user's own debug build;
  - editing the user's own save/config data.

## Ownership and redistribution
- Mod only games the user owns, from their own device or their own build. Don't download APKs, OBBs or game
  files for them.
- **Never publish:** game files or byte-identical copies, extracted assets, decompiled source, or signing keys.
- **Do publish:** your own code and assets (fal output is yours under fal's terms — check each model's license
  for commercial use), and patches / converters / installers that transform the user's own files at install
  time ("bring your own game files").
- Credit loaders, libraries and references, and disclose AI use honestly.
- Takedowns happen even without shipping assets. Commercial use, monetization and leaked material raise the risk
  sharply. When in doubt, ship less.

## The user's device and data
- **Back up first:** `am backup create <package>` before any change to saves, data or an install. On a
  debuggable build this is `run-as` (no root). Restoring is one command (`am backup restore <label>`) — write
  the label in MODLOG.md.
- **Prefer an emulator (AVD)** or a spare device for iteration, so a bad build never risks the user's main
  phone or their saves.
- **Installing** a modified build replaces the installed app for that package. `am apk install` refuses unless a
  recent backup exists and always confirms. Tell the user what changed and how to go back
  (`adb uninstall` + reinstall the original, or `am backup restore`).
- **Input automation** (`am drive`) takes over the device. Confirm before long automated runs; don't drive a
  device the user is actively holding.
- **Processes:** stop apps by exact package (`am device stop <package>`), never a wildcard kill.
- **Bridges / servers:** bind anything you add to `127.0.0.1` with a token.
- **Tools from strangers:** a viral "modded APK" is often malware, and installing one is also outside this
  toolkit's scope (it's someone else's redistributed game). Only build from sources you trust.

## When to stop and ask
- The game is online with an anti-cheat and the idea touches it.
- `am scan` reports a packer, anti-tamper, anti-cheat, integrity, licensing or billing protection on the path
  you'd need.
- The only route is defeating a protection.
- A step would overwrite saves or an install without a backup.
- Publishing: always the user's call. Draft it, show them, let them press the button.
