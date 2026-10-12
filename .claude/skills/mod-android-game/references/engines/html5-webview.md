# HTML5 / WebView games on Android (Cordova, Capacitor, Construct, Phaser, React Native)

**Fingerprint:** `assets/www/` or `assets/public/` with HTML/JS/CSS, Cordova/Capacitor classes, or a React
Native JS bundle (`assets/index.android.bundle`). `am scan` reports `html5-webview` or `react-native`.

These are the **friendliest games to mod**: the gameplay is JavaScript you can read and edit directly.

## Routes, cheapest first
1. **Web assets.** The whole game is under `assets/www` (or `public`): `index.html`, JS, CSS, images, audio,
   level JSON. Edit on your own copy — new levels, tweaked rules, reskins — then repackage. In scope for a game
   you own with no protection.
2. **Config / save edit.** WebView games store progress in `localStorage`/IndexedDB (under the app's WebView
   data) or in app files. Back up and edit.
3. **Source build.** Construct/Phaser/React Native projects rebuild cleanly if you have the source.

React Native: the logic is in `index.android.bundle` (minified JS, sometimes Hermes bytecode). Plain JS bundles
are editable; Hermes needs the source or a Hermes-aware tool — prefer the project source.

## Verifying
- `am logcat -p <package>` plus WebView console: enable `WebView.setWebContentsDebuggingEnabled` in a debug
  build, or read `console.log` through `chrome://inspect` against your own device.

## Gotchas
1. **Minified JS.** Shipped bundles are minified; editing is easiest against source. For small tweaks, search
   the minified file for string literals to find the spot.
2. **Hermes bytecode.** React Native release builds may ship `.hbc`; that's not plain JS — use the project.
3. **CSP / integrity.** Some wrappers check an asset hash on load; if editing `www` makes the game refuse to
   start, that's an integrity check — stop and use the source route.
