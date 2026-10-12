"""`am sprite`: turn generated art into engine-ready 2D assets for mobile.

Pure-Pillow operations (no device, no network):
  cutout     flood-fill the background to transparency from the corners
  fit        resize to WxH, nearest-neighbour for pixel art or Lanczos otherwise
  atlas      pack a folder of PNGs into a grid sheet + a JSON map
  densities  emit mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi copies for Android drawable-* folders

ETC2/ASTC compression is delegated to the SDK's etc2tool / astcenc if present; otherwise `am sprite compress`
explains how to get them. Nothing here needs an APK.
"""
from __future__ import annotations

import json
from pathlib import Path

import typer

from am import common

app = typer.Typer(help=__doc__, no_args_is_help=True)

DENSITIES = {"mdpi": 1.0, "hdpi": 1.5, "xhdpi": 2.0, "xxhdpi": 3.0, "xxxhdpi": 4.0}


def _pil():
    try:
        from PIL import Image
        return Image
    except ImportError:
        common.die("this needs Pillow: `pip install pillow` (or run through bin/am)")


def _parse_size(s: str) -> tuple[int, int]:
    if "x" in s.lower():
        w, h = s.lower().split("x", 1)
        return int(w), int(h)
    return int(s), int(s)


@app.command()
def cutout(
    src: Path,
    out: Path = typer.Option(None, "--out", "-o"),
    tolerance: int = typer.Option(24, "--tolerance", "-t", help="colour distance treated as background"),
):
    """Make the background transparent by flooding from the four corners."""
    Image = _pil()
    img = Image.open(src).convert("RGBA")
    px = img.load()
    w, h = img.size
    from collections import deque

    seen = set()
    dq = deque([(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)])
    bg = px[0, 0]

    def close(a, b):
        return sum(abs(a[i] - b[i]) for i in range(3)) <= tolerance

    while dq:
        x, y = dq.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        if close(px[x, y], bg):
            r, g, b, _ = px[x, y]
            px[x, y] = (r, g, b, 0)
            dq.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    out = out or src.with_name(src.stem + "_cut.png")
    img.save(out)
    typer.echo(f"am: wrote {out}")


@app.command()
def fit(
    src: Path,
    size: str = typer.Argument(..., help="WxH or N (square), e.g. 64x64"),
    out: Path = typer.Option(None, "--out", "-o"),
    pixel: bool = typer.Option(False, "--pixel", help="nearest-neighbour (pixel art)"),
):
    """Resize to an exact size."""
    Image = _pil()
    img = Image.open(src).convert("RGBA")
    w, h = _parse_size(size)
    resample = Image.NEAREST if pixel else Image.LANCZOS
    out = out or src.with_name(f"{src.stem}_{w}x{h}.png")
    img.resize((w, h), resample).save(out)
    typer.echo(f"am: wrote {out} ({w}x{h})")


@app.command()
def atlas(
    folder: Path,
    out: Path = typer.Option(Path("atlas.png"), "--out", "-o"),
    cols: int = typer.Option(0, "--cols", help="0 = square-ish"),
    cell: str = typer.Option(None, "--cell", help="force a cell size WxH; else the max frame size"),
):
    """Pack a folder of PNGs into one sheet, with a JSON frame map next to it."""
    Image = _pil()
    frames = sorted(p for p in folder.glob("*.png"))
    if not frames:
        common.die(f"no PNGs in {folder}")
    imgs = [Image.open(p).convert("RGBA") for p in frames]
    if cell:
        cw, ch = _parse_size(cell)
    else:
        cw = max(i.width for i in imgs)
        ch = max(i.height for i in imgs)
    import math

    n = len(imgs)
    cols = cols or math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    sheet = Image.new("RGBA", (cols * cw, rows * ch), (0, 0, 0, 0))
    frame_map = {}
    for i, (img, path) in enumerate(zip(imgs, frames, strict=True)):
        r, c = divmod(i, cols)
        x, y = c * cw, r * ch
        sheet.paste(img, (x + (cw - img.width) // 2, y + (ch - img.height) // 2))
        frame_map[path.stem] = {"x": x, "y": y, "w": cw, "h": ch}
    sheet.save(out)
    map_path = out.with_suffix(".json")
    map_path.write_text(json.dumps({"image": out.name, "cell": [cw, ch], "cols": cols, "frames": frame_map},
                                   indent=2), encoding="utf-8")
    typer.echo(f"am: wrote {out} ({cols}x{rows} grid) and {map_path}")


@app.command()
def densities(
    src: Path,
    base: str = typer.Option("mdpi", "--base", help="which density the source art already is"),
    out: Path = typer.Option(Path("drawable"), "--out", "-o", help="base dir; writes <out>-<density>/"),
):
    """Emit drawable-<density>/ copies for every Android screen density."""
    Image = _pil()
    img = Image.open(src).convert("RGBA")
    base_scale = DENSITIES[base]
    for name, scale in DENSITIES.items():
        f = scale / base_scale
        w, h = max(1, round(img.width * f)), max(1, round(img.height * f))
        d = out.with_name(f"{out.name}-{name}")
        d.mkdir(parents=True, exist_ok=True)
        img.resize((w, h), Image.LANCZOS).save(d / src.name)
    typer.echo(f"am: wrote {len(DENSITIES)} densities under {out.parent}/{out.name}-*")


@app.command()
def compress(
    src: Path,
    fmt: str = typer.Option("etc2", "--format", help="etc2 | astc"),
):
    """Compress a PNG to ETC2 (etc2tool) or ASTC (astcenc), if the tool is on PATH."""
    if fmt == "etc2":
        exe = common.find_tool("etc2tool", env="AM_ETC2TOOL", extra=common.sdk_dirs("tools/bin"))
        if not exe:
            common.die("etc2tool not found (ships with the Android SDK). Set AM_ETC2TOOL, or use ASTC.")
        out = src.with_suffix(".pkm")
        common.run([exe, str(src), "--encoding", "RGBA8", "-o", str(out)])
    else:
        exe = common.find_tool("astcenc", env="AM_ASTCENC")
        if not exe:
            common.die("astcenc not found. Get it from github.com/ARM-software/astc-encoder, or set AM_ASTCENC.")
        out = src.with_suffix(".astc")
        common.run([exe, "-cl", str(src), str(out), "6x6", "-medium"])
    typer.echo(f"am: wrote {out}")


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="sprite")
