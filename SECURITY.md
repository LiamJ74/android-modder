# Security & scope

android-modder is for modding Android games **the user owns**, offline, or on servers the user runs.

## In scope
- Static recon of an owned APK (engine, protections, data paths).
- The standard APK toolchain (apktool / apksigner / zipalign) for your **own builds** and games you own that
  carry no protection.
- adb-driven capture, input and logging on your device or an emulator.
- Backing up and editing an app's **own** data.
- Generating **original** assets and packaging a mod made of your own code/assets or patches.

## Out of scope (the toolkit refuses or stops)
- Defeating or working around an anti-cheat, packer, anti-tamper, DRM, Play Integrity / SafetyNet, licensing
  (LVL) or in-app billing. `am scan` reports these; `am apk` refuses to repackage an app flagged with a packer,
  anti-tamper, anti-cheat or integrity check.
- Modding online/competitive clients, or building any advantage against other players.
- Downloading, redistributing or shipping game files, extracted assets, decompiled source, or signing keys.

## Reporting
Found a way the tool helps with something out of scope above, or a vulnerability in the tool itself? Open a
private security advisory on the GitHub repository (Security → Report a vulnerability) rather than a public
issue.

## Handling secrets
Never commit `FAL_KEY` or any API key. `am publish check` surfaces common key shapes and keystores in a mod
folder before you share it, but it is advisory — review before publishing.
