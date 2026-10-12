from __future__ import annotations

from conftest import make_apk, make_dex

from am import apkinfo


def test_dex_strings_roundtrip():
    names = ["Lcom/badlogic/gdx/Game;", "Lcom/android/billingclient/api/BillingClient;"]
    assert set(apkinfo.dex_strings(make_dex(names))) == set(names)


def test_unity_il2cpp(tmp_path):
    apk = make_apk(tmp_path / "g.apk", package="com.unity.game",
                   libs={"arm64-v8a": ["libunity.so", "libil2cpp.so"]},
                   extra_files={"assets/bin/Data/Managed/Metadata/global-metadata.dat": b"\x00" * 8})
    r = apkinfo.fingerprint(apk)
    assert r["engine"] == "unity-il2cpp"
    assert r["package"] == "com.unity.game"
    assert "arm64-v8a" in r["abis"]
    assert r["playbook"].endswith("unity-il2cpp.md")


def test_unity_mono(tmp_path):
    apk = make_apk(tmp_path / "g.apk", libs={"armeabi-v7a": ["libunity.so", "libmono.so"]},
                   extra_files={"assets/bin/Data/Managed/Assembly-CSharp.dll": b"MZ"})
    assert apkinfo.fingerprint(apk)["engine"] == "unity-mono"


def test_godot(tmp_path):
    apk = make_apk(tmp_path / "g.apk", libs={"arm64-v8a": ["libgodot_android.so"]},
                   extra_files={"assets/game.pck": b"GDPC"})
    assert apkinfo.fingerprint(apk)["engine"] == "godot"


def test_libgdx_via_dex(tmp_path):
    apk = make_apk(tmp_path / "g.apk", dex_classes=["Lcom/badlogic/gdx/ApplicationListener;"])
    assert apkinfo.fingerprint(apk)["engine"] == "libgdx"


def test_html5_webview(tmp_path):
    apk = make_apk(tmp_path / "g.apk", extra_files={"assets/www/index.html": b"<html></html>"},
                   dex_classes=["Lorg/apache/cordova/CordovaActivity;"])
    assert apkinfo.fingerprint(apk)["engine"] == "html5-webview"


def test_plain_java(tmp_path):
    apk = make_apk(tmp_path / "g.apk")
    assert apkinfo.fingerprint(apk)["engine"] == "java-kotlin"


def test_protections_reported_and_online(tmp_path):
    apk = make_apk(
        tmp_path / "g.apk",
        permissions=["android.permission.INTERNET"],
        dex_classes=[
            "Lcom/google/android/play/core/integrity/IntegrityManager;",
            "Lcom/android/billingclient/api/BillingClient;",
        ],
        libs={"arm64-v8a": ["libpairipcore.so"]},
    )
    r = apkinfo.fingerprint(apk)
    kinds = {p["kind"] for p in r["protections"]}
    assert "play-integrity" in kinds
    assert "billing" in kinds
    assert "pairip" in kinds
    assert r["online"] is True


def test_signing_scheme_v1(tmp_path):
    apk = make_apk(tmp_path / "g.apk")
    assert "v1" in apkinfo.fingerprint(apk)["signing_schemes"]


def test_debuggable_and_backup_flags(tmp_path):
    apk = make_apk(tmp_path / "g.apk", debuggable=True, allow_backup=False)
    r = apkinfo.fingerprint(apk)
    assert r["debuggable"] is True
    assert r["allowBackup"] is False
