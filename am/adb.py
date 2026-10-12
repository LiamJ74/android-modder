"""A thin adb wrapper: one device (serial or the only one attached), shell, pull/push, package queries.

Every call goes through `Adb._run`, so tests swap in a fake runner instead of needing a device.
"""
from __future__ import annotations

import os
import shlex
from collections.abc import Callable
from pathlib import Path

from am import common


def adb_path() -> str:
    found = common.find_tool("adb", env="AM_ADB", extra=common.sdk_dirs("platform-tools"))
    if not found:
        raise common.ToolError(
            "adb not found: install Android platform-tools (or the Android SDK) and put it on PATH, or set AM_ADB")
    return found


def parse_devices(text: str) -> list[dict]:
    """`adb devices -l` output -> [{serial, state, model, ...}]."""
    out = []
    for line in text.splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        parts = line.split()
        d = {"serial": parts[0], "state": parts[1] if len(parts) > 1 else "unknown"}
        for kv in parts[2:]:
            if ":" in kv:
                k, v = kv.split(":", 1)
                d[k] = v
        d["emulator"] = d["serial"].startswith("emulator-")
        out.append(d)
    return out


class Adb:
    def __init__(self, serial: str | None = None, runner: Callable | None = None, exe: str | None = None):
        self._runner = runner or common.run
        self._exe = exe
        self.serial = serial or os.environ.get("ANDROID_SERIAL")

    @property
    def exe(self) -> str:
        if self._exe is None:
            self._exe = adb_path()
        return self._exe

    def _run(self, args: list[str], check: bool = True, binary: bool = False, timeout: float | None = 120,
             input=None):
        cmd = [self.exe] + (["-s", self.serial] if self.serial else []) + list(args)
        return self._runner(cmd, check=check, binary=binary, timeout=timeout, input=input)

    # -- devices ------------------------------------------------------------------------------------------
    def devices(self) -> list[dict]:
        return parse_devices(self._runner([self.exe, "devices", "-l"], check=True, binary=False, timeout=30,
                                          input=None).stdout)

    def pick(self) -> Adb:
        """Fix the serial: the one given, else the only device attached; several -> ask for --serial."""
        if self.serial:
            return self
        ready = [d for d in self.devices() if d["state"] == "device"]
        if not ready:
            raise common.ToolError("no device: plug one in with USB debugging on, or start an emulator "
                                   "(`am device avd start <name>`)")
        if len(ready) > 1:
            raise common.ToolError("several devices attached (" + ", ".join(d["serial"] for d in ready)
                                   + "): pass --serial or set ANDROID_SERIAL")
        self.serial = ready[0]["serial"]
        return self

    # -- shell --------------------------------------------------------------------------------------------
    def shell(self, cmd: str | list[str], check: bool = True, timeout: float | None = 120) -> str:
        if isinstance(cmd, list):
            cmd = " ".join(shlex.quote(c) for c in cmd)
        return self._run(["shell", cmd], check=check, timeout=timeout).stdout

    def exec_out(self, cmd: str, timeout: float | None = 300) -> bytes:
        """Binary-safe stdout (screencap, tar streams)."""
        return self._run(["exec-out", cmd], binary=True, timeout=timeout).stdout

    def pull(self, remote: str, local: Path | str, timeout: float | None = 600) -> None:
        self._run(["pull", remote, str(local)], timeout=timeout)

    def push(self, local: Path | str, remote: str, timeout: float | None = 600) -> None:
        self._run(["push", str(local), remote], timeout=timeout)

    def getprop(self, name: str) -> str:
        return self.shell(["getprop", name], check=False).strip()

    # -- packages -----------------------------------------------------------------------------------------
    def packages(self, third_party: bool = True) -> list[str]:
        out = self.shell(["pm", "list", "packages"] + (["-3"] if third_party else []))
        return sorted(line.split(":", 1)[1].strip() for line in out.splitlines() if line.startswith("package:"))

    def apk_paths(self, package: str) -> list[str]:
        """Every APK of an install: base.apk plus split_config.*.apk for App Bundle installs."""
        out = self.shell(["pm", "path", package], check=False)
        paths = [line.split(":", 1)[1].strip() for line in out.splitlines() if line.startswith("package:")]
        if not paths:
            raise common.ToolError(f"package not installed on the device: {package}")
        return paths

    def package_info(self, package: str) -> dict:
        """versionName/versionCode/flags from `dumpsys package` (the installed truth, splits included)."""
        out = self.shell(["dumpsys", "package", package], check=False)
        info: dict = {"package": package}
        for line in out.splitlines():
            s = line.strip()
            for key in ("versionName=", "versionCode=", "installerPackageName=", "pkgFlags=", "dataDir=",
                        "primaryCpuAbi="):
                if s.startswith(key) or f" {key}" in s:
                    seg = s[s.index(key):]
                    val = seg[len(key):].split(" ")[0]
                    info.setdefault(key[:-1], val)
        return info

    def is_rooted(self) -> bool:
        out = self.shell("su -c id 2>/dev/null || true", check=False)
        return "uid=0" in out

    def can_run_as(self, package: str) -> bool:
        """run-as only works for debuggable builds; that's the no-root way into /data/data/<pkg>."""
        out = self.shell(f"run-as {shlex.quote(package)} id 2>&1 || true", check=False)
        return "uid=" in out and "not debuggable" not in out and "unknown package" not in out

    def pidof(self, package: str) -> str | None:
        out = self.shell(["pidof", package], check=False).strip()
        return out.split()[0] if out else None

    def info(self) -> dict:
        return {
            "serial": self.serial,
            "model": self.getprop("ro.product.model"),
            "android": self.getprop("ro.build.version.release"),
            "sdk": self.getprop("ro.build.version.sdk"),
            "abis": self.getprop("ro.product.cpu.abilist").split(","),
            "emulator": (self.serial or "").startswith("emulator-") or self.getprop("ro.kernel.qemu") == "1",
            "rooted": self.is_rooted(),
            "screen": self.shell(["wm", "size"], check=False).strip().split(":")[-1].strip(),
            "density": self.shell(["wm", "density"], check=False).strip().split(":")[-1].strip(),
        }
