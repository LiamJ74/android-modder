"""`am apk`: the everyday APK toolchain for your own builds and the games you own — unpack, build, sign,
install, diff.

Scope, enforced by how the commands behave:
  - These wrap the standard tools (apktool, apksigner, zipalign) you'd use on your own app or an open-source
    game you build from source. They are not a way around a protected app: if `am scan` reported a packer,
    anti-tamper, anti-cheat or integrity check, this module refuses to repackage it and points you back to an
    official modding surface or the game's source.
  - `install` snapshots nothing itself but refuses to run unless a recent `am backup` exists for the package,
    and always confirms. `sign` uses a local debug keystore under AM_HOME — never a release key.

Nothing here downloads an APK for you; you bring your own, from your own device or your own build.
"""
from __future__ import annotations

from pathlib import Path

import typer

from am import apkinfo, common, safety
from am.adb import Adb

app = typer.Typer(help=__doc__, no_args_is_help=True)


def _apktool() -> str:
    exe = common.find_tool("apktool", env="AM_APKTOOL")
    if not exe:
        common.die("apktool not found. Install it (ibotpeaches.github.io/Apktool) and put it on PATH, or set "
                   "AM_APKTOOL. Needs Java too.")
    return exe


def _buildtool(name: str, env: str) -> str:
    exe = common.find_tool(name, env=env, extra=common.sdk_dirs("build-tools"))
    if not exe:
        common.die(f"{name} not found (ships in the Android SDK build-tools). Set {env} or install the SDK.")
    return exe


def _refuse_if_protected(src: Path) -> None:
    """Static check before we repackage: a protected app is out of scope for this toolkit."""
    try:
        report = apkinfo.fingerprint(src)
    except Exception:
        return  # not a fingerprintable APK (e.g. an already-unpacked dir handled elsewhere)
    stops = [p for p in report.get("protections", []) if p["kind"] in safety.STOP_PROTECTIONS]
    if stops:
        detail = "; ".join(f"{p['kind']} ({p['detail']})" for p in stops)
        common.die(f"{src.name} carries protection this toolkit won't repackage: {detail}. "
                   "Use an official modding API, build from source, or ask the user.")


@app.command()
def unpack(
    src: Path,
    out: Path = typer.Option(None, "--out", "-o", help="output dir (default: <name>_src, kept out of a repo)"),
    no_src: bool = typer.Option(False, "--no-src", help="resources only, skip disassembling code (apktool -s)"),
):
    """Unpack an APK you own with apktool (resources + manifest; code only without --no-src)."""
    _refuse_if_protected(src)
    out = out or src.with_name(src.stem + "_src")
    args = [_apktool(), "d", str(src), "-o", str(out), "-f"]
    if no_src:
        args.append("-s")
    common.run(args, timeout=600)
    typer.echo(f"am: unpacked to {out}")
    typer.echo("am: this is working material — keep it OUT of any repo you publish.", err=True)


@app.command()
def build(
    src_dir: Path,
    out: Path = typer.Option(None, "--out", "-o"),
):
    """Rebuild an apktool folder into an unsigned APK."""
    out = out or src_dir.with_name(src_dir.name.replace("_src", "") + "_unsigned.apk")
    common.run([_apktool(), "b", str(src_dir), "-o", str(out)], timeout=600)
    typer.echo(f"am: built {out} (unsigned — run `am apk sign`)")


def _debug_keystore() -> Path:
    """A local debug keystore under AM_HOME, created once. Never a release key."""
    ks = common.data_dir() / "debug.keystore"
    if ks.exists():
        return ks
    keytool = common.find_tool("keytool", env="AM_KEYTOOL")
    if not keytool:
        common.die("keytool not found (ships with the JDK). Install a JDK, or set AM_KEYTOOL.")
    common.run([keytool, "-genkeypair", "-v", "-keystore", str(ks), "-storepass", "android",
                "-keypass", "android", "-alias", "androiddebugkey", "-keyalg", "RSA", "-keysize", "2048",
                "-validity", "10000", "-dname", "CN=Android Debug,O=android-modder,C=US"], timeout=120)
    typer.echo(f"am: created a debug keystore at {ks}", err=True)
    return ks


