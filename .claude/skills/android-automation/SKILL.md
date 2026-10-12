---
name: android-automation
description: Drive an Android device or emulator with adb to test and record a mod — install/launch/stop apps, screenshot, screen-record, tap/swipe/type, dump the UI tree (uiautomator), read logcat, start an AVD, and clean up after a crash. Use when verifying a mod on device, capturing a showcase, or scripting a repeatable test path. Input automation takes over the device, so it confirms before acting.
---

# Android automation

The layer that launches the game, drives the menus, watches the screen and reads the log. It never touches
another app's files — that's backup/apk. Prefer an emulator for iteration.

## Devices and emulators
- `am device list` — attached devices/emulators and their state.
- `am device info` — model, Android version, ABIs, screen size, root.
- `am device avd list` / `am device avd start <name>` — run an AVD (needs the SDK emulator). Headless with
  `--no-window`.
- `am device launch <package>` / `am device stop <package>` — start/force-stop by exact package (never a
  wildcard kill).
- `am device crash-clean` — dismiss a stuck crash/ANR dialog so the next launch isn't wedged.

## See it
- `am shot -o shot.png` — screenshot straight to PNG (no temp file left on the device).
- `am record -t 20 -o clip.mp4` — record up to 180 s via the device's screenrecord, then pull the mp4.
- Read screenshots to decide the next tap; if you downscale for tokens, multiply coordinates back when clicking.

## Drive it (asks before acting; pass --yes to skip in a scripted run)
- `am drive tap X Y`, `am drive swipe X1 Y1 X2 Y2 --ms 300`
- `am drive text "hello"`, `am drive key BACK` (or ENTER, HOME, a KEYCODE_* name/number)
- `am drive ui -o ui.xml` — dump the uiautomator tree to find tap targets by resource-id/text, so you tap by
  meaning, not guessed pixels.

## Read the log
- `am logcat -p <package>` — the game's own lines (filtered by its pid).
- `am logcat --crash` — the crash buffer after a hang.
- `am logcat --clear` first to get a clean run.

## A repeatable test (the oracle)
1. Restore a known save (`am backup restore`) so every run starts the same.
2. `am device launch`, then a fixed `am drive` path to the scene you're testing.
3. `am shot` / `am record` at the moment that proves the mod works, and check `am logcat`.
4. **Circuit breaker:** same failure 3 times → stop, write what you know, change approach.

## Etiquette
- Input automation takes over the device — confirm before long runs, and don't drive a phone the user is
  holding. Prefer an emulator.
- Leave nothing running: stop AVDs and any server you started, by pid/package.
