"""Shared guardrails: what the toolkit will and won't help with, and the pre-publish lint patterns.

These are intentionally small and readable. The full reasoning lives in
skills/mod-android-game/references/safety.md; the strings here are what code can check mechanically.
"""
from __future__ import annotations

import re
from pathlib import Path

# Lines the agent keeps in view at every step. Printed by `am scan` and `am --rules`.
HARD_RULES = [
    "Only mod apps the user owns, offline, or servers the user runs.",
    "Prefer the friendly route: open-source games, official modding APIs, your own debug builds, and assets.",
    "Never defeat an anti-cheat, a packer, DRM, Play Integrity/SafetyNet, licensing or in-app billing — if "
    "the only route runs through one of those, stop and tell the user.",
    "Back up app data before touching it (am backup), and confirm before installing or publishing.",
    "Ship your own code and assets, or patches that run on the user's own files — never the game's files.",
    "Kill processes by exact package/pid, keep any bridge bound to 127.0.0.1, and write a MODLOG.md as you go.",
]

# Protection kinds (as apkinfo reports them) that mean "do not repackage this app".
STOP_PROTECTIONS = {"packer", "anti-cheat", "anti-tamper", "pairip"}

# Secrets that must never land in a shared mod folder.
SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    # a real fal key has digits; this avoids matching words like "fal-generated"
    ("fal key", re.compile(r"\bfal-(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{12,}")),
    ("fal key-id:secret", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:[0-9a-f]{16,}")),
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{20,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
]

# Decompiler fingerprints: not fatal, but you usually don't want them in shipped source.
DECOMPILER_HINTS = re.compile(r"\b(?:FUN_[0-9a-f]+|DAT_[0-9a-f]+|sub_[0-9A-F]+|Decompiled with|/\* loc_[0-9A-F]+)")


def scan_text_for_secrets(text: str) -> list[str]:
    hits = []
    for label, pat in SECRET_PATTERNS:
        if pat.search(text):
            hits.append(label)
    return hits


def is_probably_text(path: Path, probe: int = 2048) -> bool:
    try:
        chunk = path.read_bytes()[:probe]
    except OSError:
        return False
    if b"\x00" in chunk:
        return False
    return True
