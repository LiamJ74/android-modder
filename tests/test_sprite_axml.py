from __future__ import annotations

from typer.testing import CliRunner

from am import axml
from am.cli import app

runner = CliRunner()

pytest_plugins = []


def _png(path, size=(32, 16), color=(10, 20, 30, 255)):
    from PIL import Image

    Image.new("RGBA", size, color).save(path)


def test_fit(tmp_path):
    src = tmp_path / "a.png"
    _png(src)
    r = runner.invoke(app, ["sprite", "fit", str(src), "8x8", "--pixel", "-o", str(tmp_path / "o.png")])
    assert r.exit_code == 0, r.output
    from PIL import Image

    assert Image.open(tmp_path / "o.png").size == (8, 8)


def test_cutout_makes_transparent_corners(tmp_path):
    from PIL import Image

    img = Image.new("RGBA", (10, 10), (255, 255, 255, 255))
    for x in range(3, 7):
        for y in range(3, 7):
            img.putpixel((x, y), (200, 0, 0, 255))
    src = tmp_path / "c.png"
    img.save(src)
    out = tmp_path / "cut.png"
    r = runner.invoke(app, ["sprite", "cutout", str(src), "-o", str(out)])
    assert r.exit_code == 0, r.output
    res = Image.open(out)
    assert res.getpixel((0, 0))[3] == 0  # corner transparent
    assert res.getpixel((5, 5))[3] == 255  # centre kept


def test_atlas(tmp_path):
    folder = tmp_path / "frames"
    folder.mkdir()
    for i in range(3):
        _png(folder / f"f{i}.png", size=(16, 16))
    out = tmp_path / "atlas.png"
    r = runner.invoke(app, ["sprite", "atlas", str(folder), "-o", str(out)])
    assert r.exit_code == 0, r.output
    assert out.exists()
    assert (tmp_path / "atlas.json").exists()


def test_densities(tmp_path):
    src = tmp_path / "icon.png"
    _png(src, size=(48, 48))
    r = runner.invoke(app, ["sprite", "densities", str(src), "--base", "mdpi", "-o", str(tmp_path / "drawable")])
    assert r.exit_code == 0, r.output
    from PIL import Image

    assert Image.open(tmp_path / "drawable-xxxhdpi" / "icon.png").size == (192, 192)


def test_axml_parse_any_plaintext():
    xml = b'<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.x"/>'
    el = axml.parse_any(xml)
    assert el.get("package") == "com.x"


def test_axml_binary_magic_detection():
    # a buffer starting with the RES_XML magic but truncated should raise cleanly, not crash
    import pytest

    with pytest.raises(axml.AxmlError):
        axml.parse(b"\x03\x00\x08\x00\x04\x00\x00\x00")