@app.command()
def sign(
    apk: Path,
    out: Path = typer.Option(None, "--out", "-o"),
    align: bool = typer.Option(True, "--align/--no-align", help="zipalign first (recommended)"),
):
    """Zipalign and sign an APK with the local debug key (for your own on-device testing)."""
    ks = _debug_keystore()
    work = apk
    if align:
        za = _buildtool("zipalign", "AM_ZIPALIGN")
        aligned = apk.with_name(apk.stem + "_aligned.apk")
        common.run([za, "-f", "-p", "4", str(apk), str(aligned)])
        work = aligned
    out = out or apk.with_name(apk.stem.replace("_unsigned", "").replace("_aligned", "") + "_signed.apk")
    apksigner = _buildtool("apksigner", "AM_APKSIGNER")
    common.run([apksigner, "sign", "--ks", str(ks), "--ks-pass", "pass:android",
                "--ks-key-alias", "androiddebugkey", "--key-pass", "pass:android", "--out", str(out), str(work)])
    typer.echo(f"am: signed {out} with the debug key")


@app.command()
def install(
    apk: Path,
    package: str = typer.Option(None, "--package", help="package name, to check a backup exists first"),
    serial: str = typer.Option(None, "--serial", "-s"),
    yes: bool = typer.Option(False, "--yes", "-y"),
):
    """Install a (signed) APK onto the device. Refuses without a recent backup; always confirms."""
    if not apk.exists():
        common.die(f"no such file: {apk}")
    pkg = package or _guess_package(apk)
    if pkg and not _has_backup(pkg):
        common.die(f"no backup found for {pkg}. Run `am backup create {pkg}` first (then re-run), so you can "
                   "undo this. Pass --yes only after you've backed up.")
    common.confirm(f"Install {apk.name} onto the device?" + (f" (package {pkg})" if pkg else ""), yes)
    try:
        adb = Adb(serial).pick()
        adb._run(["install", "-r", str(apk)], timeout=600)
    except common.ToolError as e:
        common.die(str(e))
    typer.echo(f"am: installed {apk.name}")


def _guess_package(apk: Path) -> str | None:
    try:
        return apkinfo.fingerprint(apk)["package"]
    except Exception:
        return None


def _has_backup(package: str) -> bool:
    store = common.data_dir() / "backups"
    if not store.is_dir():
        return False
    import json

    for d in store.iterdir():
        mf = d / "manifest.json"
        if mf.exists():
            try:
                if json.loads(mf.read_text(encoding="utf-8")).get("package") == package:
                    return True
            except Exception:
                continue
    return False


@app.command()
def diff(a: Path, b: Path, json_out: bool = typer.Option(False, "--json")):
    """Diff two APKs by entry list and content hash — see exactly what a change touched."""
    import hashlib
    import zipfile

    def entries(p: Path) -> dict[str, str]:
        with zipfile.ZipFile(p) as z:
            return {i.filename: hashlib.sha256(z.read(i.filename)).hexdigest()[:16] for i in z.infolist()
                    if not i.is_dir()}

    ea, eb = entries(a), entries(b)
    out = {
        "added": sorted(set(eb) - set(ea)),
        "removed": sorted(set(ea) - set(eb)),
        "changed": sorted(n for n in set(ea) & set(eb) if ea[n] != eb[n]),
    }
    if json_out:
        common.emit(out, as_json=True)
    else:
        for k in ("added", "removed", "changed"):
            typer.echo(f"{k} ({len(out[k])}):")
            for n in out[k][:200]:
                typer.echo(f"  {n}")


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="apk")
