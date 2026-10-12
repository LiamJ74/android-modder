"""Static APK analysis in pure Python: manifest, ABIs, engine, protections, data paths, ranked routes.

Works on .apk and on bundles (.xapk / .apks / .apkm: zips of base + split APKs). Nothing is executed and
nothing is bypassed: protections are *reported* so the agent can stay clear of them.
"""
from __future__ import annotations

import io
import re
import struct
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from am import axml

# -- engine signatures --------------------------------------------------------------------------------------
# (engine key, playbook file, test) — first match wins, most specific first.
ENGINES: list[tuple[str, str, str]] = [
    ("unity-il2cpp", "unity-il2cpp.md", "Unity with IL2CPP: C# compiled to native libil2cpp.so + global-metadata.dat"),
    ("unity-mono", "unity-mono.md", "Unity with Mono: C# assemblies in assets/bin/Data/Managed"),
    ("unreal", "unreal.md", "Unreal Engine: libUE4.so / libUnreal.so and .pak archives"),
    ("godot", "godot.md", "Godot: libgodot_android.so and a .pck (or loose res://) pack"),
    ("libgdx", "libgdx.md", "libGDX: Java/Kotlin game code on com.badlogic.gdx"),
    ("cocos2d-x", "native-cpp.md", "Cocos2d-x: C++ (libcocos2dcpp.so) or Lua/JS scripts in assets"),
    ("gamemaker", "native-cpp.md", "GameMaker: libyoyo.so runner + game.droid data file"),
    ("defold", "native-cpp.md", "Defold: native engine, Lua game logic in archives"),
    ("flutter", "native-cpp.md", "Flutter: Dart AOT in libapp.so"),
    ("xamarin", "unity-mono.md", "Xamarin/.NET MAUI: .NET assemblies (libmonodroid.so)"),
    ("react-native", "html5-webview.md", "React Native: JS bundle in assets/index.android.bundle"),
    ("html5-webview", "html5-webview.md", "HTML5 in a WebView: Cordova/Capacitor/Construct/Phaser in assets/www"),
    ("native-cpp", "native-cpp.md", "Native C/C++ engine (NativeActivity or large custom .so)"),
    ("java-kotlin", "java-kotlin.md", "Plain Java/Kotlin app (Android views, Canvas, or a small GL renderer)"),
]
PLAYBOOK = {k: p for k, p, _ in ENGINES}
ENGINE_DESC = {k: d for k, _, d in ENGINES}

# Class-descriptor prefixes in dex string tables -> what they reveal. Reported, never patched out.
DEX_MARKERS: dict[str, tuple[str, str]] = {
    "Lcom/google/android/play/core/integrity/": ("play-integrity", "Play Integrity API"),
    "Lcom/google/android/play/integrity/": ("play-integrity", "Play Integrity API"),
    "Lcom/google/android/gms/safetynet/": ("safetynet", "SafetyNet attestation (legacy)"),
    "Lcom/android/billingclient/": ("billing", "Google Play Billing (in-app purchases)"),
    "Lcom/android/vending/billing/": ("billing", "Google Play Billing AIDL (in-app purchases)"),
    "Lcom/android/vending/licensing/": ("licensing", "Play Licensing (LVL)"),
    "Lcom/google/android/vending/licensing/": ("licensing", "Play Licensing (LVL)"),
    "Lcom/pairip/": ("pairip", "Google Play automatic integrity protection (pairip)"),
    "Lcom/unity3d/": ("unity-java", "Unity player Java layer"),
    "Lcom/badlogic/gdx/": ("libgdx", "libGDX"),
    "Lorg/godotengine/": ("godot-java", "Godot Java layer"),
    "Lcom/epicgames/": ("unreal-java", "Unreal Java layer"),
    "Lorg/apache/cordova/": ("cordova", "Cordova"),
    "Lcom/getcapacitor/": ("capacitor", "Capacitor"),
    "Lcom/facebook/react/": ("react-native", "React Native"),
    "Lorg/cocos2dx/": ("cocos2d-x", "Cocos2d-x Java layer"),
    "Lcom/yoyogames/": ("gamemaker", "GameMaker Java layer"),
    "Lcom/defold/": ("defold", "Defold Java layer"),
    "Lio/flutter/": ("flutter", "Flutter embedding"),
    "Lcom/google/firebase/": ("firebase", "Firebase (remote config, analytics, backend)"),
    "Lcom/google/android/gms/games/": ("play-games", "Play Games Services (cloud saves, leaderboards)"),
    "Lcom/google/android/gms/ads/": ("ads", "Google Mobile Ads"),
    "Lcom/playfab/": ("online-backend", "PlayFab backend"),
    "Lcom/gameanalytics/": ("analytics", "GameAnalytics"),
}

