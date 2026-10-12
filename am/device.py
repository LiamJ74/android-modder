"""`am device/shot/record/drive/logcat`: adb-driven capture, input and log reading for the device/emulator.

Nothing here touches another app's files; it's the "watch the game and drive the menus" layer. Input
automation takes over the device, so `drive` asks before acting unless given --yes.
"""
from __future__ import annotations

import time
from pathlib import Path

import typer

from am import common
from am.adb import Adb, adb_path, parse_devices

device_app = typer.Typer(help="Devices, emulators, app launch/stop, crash cleanup.", no_args_is_help=True)
shot_app = typer.Typer(help="Screenshot the device.")
record_app = typer.Typer(help="Record the device screen.")
drive_app = typer.Typer(help="Tap, swipe, type, press keys, dump the UI tree.", no_args_is_help=True)
logcat_app = typer.Typer(help="Read the device log, filtered to one app or to crashes.")


# -- device --------------------------------------------------------------------------------------------------
@device_app.command("list")
def device_list(json_out: bool = typer.Option(False, "--json")):
    """List attached devices and emulators."""
    try:
        out = common.run([adb_path(), "devices", "-l"]).stdout
    except common.ToolError as e:
        common.die(str(e))
    devs = parse_devices(out)
    common.emit(devs if json_out else "\n".join(
        f"{d['serial']:24} {d['state']:10} {d.get('model', '')}" for d in devs) or "(no devices)", as_json=json_out)


@device_app.command("info")
def device_info(serial: str = typer.Option(None, "--serial", "-s")):
    """Model, Android version, ABIs, screen size, root status."""
    try:
        common.emit(Adb(serial).pick().info(), as_json=True)
    except common.ToolError as e:
        common.die(str(e))


@device_app.command("launch")
def device_launch(package: str, serial: str = typer.Option(None, "--serial", "-s")):
    """Launch an app by package (its default launcher activity)."""
    try:
        adb = Adb(serial).pick()
        adb.shell(["monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"])
        typer.echo(f"am: launched {package}")
    except common.ToolError as e:
        common.die(str(e))


@device_app.command("stop")
def device_stop(package: str, serial: str = typer.Option(None, "--serial", "-s")):
    """Force-stop an app by package (clean, by name — not a wildcard process kill)."""
    try:
        Adb(serial).pick().shell(["am", "force-stop", package])
        typer.echo(f"am: stopped {package}")
    except common.ToolError as e:
        common.die(str(e))


@device_app.command("crash-clean")
def device_crash_clean(serial: str = typer.Option(None, "--serial", "-s")):
    """Dismiss a stuck 'app isn't responding' / crash dialog so the next launch isn't wedged."""
    try:
        adb = Adb(serial).pick()
        adb.shell("input keyevent KEYCODE_BACK", check=False)
        typer.echo("am: sent BACK to clear any crash dialog")
    except common.ToolError as e:
        common.die(str(e))


avd_app = typer.Typer(help="Android Virtual Devices (emulator).", no_args_is_help=True)
device_app.add_typer(avd_app, name="avd")


@avd_app.command("list")
def avd_list():
    """List AVDs (needs the Android SDK emulator on PATH or AM_EMULATOR)."""
    exe = common.find_tool("emulator", env="AM_EMULATOR", extra=common.sdk_dirs("emulator"))
    if not exe:
        common.die("emulator not found: install the Android SDK emulator, or set AM_EMULATOR")
    common.emit(common.run([exe, "-list-avds"]).stdout.strip() or "(no AVDs)")


@avd_app.command("start")
def avd_start(name: str, no_window: bool = typer.Option(False, "--no-window", help="headless")):
    """Start an AVD by name (runs in the background; returns once adb sees it)."""
    exe = common.find_tool("emulator", env="AM_EMULATOR", extra=common.sdk_dirs("emulator"))
    if not exe:
        common.die("emulator not found: install the Android SDK emulator, or set AM_EMULATOR")
    import subprocess

    args = [exe, "-avd", name]
    if no_window:
        args += ["-no-window", "-no-audio"]
    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    typer.echo(f"am: starting AVD {name} … (watch `am device list`)")


# -- shot ----------------------------------------------------------------------------------------------------
@shot_app.callback(invoke_without_command=True)
def shot(
    out: Path = typer.Option(Path("shot.png"), "--out", "-o"),
    serial: str = typer.Option(None, "--serial", "-s"),
):
    """Grab a screenshot straight to a PNG (via exec-out screencap, no temp file on the device)."""
    try:
        png = Adb(serial).pick().exec_out("screencap -p", timeout=60)
    except common.ToolError as e:
        common.die(str(e))
    # some devices/shells turn \n into \r\n on the stream; undo it for PNG integrity
    png = png.replace(b"\r\n", b"\n")
    out.write_bytes(png)
    typer.echo(f"am: wrote {out} ({len(png)} bytes)")


