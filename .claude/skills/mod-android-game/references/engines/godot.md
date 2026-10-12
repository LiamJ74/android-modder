# Godot on Android

**Fingerprint:** `libgodot_android.so` and a `.pck` (or `.zip`) resource pack, or `godot-java` classes.
`am scan` reports `godot`. Godot 3 uses GDScript bytecode; Godot 4 ships `.pck` with resources and (often)
compiled GDScript.

Godot games are frequently **open source or source-available** — always check first, because building from the
project is the cleanest route and keeps the mod shareable.

## Routes, cheapest first
1. **Source build.** If the project is available, clone it, make your change in the Godot editor, and export
   your own Android build. This is the intended way and needs no repackaging.
2. **User data edit.** Godot's `user://` maps to `/data/data/<pkg>/files/` (saves, settings). Back up and edit.
3. **Resource pack (.pck).** For a game you own, the `.pck` holds scenes, scripts and assets. Community tools
   (godotpcktool, the editor's import/export) can read and rebuild a pack so you can swap your own assets in.
   Repackaging the APK afterwards is in scope only when there's no protection and the user owns the game.

## Verifying
- `am logcat -p <package>` shows Godot's `print()` output and script errors.

## Gotchas
1. **Encrypted .pck.** Some exports encrypt the pack with a key baked into the binary. Treat an encrypted pack
   as a protection — don't extract the key. Use the source route instead.
2. **GDScript bytecode version.** Decompilers are version-specific (3.x vs 4.x); match the Godot version from the
   binary.
3. **`.pck` embedded in the .so/apk.** Some exports append the pack to the executable rather than shipping a
   loose `.pck`; look for it inside the APK or alongside `libgodot_android.so`.