# Native libraries that reveal a packer, an anti-tamper SDK or an anti-cheat. Stop signs, not puzzles.
NATIVE_PROTECTIONS: dict[str, tuple[str, str]] = {
    "libpairipcore.so": ("pairip", "Google Play automatic integrity protection (pairip)"),
    "libjiagu": ("packer", "Qihoo 360 Jiagu packer"),
    "libsecexe": ("packer", "Bangcle packer"),
    "libDexHelper": ("packer", "SecNeo/DexHelper packer"),
    "libshella": ("packer", "Tencent Legu packer"),
    "libprotectClass": ("packer", "packer (protectClass)"),
    "libliapp": ("anti-tamper", "LIAPP anti-tamper"),
    "libcovault": ("anti-tamper", "AppSealing anti-tamper"),
    "libshield": ("anti-tamper", "Promon SHIELD"),
    "libtersafe": ("anti-cheat", "Tencent TP / ACE anti-cheat"),
    "libanogs": ("anti-cheat", "Tencent ACE anti-cheat"),
    "libtprt": ("anti-cheat", "Tencent anti-cheat runtime"),
    "libNetHTProtect": ("anti-cheat", "NetEase Yidun anti-cheat"),
    "libxigncode": ("anti-cheat", "XIGNCODE3 anti-cheat"),
    "libnprotect": ("anti-cheat", "nProtect GameGuard"),
    "libeasyanticheat": ("anti-cheat", "Easy Anti-Cheat"),
    "libBugly": ("crash-reporter", "Tencent Bugly crash reporter"),
}

SIG_BLOCK_IDS = {0x7109871A: "v2", 0xF05368C0: "v3", 0x1B93AD61: "v3.1", 0x6DFF800D: "source-stamp"}
ONLINE_PERMS = {"android.permission.INTERNET"}


@dataclass
class ApkData:
    """Everything we need from one or more APK zips (base + splits) to fingerprint the app."""
    names: list[str] = field(default_factory=list)
    sizes: dict[str, int] = field(default_factory=dict)
    manifest: axml.Element | None = None
    dex_markers: dict[str, str] = field(default_factory=dict)
    class_names: list[str] = field(default_factory=list)
    signature: list[str] = field(default_factory=list)
    splits: list[str] = field(default_factory=list)


