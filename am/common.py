"""Small helpers shared by the commands: tool lookup, subprocess, output, per-user state, confirmations."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import typer


class ToolError(RuntimeError):
    """A command failed in a way the user can act on; the CLI prints it and exits 1."""


def die(msg: str, code: int = 1):
    typer.echo(f"am: {msg}", err=True)
    raise typer.Exit(code)


def emit(obj, as_json: bool = False):
    if as_json or not isinstance(obj, str):
        typer.echo(json.dumps(obj, indent=2, default=str, ensure_ascii=False))
    else:
        typer.echo(obj)


def data_dir() -> Path:
    """Per-user state: backups, pulled APKs, the debug keystore. Override with AM_HOME.

    Lives outside any repo on purpose: what lands here (original APKs, app data, keys) is never published.
    """
    d = Path(os.environ.get("AM_HOME", Path.home() / ".android-modder"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def find_tool(name: str, env: str | None = None, extra: list[Path] | None = None) -> str | None:
    """An env override (AM_ADB=...), then PATH (with .bat/.cmd/.exe on Windows), then known install folders."""
    if env and os.environ.get(env):
        return os.environ[env]
    for cand in (name, name + ".bat", name + ".cmd", name + ".exe"):
        found = shutil.which(cand)
        if found:
            return found
    for d in extra or []:
        for cand in (name, name + ".bat", name + ".exe"):
            p = d / cand
            if p.exists():
                return str(p)
    return None


def sdk_dirs(sub: str) -> list[Path]:
    """<sdk>/<sub> for every Android SDK we can guess (ANDROID_HOME, ANDROID_SDK_ROOT, default installs)."""
    roots = [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT")]
    if os.name == "nt":
        roots.append(str(Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk"))
    else:
        roots += [str(Path.home() / "Android" / "Sdk"), str(Path.home() / "Library" / "Android" / "sdk")]
    out = []
    for r in roots:
        if not r:
            continue
        base = Path(r) / sub
        if sub == "build-tools" and base.is_dir():
            # newest build-tools first
            out += sorted((p for p in base.iterdir() if p.is_dir()), reverse=True)
        elif base.is_dir():
            out.append(base)
    return out


def run(cmd: list[str], check: bool = True, binary: bool = False, timeout: float | None = None,
        input: bytes | str | None = None) -> subprocess.CompletedProcess:
    """Run a tool and capture its output. Raises ToolError with the tail of stderr on failure."""
    try:
        cp = subprocess.run([str(c) for c in cmd], capture_output=True, text=not binary, timeout=timeout,
                            input=input)
    except FileNotFoundError as e:
        raise ToolError(f"not found: {cmd[0]}") from e
    except subprocess.TimeoutExpired as e:
        raise ToolError(f"timed out after {timeout}s: {' '.join(map(str, cmd[:4]))}") from e
    if check and cp.returncode != 0:
        err = cp.stderr if not binary else cp.stderr.decode("utf-8", "replace")
        out = cp.stdout if not binary else ""
        head = " ".join(map(str, cmd[:4]))
        raise ToolError(f"{head} ... failed ({cp.returncode}):\n{(err or out or '').strip()[-2000:]}")
    return cp


def confirm(question: str, yes: bool) -> None:
    """Ask before anything that writes to the device or leaves the machine. `--yes` answers for the user."""
    if yes:
        return
    if not sys.stdin or not sys.stdin.isatty():
        die(f"{question} Needs confirmation: re-run with --yes once the user has agreed.")
    if not typer.confirm(question, default=False):
        raise typer.Abort()


def sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()
