# libGDX on Android

**Fingerprint:** `com.badlogic.gdx` classes in the dex (and often `libgdx.so`). `am scan` reports `libgdx`.

libGDX is a Java/Kotlin framework, so the game logic is ordinary JVM code and the assets are loose files. Many
libGDX games (Mindustry, several itch/F-Droid titles) are **open source** — check first.

## Routes, cheapest first
1. **Source build.** If the project is open, build from it. libGDX projects use Gradle; the Android module
   produces the APK. This is the best route for new items/mechanics.
2. **Assets.** Textures, atlases (`.atlas` + page PNGs), audio, fonts and often data files (JSON) live under
   `assets/`. Swap your own art at matching atlas coordinates/size — `am sprite atlas` builds a compatible sheet.
3. **Data files.** Many libGDX games read JSON/CSV content you can edit for new content without touching code.

## Verifying
- `am logcat -p <package>` shows `Gdx.app.log` output and stack traces.

## Gotchas
1. **TexturePacker atlas coords.** If you resize a sprite you must update the `.atlas` region; easier to keep the
   exact cell size. `am sprite fit` to the original size avoids re-packing.
2. **Obfuscated release builds.** R8/ProGuard renames classes; for source changes use the project, not the
   decompiled APK.
3. **Desktop vs Android asset paths.** libGDX uses `internal` (bundled) vs `local`/`external` (writable); saves
   go to app data, bundled assets are read-only in the APK.
