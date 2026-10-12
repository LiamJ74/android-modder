from __future__ import annotations

import os

import pytest
from typer.testing import CliRunner

from am import kb
from am.cli import app

runner = CliRunner()


def test_slugify():
    assert kb.slugify("A Nuke in Mindustry!") == "a-nuke-in-mindustry"


def test_parse_front_matter_lists():
    text = '---\nkind: game\ntitle: "X: Y"\ntags: [a, b]\n---\n# body\n'
    meta, body = kb.parse_front_matter(text)
    assert meta["kind"] == "game"
    assert meta["title"] == "X: Y"
    assert meta["tags"] == ["a", "b"]
    assert body.strip() == "# body"


@pytest.fixture
def kb_env(tmp_path, monkeypatch):
    root = tmp_path / "knowledge"
    (root / "techniques").mkdir(parents=True)
    (root / "TEMPLATE.md").write_text(
        '---\nkind: game\ntitle: "t"\ngame: "g"\nengine: unknown\nroute: other\n'
        'status: idea\ndate: 2026-01-01\n---\n# t\n\n## Setup\n', encoding="utf-8")
    monkeypatch.setenv("AM_KB", str(root))
    return root


def test_new_then_index_then_check(kb_env):
    r = runner.invoke(app, ["kb", "new", "--title", "Nuke in Mindustry", "--game", "Mindustry",
                            "--engine", "libgdx", "--route", "source"])
    assert r.exit_code == 0, r.output
    assert (kb_env / "techniques" / "nuke-in-mindustry.md").exists()

    r = runner.invoke(app, ["kb", "index"])
    assert r.exit_code == 0
    assert (kb_env / "INDEX.md").exists()
    assert "Mindustry" in (kb_env / "INDEX.md").read_text(encoding="utf-8")

    r = runner.invoke(app, ["kb", "check", "--index"])
    assert r.exit_code == 0, r.output


def test_search_finds_note(kb_env):
    runner.invoke(app, ["kb", "new", "--title", "Godot save editor", "--game", "SomeGodotGame",
                        "--engine", "godot", "--route", "data"])
    r = runner.invoke(app, ["kb", "search", "godot", "--json"])
    assert r.exit_code == 0
    assert "SomeGodotGame" in r.output


def test_check_fails_on_stale_index(kb_env):
    runner.invoke(app, ["kb", "new", "--title", "Thing", "--game", "G"])
    # index.md not rebuilt -> stale
    r = runner.invoke(app, ["kb", "check", "--index"])
    assert r.exit_code == 1


def test_env_isolation(kb_env):
    assert os.environ["AM_KB"] == str(kb_env)