# -- record --------------------------------------------------------------------------------------------------
@record_app.callback(invoke_without_command=True)
def record(
    out: Path = typer.Option(Path("record.mp4"), "--out", "-o"),
    seconds: int = typer.Option(10, "--seconds", "-t", help="max 180 (screenrecord limit)"),
    serial: str = typer.Option(None, "--serial", "-s"),
):
    """Record the screen for N seconds, then pull the mp4 (uses the device's screenrecord)."""
    seconds = min(seconds, 180)
    remote = "/sdcard/am_record.mp4"
    try:
        adb = Adb(serial).pick()
        typer.echo(f"am: recording {seconds}s …")
        adb.shell(["screenrecord", "--time-limit", str(seconds), remote], timeout=seconds + 30)
        adb.pull(remote, out)
        adb.shell(["rm", "-f", remote], check=False)
    except common.ToolError as e:
        common.die(str(e))
    typer.echo(f"am: wrote {out}")


# -- drive ---------------------------------------------------------------------------------------------------
@drive_app.command("tap")
def drive_tap(x: int, y: int, serial: str = typer.Option(None, "--serial", "-s"),
              yes: bool = typer.Option(False, "--yes", "-y")):
    """Tap at x y."""
    common.confirm(f"Drive the device: tap ({x},{y})?", yes)
    _input(serial, ["tap", str(x), str(y)])


@drive_app.command("swipe")
def drive_swipe(x1: int, y1: int, x2: int, y2: int, ms: int = typer.Option(300, "--ms"),
                serial: str = typer.Option(None, "--serial", "-s"), yes: bool = typer.Option(False, "--yes", "-y")):
    """Swipe from (x1,y1) to (x2,y2) over MS milliseconds."""
    common.confirm(f"Drive the device: swipe ({x1},{y1})->({x2},{y2})?", yes)
    _input(serial, ["swipe", str(x1), str(y1), str(x2), str(y2), str(ms)])


@drive_app.command("text")
def drive_text(text: str, serial: str = typer.Option(None, "--serial", "-s"),
               yes: bool = typer.Option(False, "--yes", "-y")):
    """Type TEXT into the focused field."""
    common.confirm(f"Drive the device: type {text!r}?", yes)
    _input(serial, ["text", text.replace(" ", "%s")])


@drive_app.command("key")
def drive_key(keycode: str, serial: str = typer.Option(None, "--serial", "-s"),
              yes: bool = typer.Option(False, "--yes", "-y")):
    """Press a key (e.g. BACK, HOME, ENTER, or a KEYCODE_* name/number)."""
    common.confirm(f"Drive the device: key {keycode}?", yes)
    kc = keycode if keycode.isdigit() or keycode.startswith("KEYCODE_") else "KEYCODE_" + keycode.upper()
    _input(serial, ["keyevent", kc])


@drive_app.command("ui")
def drive_ui(serial: str = typer.Option(None, "--serial", "-s"),
             out: Path = typer.Option(None, "--out", "-o", help="save the XML here")):
    """Dump the current UI tree (uiautomator) so you can find tap targets by resource-id/text."""
    try:
        adb = Adb(serial).pick()
        adb.shell(["uiautomator", "dump", "/sdcard/am_ui.xml"], timeout=60)
        xml = adb.exec_out("cat /sdcard/am_ui.xml", timeout=60).decode("utf-8", "replace")
        adb.shell(["rm", "-f", "/sdcard/am_ui.xml"], check=False)
    except common.ToolError as e:
        common.die(str(e))
    if out:
        out.write_text(xml, encoding="utf-8")
        typer.echo(f"am: wrote {out}")
    else:
        typer.echo(xml)


def _input(serial: str | None, args: list[str]) -> None:
    try:
        Adb(serial).pick().shell(["input"] + args)
    except common.ToolError as e:
        common.die(str(e))


# -- logcat --------------------------------------------------------------------------------------------------
@logcat_app.callback(invoke_without_command=True)
def logcat(
    package: str = typer.Option(None, "--package", "-p", help="only this app's lines (by pid)"),
    crash: bool = typer.Option(False, "--crash", help="only the crash buffer"),
    clear: bool = typer.Option(False, "--clear", help="clear the log first"),
    lines: int = typer.Option(200, "--lines", "-n"),
    serial: str = typer.Option(None, "--serial", "-s"),
):
    """Dump the recent log. With --package, filter to that app's process."""
    try:
        adb = Adb(serial).pick()
        if clear:
            adb.shell("logcat -c", check=False)
            time.sleep(0.2)
        args = ["logcat", "-d", "-t", str(lines)]
        if crash:
            args += ["-b", "crash"]
        if package:
            pid = adb.pidof(package)
            if pid:
                args += ["--pid", pid]
            else:
                typer.echo(f"am: {package} isn't running; showing unfiltered tail", err=True)
        out = adb._run(args, timeout=60).stdout
    except common.ToolError as e:
        common.die(str(e))
    typer.echo(out)


def register(parent: typer.Typer) -> None:
    parent.add_typer(device_app, name="device")
    parent.add_typer(shot_app, name="shot")
    parent.add_typer(record_app, name="record")
    parent.add_typer(drive_app, name="drive")
    parent.add_typer(logcat_app, name="logcat")
