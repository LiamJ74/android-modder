# Native C/C++ engines on Android (incl. Cocos2d-x, GameMaker, Defold, Flutter)

**Fingerprint:** a large game `.so` with `NativeActivity`, or a known native runtime — `libcocos2d*.so`,
`libyoyo.so` (GameMaker) + `assets/game.droid`, `libdmengine.so` (Defold), `libflutter.so` + `libapp.so`.
`am scan` reports `native-cpp`, `cocos2d-x`, `gamemaker`, `defold` or `flutter`.

Native logic is compiled, so code changes are hard and usually out of scope for store builds. The leverage is in
**data and scripts**, which these engines often keep editable.

## Routes, cheapest first
1. **Scripts.** Cocos2d-x games frequently ship Lua or JS in `assets/` (sometimes in a `jsb`/`luac` form, often
   plain). Defold keeps logic in a Lua-based archive. Editing these on your own copy is the main route.
2. **Data files.** GameMaker's `assets/game.droid` holds rooms, objects and sprites; community tools
   (UndertaleModTool for the YYC/VM data format) read and rebuild it for a game you own.
3. **Assets.** Textures/atlases/audio under `assets/` — swap your own at matching size/format.
4. **Config / save edit.** App private data under `/data/data/<pkg>/`.

Flutter's Dart is AOT-compiled into `libapp.so`; there's no script route, so stick to assets and config, or
build from source if the project is open.

## Verifying
- `am logcat -p <package>` — native engines log through Android's log; Cocos/GameMaker tag their output.

## Gotchas
1. **Compiled scripts.** `.luac`/`jsb` bytecode is version-specific; match the engine version or keep to assets.
2. **GameMaker data version.** `game.droid` format tracks the IDE version; the tool must match.
3. **Big `.so` = compiled logic.** If the idea truly needs engine-code changes and the game isn't open, say so
   and propose assets/data instead.
