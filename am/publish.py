"""`am publish check`: a pre-release lint for a mod folder, run before you share anything.

Per the project's scope this lint is advisory: it SURFACES things to look at (secrets, keystores, decompiler
fingerprints, game-file-shaped blobs, a missing README, uncredited fal assets) and prints guidance, but it
does not hard-fail on content. It exits non-zero only when it literally can't read the folder, so it stays
usable in CI without gatekeeping what people ship. The real rules live in the skills and safety.md.
"""
from __future__ import annotations

from pathlib import Path

import typer

from am import common, safety

app = typer.Typer(help=__doc__, no_args_is_help=True)

# File shapes worth a second look in a *shared* mod folder.
GAME_FILE_SUFFIXES = {".apk", ".apks", ".xapk", ".apkm", ".obb", ".dex"}
KEYSTORE_SUFFIXES = {".jks", ".keystore", ".pem", ".pk8", ".p12"}
BIG_ARCHIVE_SUFFIXES = {".pak", ".pck", ".assets", ".bundle", ".resource", ".obb"}


@app.command()
def check(
    folder: Path = typer.Argument(Path("."), help="the mod folder to lint"),
    json_out: bool = typer.Option(False, "--json"),
):
    """Lint FOLDER and print notes. Advisory only — review each note before you share."""
    folder = folder.resolve()
    if not folder.is_dir():
        common.die(f"not a folder: {folder}")

    notes: list[dict] = []

    def note(level: str, msg: str, path: Path | None = None):
        notes.append({"level": level, "note": msg, "path": str(path.relative_to(folder)) if path else None})

    files = [p for p in folder.rglob("*") if p.is_file() and ".git" not in p.parts]

    for p in files:
        suf = p.suffix.lower()
        if suf in KEYSTORE_SUFFIXES:
            note("look", f"signing key / keystore — don't share this ({p.name})", p)
        if suf in GAME_FILE_SUFFIXES:
            note("look", f"looks like a game/app binary — ship patches or your own assets, not this ({p.name})", p)
        if suf in BIG_ARCHIVE_SUFFIXES and p.stat().st_size > 2_000_000:
            note("look", f"large engine archive ({p.stat().st_size // 1_000_000} MB) — is it the game's? ({p.name})", p)
        if p.name == ".env":
            note("look", "a .env file — check it holds no keys before sharing", p)
        if safety.is_probably_text(p):
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for label in safety.scan_text_for_secrets(text):
                note("look", f"possible {label} in a shared file", p)
            if safety.DECOMPILER_HINTS.search(text):
                note("tidy", "decompiler fingerprints (FUN_/DAT_/sub_…) — usually cleaned before shipping", p)

    if next((p for p in files if p.name.lower() in {"readme.md", "readme.txt"}), None) is None:
        note("tidy", "no README — add install steps, requirements, credits and AI disclosure")

    manifests = [p for p in files if p.name == "fal_manifest.jsonl"]
    readme = next((p for p in files if p.name.lower() == "readme.md"), None)
    if manifests and readme:
        rt = readme.read_text(encoding="utf-8", errors="replace").lower()
        if "fal" not in rt:
            note("tidy", "fal assets were generated but the README doesn't credit fal — add the credit line")

    # smali/jadx output dirs — a heads-up, not a verdict
    for d in folder.rglob("smali*"):
        if d.is_dir():
            note("look", "a smali/ dir — keep decompiled code out of what you share", d)
            break

    summary = {"folder": str(folder), "files": len(files), "notes": notes,
               "look": sum(n["level"] == "look" for n in notes), "tidy": sum(n["level"] == "tidy" for n in notes)}
    if json_out:
        common.emit(summary, as_json=True)
        return
    if not notes:
        typer.echo(f"am: nothing to flag in {folder} ({len(files)} files). Still your call to publish.")
    else:
        for n in notes:
            tag = "LOOK" if n["level"] == "look" else "tidy"
            where = f"  ({n['path']})" if n["path"] else ""
            typer.echo(f"  [{tag}] {n['note']}{where}")
        typer.echo(f"\nam: {summary['look']} to look at, {summary['tidy']} to tidy. Advisory only — "
                   "review, then it's your call to publish.")


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="publish")
