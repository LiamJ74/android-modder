"""`am backup`: snapshot and restore an app's own data before you touch it.

Three ways in, tried in order of what the device allows:
  - run-as   (debuggable builds): tar /data/data/<pkg> without root — the clean path for your own builds
  - root     (su): tar /data/data/<pkg> as root
  - adb backup (ab): the legacy full-backup for apps that still allow it

Every snapshot carries a manifest.json (package, method, time, sha256) so restore is one command and you can
diff two snapshots. Snapshots live under AM_HOME, never in a repo.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import typer

from am import common
from am.adb import Adb

app = typer.Typer(help=__doc__, no_args_is_help=True)


def _store() -> Path:
    d = common.data_dir() / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


@app.command()
def create(
    package: str,
    name: str = typer.Option(None, "--name", help="label for the snapshot (default: package+timestamp)"),
    serial: str = typer.Option(None, "--serial", "-s"),
):
    """Snapshot <package>'s data to AM_HOME. Picks run-as, root, or adb backup automatically."""
    try:
        adb = Adb(serial).pick()
        label = name or f"{package}-{time.strftime('%Y%m%d-%H%M%S')}"
        dest = _store() / label
        dest.mkdir(parents=True, exist_ok=True)
        method, artifact = _capture(adb, package, dest)
    except common.ToolError as e:
        common.die(str(e))
    manifest = {
        "package": package, "method": method, "serial": adb.serial,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "artifact": artifact.name,
        "sha256": common.sha256(artifact), "bytes": artifact.stat().st_size,
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    typer.echo(f"am: backed up {package} via {method} -> {dest}")
    common.emit(manifest, as_json=True)


def _capture(adb: Adb, package: str, dest: Path) -> tuple[str, Path]:
    if adb.can_run_as(package):
        tar = dest / "data.tar"
        raw = adb.exec_out(f"run-as {package} tar -c -C /data/data/{package} .", timeout=600)
        tar.write_bytes(raw)
        return "run-as", tar
    if adb.is_rooted():
        tar = dest / "data.tar"
        raw = adb.exec_out(f"su -c 'tar -c -C /data/data/{package} .'", timeout=600)
        tar.write_bytes(raw)
        return "root", tar
    ab = dest / "data.ab"
    typer.echo("am: no run-as/root — using adb backup. Confirm the restore/backup prompt ON THE DEVICE.",
               err=True)
    adb._run(["backup", "-f", str(ab), "-noapk", package], timeout=600)
    if not ab.exists() or ab.stat().st_size < 100:
        raise common.ToolError("adb backup produced nothing (modern Android often disables it; use a debug "
                               "build for run-as, or root)")
    return "adb-backup", ab


@app.command("list")
def list_backups(json_out: bool = typer.Option(False, "--json")):
    """List snapshots under AM_HOME."""
    rows = []
    for d in sorted(_store().iterdir()):
        mf = d / "manifest.json"
        if mf.exists():
            rows.append(json.loads(mf.read_text(encoding="utf-8")) | {"label": d.name})
    common.emit(rows if json_out else "\n".join(
        f"{r['label']:34} {r['method']:11} {r['package']:28} {r.get('created', '')}" for r in rows)
        or "(no snapshots)", as_json=json_out)


@app.command()
def diff(label_a: str, label_b: str):
    """Compare two snapshots by file list + sha (tar snapshots only)."""
    import tarfile

    def entries(label: str) -> dict[str, int]:
        tar = _store() / label / "data.tar"
        if not tar.exists():
            common.die(f"{label} has no data.tar (adb-backup snapshots can't be diffed)")
        with tarfile.open(tar) as t:
            return {m.name: m.size for m in t.getmembers() if m.isfile()}

    a, b = entries(label_a), entries(label_b)
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    changed = sorted(n for n in set(a) & set(b) if a[n] != b[n])
    common.emit({"added": added, "removed": removed, "changed_size": changed}, as_json=True)


@app.command()
def restore(
    label: str,
    serial: str = typer.Option(None, "--serial", "-s"),
    yes: bool = typer.Option(False, "--yes", "-y"),
):
    """Restore a snapshot back onto the device. Overwrites the app's current data — asks first."""
    dest = _store() / label
    mf = dest / "manifest.json"
    if not mf.exists():
        common.die(f"no snapshot named {label} (see `am backup list`)")
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    package, method = manifest["package"], manifest["method"]
    common.confirm(f"Restore {label} onto {package} via {method}? This overwrites its current data.", yes)
    try:
        adb = Adb(serial).pick()
        if method in ("run-as", "root"):
            tar = dest / "data.tar"
            cmd = (f"run-as {package} tar -x -C /data/data/{package}" if method == "run-as"
                   else f"su -c 'tar -x -C /data/data/{package}'")
            # stream the tar into the device-side extractor over `adb shell` stdin
            adb._run(["shell", cmd], binary=True, input=tar.read_bytes(), timeout=600)
        else:
            adb._run(["restore", str(dest / "data.ab")], timeout=600)
            typer.echo("am: confirm the restore prompt ON THE DEVICE.", err=True)
    except common.ToolError as e:
        common.die(str(e))
    typer.echo(f"am: restored {label} onto {package}")


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="backup")
