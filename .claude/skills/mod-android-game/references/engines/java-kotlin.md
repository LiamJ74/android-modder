# Plain Java/Kotlin games on Android

**Fingerprint:** no engine library — Android `View`/`Canvas`/`SurfaceView` or a small custom GL renderer, logic
in the dex. `am scan` reports `java-kotlin`. Common for puzzle games, card games, idle games and classic 2D
titles.

Everything is standard Android: resources in `res/`, assets in `assets/`, data in app private storage. If the
game is open source (many simple ones are), build from the project.

## Routes, cheapest first
1. **Source build.** Open-source? Clone and build — new content, new rules, reskins, all clean.
2. **Resources / assets.** Drawables in `res/drawable-*`, strings in `res/values/strings.xml`, raw assets in
   `assets/`. Swap your own art (mind the screen densities — `am sprite densities`) and text.
3. **Config / save edit.** SharedPreferences XML and SQLite databases under `/data/data/<pkg>/`. Great for
   progress and settings; `am scan` lists the paths.

## Verifying
- `am logcat -p <package>` shows the app's `Log.d/i/e` output.

## Gotchas
1. **Resource IDs are compiled.** You can swap a drawable's bytes but renaming/adding resources means a rebuild;
   prefer same-name swaps or build from source.
2. **Obfuscation.** Release builds are R8-minified; for logic changes use the source, not the decompiled dex.
3. **SQLite locks.** Stop the app before editing its database, or the change won't stick / may corrupt. Back up
   first.
