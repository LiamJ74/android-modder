from __future__ import annotations

import json

from conftest import make_apk
from typer.testing import CliRunner

from am import apk as apk_mod
from am import common
from am.cli import app

runner = CliRunner()


def test_version_and_rules():
    assert runner.invoke(app, ["--version"]).exit_code == 0
    r = runner.invoke(app, ["--rules"])
    assert r.exit_code == 0
    assert "own" in r.output.lower()


def test_help_lists_all_groups():
    out = runner.invoke(app, ["--help"]).output
    for group in ("scan", "apk", "device", "shot", "record", "drive", "logcat", "backup", "fal",
                  "sprite", "publish", "kb"):
        assert group in out


def test_scan_file_writes_plan(tmp_path):
    apk = make_apk(tmp_path / "g.apk", package="com.example.godotgame",
                   libs={"arm64-v8a": ["libgodot_android.so"]},
                   extra_files={"assets/game.pck": b"GDPC"})
    plan = tmp_path / "PLAN.md"
    r = runner.invoke(app, ["scan", "info", str(apk), "-o", str(plan)])
    assert r.exit_code == 0, r.output
    text = plan.read_text(encoding="utf-8")
    assert "com.example.godotgame" in text
    assert "godot" in text
    assert "Candidate routes" in text


def test_scan_json(tmp_path):
    apk = make_apk(tmp_path / "g.apk", libs={"arm64-v8a": ["libunity.so", "libil2cpp.so"]})
    r = runner.invoke(app, ["scan", "info", str(apk), "--json"])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert data["engine"] == "unity-il2cpp"


def test_apk_refuses_protected(tmp_path, monkeypatch):
    # an app flagged with a packer must not be repackaged
    apk = make_apk(tmp_path / "p.apk", libs={"arm64-v8a": ["libpairipcore.so"]})
    r = runner.invoke(app, ["apk", "unpack", str(apk)])
    assert r.exit_code == 1
    assert "won't repackage" in r.output or "protection" in r.output.lower()


def test_apk_diff(tmp_path):
    a = make_apk(tmp_path / "a.apk")
    b = make_apk(tmp_path / "b.apk", extra_files={"assets/new.txt": b"hello"})
    r = runner.invoke(app, ["apk", "diff", str(a), str(b), "--json"])
    assert r.exit_code == 0
    data = json.loads(r.output)
    assert "assets/new.txt" in data["added"]


def test_data_dir_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AM_HOME", str(tmp_path / "home"))
    d = common.data_dir()
    assert d.exists()
    assert str(tmp_path) in str(d)


def test_backup_list_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("AM_HOME", str(tmp_path / "home"))
    r = runner.invoke(app, ["backup", "list"])
    assert r.exit_code == 0
    assert "no snapshots" in r.output


def test_apk_has_backup_helper(tmp_path, monkeypatch):
    monkeypatch.setenv("AM_HOME", str(tmp_path / "home"))
    assert apk_mod._has_backup("com.nope") is False
    store = (tmp_path / "home" / ".android-modder" / "backups" / "lbl")
    # data_dir() is ~/.android-modder unless AM_HOME points elsewhere; here AM_HOME is the root
    store = common.data_dir() / "backups" / "lbl"
    store.mkdir(parents=True)
    (store / "manifest.json").write_text(json.dumps({"package": "com.yes"}), encoding="utf-8")
    assert apk_mod._has_backup("com.yes") is True
