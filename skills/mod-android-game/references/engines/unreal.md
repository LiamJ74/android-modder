# Unreal Engine on Android

**Fingerprint:** `libUE4.so` / `libUnreal.so`, and `.pak` archives (often in an OBB:
`/sdcard/Android/obb/<pkg>/`). `am scan` reports `unreal`.

Unreal ships cooked content in `.pak` files and native C++ logic in the `.so`. The practical route on mobile is
assets and config, not C++.

## Routes, cheapest first
1. **Config / save edit.** Unreal keeps `.ini` config and `.sav` saves under the app's private data /
   `files/`. Back up and edit for settings and simple progress.
2. **Pak asset overrides.** Unreal can load additional `.pak` files that override cooked assets. Build a small
   override pak with your own assets (UnrealPak, or community repak tools) and place it where the game scans for
   paks. This swaps textures/meshes/sounds without touching the executable. In scope for a game you own with no
   protection.
3. **Mod support.** Some Unreal games ship official mod/pak support or a Dev kit — use it if present.

## Verifying
- `am logcat -p <package>` shows Unreal's log category output; also check `UE4.log`/`Unreal.log` in app files.

## Gotchas
1. **Signed/encrypted paks.** If the game encrypts paks (AES key in the binary), treat it as a protection and
   stop; use official mod support instead.
2. **OBB expansion files.** Large games keep paks in the OBB on the SD card, not in the APK — `am scan` notes the
   OBB path; back up the OBB before changing anything there.
3. **Pak mount order.** Your override only wins if it mounts after the base pak; name/placement matters per game.
