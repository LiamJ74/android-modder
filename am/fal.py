"""`am fal`: generate assets with fal's REST API (images, textures, sound effects, or any model).

Needs FAL_KEY in the environment. Every call is appended to fal_manifest.jsonl in the output folder, so a mod
can credit exactly which models made which assets. Uses only the standard library for HTTP, so there's no
extra dependency; if the fal MCP server is configured for the agent, that's an alternative to this.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import typer

from am import common

app = typer.Typer(help=__doc__, no_args_is_help=True)

FAL_QUEUE = "https://queue.fal.run"
RECIPES = {
    "image": "fal-ai/flux/dev",
    "texture": "fal-ai/flux/dev",
    "sfx": "fal-ai/stable-audio",
    "music": "fal-ai/stable-audio",
}


def _key() -> str:
    key = os.environ.get("FAL_KEY")
    if not key:
        common.die("set FAL_KEY in the environment (get one at fal.ai). The fal MCP server is another option.")
    return key


def _post(url: str, payload: dict, key: str) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST", headers={
        "Authorization": f"Key {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        common.die(f"fal HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}")
    except urllib.error.URLError as e:
        common.die(f"fal request failed: {e}")


def _get(url: str, key: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Key {key}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def _run_model(model: str, payload: dict, key: str, poll: float = 2.0, timeout: float = 600) -> dict:
    """Submit to the queue, poll until done, return the result JSON."""
    submit = _post(f"{FAL_QUEUE}/{model}", payload, key)
    status_url = submit.get("status_url")
    response_url = submit.get("response_url")
    if not status_url:
        return submit  # some models answer synchronously
    deadline = time.time() + timeout
    while time.time() < deadline:
        st = _get(status_url, key)
        if st.get("status") == "COMPLETED":
            return _get(response_url, key)
        if st.get("status") in ("FAILED", "ERROR"):
            common.die(f"fal job failed: {json.dumps(st)[:500]}")
        time.sleep(poll)
    common.die("fal job timed out")


def _download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as r:
        dest.write_bytes(r.read())


def _record(outdir: Path, entry: dict) -> None:
    with open(outdir / "fal_manifest.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _generate(recipe: str, prompt: str, outdir: Path, model: str | None, extra: dict) -> None:
    key = _key()
    model = model or RECIPES[recipe]
    outdir.mkdir(parents=True, exist_ok=True)
    payload = {"prompt": prompt, **extra}
    typer.echo(f"am: fal {model} …")
    result = _run_model(model, payload, key)
    saved = []
    for coll in ("images", "audio_file", "audio", "video", "files"):
        items = result.get(coll)
        if not items:
            continue
        for i, item in enumerate(items if isinstance(items, list) else [items]):
            url = item.get("url") if isinstance(item, dict) else item
            if not url:
                continue
            ext = Path(url.split("?")[0]).suffix or (".png" if recipe in ("image", "texture") else ".bin")
            dest = outdir / f"{recipe}_{int(time.time())}_{i}{ext}"
            _download(url, dest)
            saved.append(dest.name)
    _record(outdir, {"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "recipe": recipe, "model": model,
                     "prompt": prompt, "extra": extra, "files": saved})
    typer.echo(f"am: wrote {', '.join(saved) or '(no files in response)'} + fal_manifest.jsonl")


@app.command()
def image(prompt: str, out: Path = typer.Option(Path("assets"), "--out", "-o"),
          model: str = typer.Option(None, "--model"),
          size: str = typer.Option("square_hd", "--size", help="fal image_size enum or WxH")):
    """Generate an image."""
    extra = {"image_size": size} if "x" not in size else {
        "image_size": {"width": int(size.split("x")[0]), "height": int(size.split("x")[1])}}
    _generate("image", prompt, out, model, extra)


@app.command()
def texture(prompt: str, out: Path = typer.Option(Path("assets"), "--out", "-o"),
            model: str = typer.Option(None, "--model")):
    """Generate a tiling-ish texture (same models as image; prompt for 'seamless texture')."""
    _generate("texture", prompt + ", seamless tileable texture, flat lighting", out, model, {"image_size": "square_hd"})


@app.command()
def sfx(prompt: str, out: Path = typer.Option(Path("assets"), "--out", "-o"),
        seconds: int = typer.Option(5, "--seconds"), model: str = typer.Option(None, "--model")):
    """Generate a sound effect."""
    _generate("sfx", prompt, out, model, {"seconds_total": seconds})


@app.command()
def run(model: str, out: Path = typer.Option(Path("assets"), "--out", "-o"),
        param: list[str] = typer.Option([], "--param", "-p", help="key=value, repeatable")):
    """Run any fal model by id with raw key=value params (escape hatch)."""
    extra = {}
    prompt = ""
    for kv in param:
        k, _, v = kv.partition("=")
        if k == "prompt":
            prompt = v
        else:
            extra[k] = v
    _generate("run", prompt, out, model, extra)


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="fal")
