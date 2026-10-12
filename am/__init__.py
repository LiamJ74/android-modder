"""android-modder: tools an AI agent uses to mod Android games the user owns, offline.

Commands (see `am --help`):
  scan      fingerprint an APK or an installed package: engine, ABI, protections, data paths, routes
  apk       pull, unpack, build, sign, install and diff APKs (apktool, apksigner, zipalign)
  shot      screenshot the device
  record    record the device screen
  drive     tap, swipe, type, press keys, dump the UI tree (uiautomator)
  logcat    read the log, filtered to one app or to crashes
  device    devices, emulators (AVD), launch/stop apps, clean up after crashes
  backup    snapshot and restore an app's data before you touch it
  fal       generate assets with fal (images, textures, sound effects, any model)
  sprite    cut out, fit, pack atlases, export screen densities, compress to ETC2/ASTC
  publish   pre-release lint of a mod folder
  kb        the knowledge base: search field notes, write your own, check and index them
"""

__version__ = "0.1.0"
