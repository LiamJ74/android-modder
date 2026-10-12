"""`am scan`: fingerprint an installed package or an APK/bundle file, and write a MODDING_PLAN.md.

Two modes:
  am scan --list                 list moddable third-party packages on the device
  am scan <package>              pull the APK from the device, then fingerprint it
  am scan <file.apk|.xapk|...>   fingerprint a local APK / bundle (no device needed)

The report is static only: nothing on the device is modified. Protections are reported, not touched.
"""
from __future__ import annotations

from pathlib import Path

import typer

from am import apkinfo, common, safety
from am.adb import Adb

app = typer.Typer(help=__doc__, no_args_is_help=True)


def _render_plan(report: dict) -> str:
    r = report
    lines = [
        f"# Modding plan: {r['package']}",
        "",
        f"- **Version:** {r.get('versionName')} (code {r.get('versionCode')})",
        f"- **Engine:** {r['engine']} — {r['engine_description']}",
        f"  - evidence: {', '.join(r['engine_evidence'])}",
        f"  - playbook: `{r['playbook']}`",
        f"- **ABIs:** {', '.join(r['abis']) or 'none (no native libs)'}",
        f"- **Min/target SDK:** {r.get('minSdk')} / {r.get('targetSdk')}",
        f"- **Debuggable:** {r['debuggable']}  ·  **allowBackup:** {r['allowBackup']}",
        f"- **Signing:** {', '.join(r['signing_schemes']) or 'unknown'}"
        + ("  ·  **bundle/splits:** " + ', '.join(r['splits']) if r['is_bundle'] else ""),
        f"- **Online (INTERNET):** {r['online']}",
        f"- **Obfuscated:** {r['obfuscation']['obfuscated']} "
        f"({r['obfuscation']['short_name_ratio']:.0%} short class names)",
        "",
    ]
    if r["protections"]:
        lines += ["## Protections (respect these — do not defeat them)", ""]
        for p in r["protections"]:
            stop = "  **STOP SIGN**" if p["kind"] in safety.STOP_PROTECTIONS else ""
            lines.append(f"- `{p['kind']}` — {p['detail']}{stop}")
        lines.append("")
        if any(p["kind"] in safety.STOP_PROTECTIONS for p in r["protections"]):
            lines += ["> This app carries a packer / anti-tamper / anti-cheat. Repackaging it is out of scope. "
                      "Use an official modding surface, an open-source build, or ask the user.", ""]
    if r["sdks"]:
        lines += ["## Third-party SDKs", "", *[f"- {s}" for s in r["sdks"]], ""]
    lines += ["## Where the app keeps its data", ""]
    for loc in r["data_locations"]:
        lines.append(f"- `{loc['path']}` — {loc['what']}  _(access: {loc['access']})_")
    lines += ["", "## Candidate routes (cheapest first)", ""]
    for route in r["routes"]:
        lines.append(f"- {route}")
    lines += ["", "## Rules", "", *[f"- {rule}" for rule in safety.HARD_RULES], ""]
    lines += ["## Next", "",
              "1. Confirm the user owns this and it's offline / their own server.",
              "2. `am backup create <package>` before any change.",
              "3. Read the playbook above and the knowledge base (`am kb search`).",
              "4. Build a vertical slice, verify on device, write the MODLOG.md.", ""]
    return "\n".join(lines)


@app.command("list")
def list_packages(
    serial: str = typer.Option(None, "--serial", "-s", help="device serial (else the only one attached)"),
    json_out: bool = typer.Option(False, "--json"),
):
    """List third-party (user-installed) packages — the moddable candidates."""
    try:
        adb = Adb(serial).pick()
        pkgs = adb.packages(third_party=True)
    except common.ToolError as e:
        common.die(str(e))
    common.emit(pkgs if json_out else "\n".join(pkgs), as_json=json_out)


@app.command()
def info(
    target: str = typer.Argument(..., help="a package name on the device, or a path to an .apk/.xapk/.apks/.apkm"),
    serial: str = typer.Option(None, "--serial", "-s"),
    out: Path = typer.Option(None, "--out", "-o", help="write MODDING_PLAN.md here (default: ./MODDING_PLAN.md)"),
    json_out: bool = typer.Option(False, "--json", help="print the raw report as JSON instead of a plan"),
    keep: bool = typer.Option(False, "--keep", help="when pulling from a device, keep the pulled APK under AM_HOME"),
):
    """Fingerprint TARGET and write a modding plan. TARGET is a local file or an installed package."""
    try:
        p = Path(target)
        if p.exists() and p.suffix.lower() in {".apk", ".xapk", ".apks", ".apkm"}:
            report = apkinfo.fingerprint(p)
        else:
            adb = Adb(serial).pick()
            report = _scan_installed(adb, target, keep)
    except (common.ToolError, ValueError) as e:
        common.die(str(e))

    if json_out:
        common.emit(report, as_json=True)
        return
    plan = _render_plan(report)
    dest = out or Path("MODDING_PLAN.md")
    dest.write_text(plan, encoding="utf-8")
    typer.echo(plan)
    typer.echo(f"\nam: wrote {dest}")


def _scan_installed(adb: Adb, package: str, keep: bool) -> dict:
    paths = adb.apk_paths(package)
    base = next((p for p in paths if p.endswith("base.apk")), paths[0])
    dest_dir = common.data_dir() / "pulled" / package
    dest_dir.mkdir(parents=True, exist_ok=True)
    local = dest_dir / "base.apk"
    adb.pull(base, local)
    report = apkinfo.fingerprint(local)
    report["installed"] = adb.package_info(package)
    report["device"] = adb.info()
    report["apk_source"] = str(local) if keep else "(pulled APK kept out of any repo under AM_HOME)"
    if not keep:
        typer.echo(f"am: pulled base.apk to {local} (under AM_HOME — never commit it)", err=True)
    return report


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="scan")
