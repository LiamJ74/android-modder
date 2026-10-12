from __future__ import annotations

from typer.testing import CliRunner

from am import safety
from am.cli import app

runner = CliRunner()


def test_secret_patterns():
    assert "fal key" in safety.scan_text_for_secrets("FAL_KEY=fal-ABCDEFGH12345")
    assert "GitHub token" in safety.scan_text_for_secrets("ghp_" + "a" * 36)
    assert safety.scan_text_for_secrets("nothing to see") == []


def test_check_clean_folder_exit_zero(tmp_path):
    (tmp_path / "README.md").write_text("# My mod\nBuilt with fal.\n", encoding="utf-8")
    (tmp_path / "src.py").write_text("print('hello')\n", encoding="utf-8")
    r = runner.invoke(app, ["publish", "check", str(tmp_path), "--json"])
    assert r.exit_code == 0
    assert '"look": 0' in r.output


def test_check_flags_secret_but_does_not_fail(tmp_path):
    (tmp_path / "config.txt").write_text("token = ghp_" + "b" * 36 + "\n", encoding="utf-8")
    r = runner.invoke(app, ["publish", "check", str(tmp_path)])
    # advisory only: surfaces the issue, still exits 0
    assert r.exit_code == 0
    assert "GitHub token" in r.output


def test_check_flags_game_binary(tmp_path):
    (tmp_path / "game.apk").write_bytes(b"PK\x03\x04rest")
    (tmp_path / "README.md").write_text("# m", encoding="utf-8")
    r = runner.invoke(app, ["publish", "check", str(tmp_path), "--json"])
    assert r.exit_code == 0
    assert "game/app binary" in r.output


def test_check_missing_readme_is_tidy(tmp_path):
    (tmp_path / "mod.py").write_text("x = 1\n", encoding="utf-8")
    r = runner.invoke(app, ["publish", "check", str(tmp_path), "--json"])
    assert r.exit_code == 0
    assert "no README" in r.output