# -- dex ----------------------------------------------------------------------------------------------------
def _uleb(buf: bytes, p: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        b = buf[p]
        p += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, p
        shift += 7


def dex_strings(buf: bytes, limit: int = 400_000) -> list[str]:
    """The string table of a classes.dex: class descriptors, method names, literals."""
    if buf[:4] != b"dex\n" or len(buf) < 0x70:
        return []
    count, off = struct.unpack_from("<II", buf, 0x38)
    out = []
    for i in range(min(count, limit)):
        (data_off,) = struct.unpack_from("<I", buf, off + 4 * i)
        _n, p = _uleb(buf, data_off)
        end = buf.index(b"\x00", p)
        out.append(buf[p:end].decode("utf-8", "replace"))
    return out


# -- APK signing block --------------------------------------------------------------------------------------
def signing_schemes(raw: bytes, names: list[str]) -> list[str]:
    schemes = []
    if any(re.fullmatch(r"META-INF/[^/]+\.(RSA|DSA|EC)", n) for n in names):
        schemes.append("v1")
    eocd = raw.rfind(b"PK\x05\x06")
    if eocd >= 0 and eocd + 20 <= len(raw):
        (cd_off,) = struct.unpack_from("<I", raw, eocd + 16)
        if cd_off >= 24 and raw[cd_off - 16:cd_off] == b"APK Sig Block 42":
            (size,) = struct.unpack_from("<Q", raw, cd_off - 24)
            start = cd_off - size - 8
            p = start + 8
            while 0 <= start and p < cd_off - 24:
                (plen,) = struct.unpack_from("<Q", raw, p)
                (pid,) = struct.unpack_from("<I", raw, p + 8)
                if pid in SIG_BLOCK_IDS:
                    schemes.append(SIG_BLOCK_IDS[pid])
                p += 8 + plen
    return schemes


# -- loading ------------------------------------------------------------------------------------------------
def _read_apk(raw: bytes, data: ApkData, label: str) -> None:
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        data.names += names
        for i in infos:
            data.sizes[i.filename] = max(data.sizes.get(i.filename, 0), i.file_size)
        if "AndroidManifest.xml" in names:
            m = axml.parse_any(z.read("AndroidManifest.xml"))
            if m.get("split") is None and data.manifest is None:
                data.manifest = m
                data.signature = signing_schemes(raw, names)
            elif m.get("split"):
                data.splits.append(m.get("split") or label)
        for n in names:
            if re.fullmatch(r"classes\d*\.dex", n):
                for s in dex_strings(z.read(n)):
                    if s.startswith("L") and s.endswith(";"):
                        data.class_names.append(s)
                        for prefix, (key, desc) in DEX_MARKERS.items():
                            if s.startswith(prefix):
                                data.dex_markers[key] = desc


def load(path: Path) -> ApkData:
    raw = Path(path).read_bytes()
    data = ApkData()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        inner = [n for n in names if n.lower().endswith(".apk")]
        if "AndroidManifest.xml" not in names and inner:
            # bundle: base first so its manifest wins
            inner.sort(key=lambda n: (0 if "base" in n.lower() or "/" not in n and n.count(".") == 1 else 1, n))
            for n in inner:
                _read_apk(z.read(n), data, n)
            data.names += [n for n in names if not n.lower().endswith(".apk")]  # xapk OBBs, manifest.json
            return data
    _read_apk(raw, data, Path(path).name)
    return data


# -- detection ----------------------------------------------------------------------------------------------
def _libs(names: list[str]) -> dict[str, list[str]]:
    """{abi: [lib names]} from lib/<abi>/*.so."""
    out: dict[str, list[str]] = {}
    for n in names:
        m = re.fullmatch(r"lib/([^/]+)/([^/]+\.so)", n)
        if m:
            out.setdefault(m.group(1), []).append(m.group(2))
    return {k: sorted(set(v)) for k, v in sorted(out.items())}


def detect_engine(data: ApkData) -> tuple[str, list[str]]:
    names = set(data.names)
    libs = {lib for v in _libs(data.names).values() for lib in v}
    ev: list[str] = []

    def has(prefix: str) -> bool:
        return any(n.startswith(prefix) for n in names)

    if "libil2cpp.so" in libs or has("assets/bin/Data/Managed/Metadata/global-metadata.dat"):
        ev += [e for e in ("libil2cpp.so", "global-metadata.dat") if e in libs or has(
            "assets/bin/Data/Managed/Metadata/" + e)]
        return "unity-il2cpp", ev or ["libil2cpp.so"]
    if "libunity.so" in libs or "libmono.so" in libs or "libmonobdwgc-2.0.so" in libs:
        if has("assets/bin/Data/Managed/") or "libmono.so" in libs or "libmonobdwgc-2.0.so" in libs:
            return "unity-mono", ["libunity.so", "assets/bin/Data/Managed/*.dll"]
        return "unity-il2cpp", ["libunity.so (no Managed/ dlls: IL2CPP likely, split APK may hold libil2cpp.so)"]
    if libs & {"libUE4.so", "libUnreal.so"} or any(n.endswith(".pak") for n in names):
        return "unreal", sorted(libs & {"libUE4.so", "libUnreal.so"}) or [".pak archives"]
    if "libgodot_android.so" in libs or any(n.endswith(".pck") for n in names) or "godot-java" in data.dex_markers:
        return "godot", ["libgodot_android.so" if "libgodot_android.so" in libs else "assets/*.pck"]
    if "libgdx.so" in libs or "libgdx" in data.dex_markers:
        return "libgdx", ["com.badlogic.gdx" if "libgdx" in data.dex_markers else "libgdx.so"]
    cocos = {"libcocos2dcpp.so", "libcocos2djs.so", "libcocos2dlua.so", "libcocos.so"}
    if libs & cocos or "cocos2d-x" in data.dex_markers:
        return "cocos2d-x", sorted(libs & cocos) or ["com.cocos / org.cocos2dx"]
    if "libyoyo.so" in libs or "assets/game.droid" in names:
        return "gamemaker", ["libyoyo.so", "assets/game.droid"]
    if "libdmengine.so" in libs or "defold" in data.dex_markers:
        return "defold", ["libdmengine.so"]
    if "libflutter.so" in libs:
        return "flutter", ["libflutter.so", "libapp.so"]
    if "libmonodroid.so" in libs or has("assemblies/"):
        return "xamarin", ["libmonodroid.so", "assemblies/"]
    if "assets/index.android.bundle" in names or "react-native" in data.dex_markers:
        return "react-native", ["assets/index.android.bundle"]
    if has("assets/www/") or has("assets/public/") or {"cordova", "capacitor"} & set(data.dex_markers):
        return "html5-webview", [p for p in ("assets/www/", "assets/public/") if has(p)] or ["Cordova/Capacitor"]
    m = data.manifest
    native_activity = bool(m and any(
        a.get("name") == "android.app.lib_name" for a in m.iter("meta-data")))
    big_so = [n for n, s in data.sizes.items() if n.endswith(".so") and s > 2_000_000]
    if native_activity or big_so:
        return "native-cpp", (["NativeActivity"] if native_activity else []) + [Path(n).name for n in big_so[:3]]
    return "java-kotlin", ["no engine library found"]


def obfuscation(class_names: list[str], package: str | None) -> dict:
    """Share of the app's own classes with 1-2 letter names (R8/ProGuard renaming)."""
    own = [c for c in class_names if not c.startswith(("Landroid", "Ljava", "Lkotlin", "Ldalvik"))]
    if not own:
        return {"classes": 0, "short_name_ratio": 0.0, "obfuscated": False}
    short = [c for c in own if len(c[1:-1].rsplit("/", 1)[-1].split("$")[0]) <= 2]
    ratio = round(len(short) / len(own), 3)
    return {"classes": len(own), "short_name_ratio": ratio, "obfuscated": ratio > 0.3}


def data_locations(package: str, engine: str, has_obb: bool) -> list[dict]:
    locs = [
        {"path": f"/data/data/{package}/", "access": "run-as (debuggable builds) or root",
         "what": "shared_prefs/ (settings, often saves), files/, databases/, no_backup/"},
        {"path": f"/sdcard/Android/data/{package}/files/", "access": "adb pull (pre-Android 11 freely; later "
         "versions may need the device's file manager or root)", "what": "external files, downloaded content"},
    ]
    if has_obb:
        locs.append({"path": f"/sdcard/Android/obb/{package}/", "access": "adb pull",
                     "what": "OBB expansion files (main.<code>.<pkg>.obb)"})
    if engine.startswith("unity"):
        locs.append({"path": f"/data/data/{package}/shared_prefs/{package}.v2.playerprefs.xml",
                     "access": "run-as or root", "what": "Unity PlayerPrefs (keys URL-encoded, values often base64)"})
    if engine == "godot":
        locs.append({"path": f"/data/data/{package}/files/", "access": "run-as or root",
                     "what": "Godot user:// (saves, settings)"})
    return locs


ROUTES: dict[str, list[str]] = {
    "unity-mono": ["assets: swap AssetBundles / serialized assets (UABEA, AssetRipper) on your own install",
                   "runtime: a BepInEx-for-Android style loader, or an official modding API if the game ships one"],
    "unity-il2cpp": ["assets: same asset route as Mono (the C# is compiled to native, so no managed DLLs to edit)",
                     "config/data: edit the app's own save and config files after a backup"],
    "godot": ["source: Godot games are often open; build your changes from the project and export your own build",
              "pack: for your own install, repack resources with the Godot tools"],
    "libgdx": ["source: libGDX games are frequently open source — fork and build",
               "assets: replace textures/atlases/audio the game loads"],
    "unreal": ["assets: .pak overrides (UnrealPak) on your own install", "config: edit the app's .ini/save files"],
    "cocos2d-x": ["scripts: Lua/JS games keep logic in assets; edit on your own copy",
                  "assets: replace sprites, atlases, audio"],
    "gamemaker": ["assets/data: edit the game.droid data file with community tools on your own copy"],
    "html5-webview": ["web: edit the HTML/JS/CSS in assets/www on your own install — the friendliest route"],
    "react-native": ["bundle: the JS lives in assets/index.android.bundle; patch on your own copy"],
    "java-kotlin": ["assets/resources: swap drawables, strings, raw assets",
                    "source: if the game is open source, build from it"],
    "native-cpp": ["assets: replace data files the engine loads",
                   "source: build from the project if it is open source"],
    "flutter": ["assets: replace bundled assets; the Dart logic is AOT-compiled in libapp.so"],
    "defold": ["assets: edit the Defold archive on your own copy; build from the project if open"],
    "xamarin": ["assets/data: edit the app's own data files after a backup"],
}


def protections(data: ApkData) -> list[dict]:
    """Everything that protects the app — integrity, billing, licensing, packers, anti-cheat.

    Reported so the agent can respect it and stay clear, never to defeat it. An app carrying any of these
    (especially a packer, anti-cheat or integrity check) is a stop sign for repackaging.
    """
    out: list[dict] = []
    libs = {lib for v in _libs(data.names).values() for lib in v}
    for key, desc in sorted(data.dex_markers.items()):
        if key in {"play-integrity", "safetynet", "billing", "licensing", "pairip"}:
            out.append({"kind": key, "detail": desc, "source": "dex"})
    for lib in sorted(libs):
        for needle, (kind, desc) in NATIVE_PROTECTIONS.items():
            if lib.startswith(needle):
                out.append({"kind": kind, "detail": f"{desc} ({lib})", "source": "native-lib"})
    return out


def fingerprint(path: Path) -> dict:
    """Full static report for one APK / bundle, the payload behind `am scan <file>`."""
    data = load(path)
    m = data.manifest
    if m is None:
        raise ValueError(f"no AndroidManifest.xml found in {path}")
    app = next(iter(m.iter("application")), None)
    package = m.get("package") or "?"
    engine, evidence = detect_engine(data)
    perms = sorted({p.get("name") for p in m.iter("uses-permission") if p.get("name")})
    has_obb = any(n.startswith("assets/") and n.endswith(".obb") for n in data.names)
    report = {
        "package": package,
        "versionName": m.get("versionName"),
        "versionCode": m.get("versionCode"),
        "minSdk": (next(iter(m.iter("uses-sdk")), axml.Element("x")).get("minSdkVersion")),
        "targetSdk": (next(iter(m.iter("uses-sdk")), axml.Element("x")).get("targetSdkVersion")),
        "debuggable": (app.get("debuggable") if app else None) == "true",
        "allowBackup": (app.get("allowBackup") if app else None) != "false",
        "extractNativeLibs": (app.get("extractNativeLibs") if app else None),
        "engine": engine,
        "engine_description": ENGINE_DESC.get(engine, ""),
        "engine_evidence": evidence,
        "playbook": f"skills/mod-android-game/references/engines/{PLAYBOOK.get(engine, 'native-cpp.md')}",
        "abis": sorted(_libs(data.names).keys()),
        "native_libs": _libs(data.names),
        "splits": sorted(set(data.splits)),
        "is_bundle": bool(data.splits),
        "signing_schemes": sorted(set(data.signature)),
        "permissions": perms,
        "online": bool(set(perms) & ONLINE_PERMS),
        "obfuscation": obfuscation(data.class_names, package),
        "protections": protections(data),
        "sdks": sorted({d for k, d in data.dex_markers.items()
                        if k in {"firebase", "play-games", "ads", "online-backend", "analytics", "crash-reporter"}}),
        "data_locations": data_locations(package, engine, has_obb),
        "routes": ROUTES.get(engine, []),
    }
    return report
