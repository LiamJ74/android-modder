from __future__ import annotations

import subprocess

import pytest

from am import common
from am.adb import Adb, parse_devices


def test_parse_devices():
    out = (
        "List of devices attached\n"
        "emulator-5554\tdevice product:sdk_gphone model:Pixel_6 transport_id:1\n"
        "ABCD1234\tunauthorized\n"
        "\n"
    )
    devs = parse_devices(out)
    assert devs[0]["serial"] == "emulator-5554"
    assert devs[0]["state"] == "device"
    assert devs[0]["emulator"] is True
    assert devs[0]["model"] == "Pixel_6"
    assert devs[1]["state"] == "unauthorized"


class FakeRunner:
    """Maps a command tail to canned stdout, so Adb needs no real adb binary."""

    def __init__(self, responses: dict[str, str]):
        self.responses = responses
        self.calls: list[list[str]] = []

    def __call__(self, cmd, check=True, binary=False, timeout=None, input=None):
        self.calls.append(cmd)
        key = " ".join(str(c) for c in cmd[1:])  # drop the exe
        for pat, out in self.responses.items():
            if pat in key:
                return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")


def test_pick_single_device():
    runner = FakeRunner({"devices -l": "List\nSER123\tdevice\n"})
    adb = Adb(runner=runner, exe="adb").pick()
    assert adb.serial == "SER123"


def test_pick_none_raises():
    runner = FakeRunner({"devices -l": "List of devices attached\n"})
    with pytest.raises(common.ToolError):
        Adb(runner=runner, exe="adb").pick()


def test_pick_multiple_raises():
    runner = FakeRunner({"devices -l": "List\nA\tdevice\nB\tdevice\n"})
    with pytest.raises(common.ToolError):
        Adb(runner=runner, exe="adb").pick()


def test_packages_parsed():
    runner = FakeRunner({"list packages": "package:com.a\npackage:com.b\n"})
    adb = Adb(serial="S", runner=runner, exe="adb")
    assert adb.packages() == ["com.a", "com.b"]


def test_apk_paths_missing_raises():
    runner = FakeRunner({"path com.x": ""})
    adb = Adb(serial="S", runner=runner, exe="adb")
    with pytest.raises(common.ToolError):
        adb.apk_paths("com.x")
