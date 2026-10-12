"""Helpers to build synthetic APKs and DEX files, so tests never need a device or the Android SDK."""
from __future__ import annotations

import io
import struct
import zipfile
from pathlib import Path

MANIFEST = """<?xml version="1.0"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{package}">
  <uses-sdk android:minSdkVersion="24" android:targetSdkVersion="34"/>
  {perms}
  <application android:label="Test" android:debuggable="{debuggable}" android:allowBackup="{backup}">
    <activity android:name=".MainActivity"/>
  </application>
</manifest>
"""


def make_dex(class_descriptors: list[str]) -> bytes:
    """A minimal DEX whose string table holds the given descriptors (enough for apkinfo.dex_strings)."""
    strings = list(class_descriptors)
    n = len(strings)
    header = bytearray(0x70)
    header[0:4] = b"dex\n"
    header[4:8] = b"035\x00"
    string_ids_off = 0x70
    # string data goes right after the id array
    data_off = string_ids_off + 4 * n
    id_array = bytearray()
    data = bytearray()
    for s in strings:
        raw = s.encode("utf-8")
        # uleb128 length (assume < 128 chars)
        entry_off = data_off + len(data)
        id_array += struct.pack("<I", entry_off)
        data += bytes([len(raw)]) + raw + b"\x00"
    struct.pack_into("<II", header, 0x38, n, string_ids_off)
    return bytes(header) + bytes(id_array) + bytes(data)


def make_apk(
    path: Path,
    package: str = "com.example.game",
    libs: dict[str, list[str]] | None = None,
    extra_files: dict[str, bytes] | None = None,
    dex_classes: list[str] | None = None,
    permissions: list[str] | None = None,
    debuggable: bool = False,
    allow_backup: bool = True,
) -> Path:
    """Write a small but structurally real APK zip to `path`."""
    perms = "\n  ".join(f'<uses-permission android:name="{p}"/>' for p in (permissions or []))
    manifest = MANIFEST.format(package=package, perms=perms,
                               debuggable="true" if debuggable else "false",
                               backup="true" if allow_backup else "false")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("AndroidManifest.xml", manifest)
        z.writestr("classes.dex", make_dex(dex_classes or ["Lcom/example/game/MainActivity;"]))
        z.writestr("resources.arsc", b"\x00" * 16)
        z.writestr("META-INF/CERT.RSA", b"\x00" * 8)  # v1 signature marker
        for abi, sos in (libs or {}).items():
            for so in sos:
                z.writestr(f"lib/{abi}/{so}", b"\x7fELF" + b"\x00" * 64)
        for name, content in (extra_files or {}).items():
            z.writestr(name, content)
    path.write_bytes(buf.getvalue())
    return path
