"""`am kb`: the shared knowledge base of field notes — search it, write one, check it, rebuild the index.

A note is a Markdown file under knowledge/techniques/ with a YAML front matter (see knowledge/TEMPLATE.md).
`am kb index` rebuilds knowledge/INDEX.md and knowledge/index.json from the notes; `am kb check` fails CI if
they're stale or a note is malformed.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import typer

from am import common

app = typer.Typer(help=__doc__, no_args_is_help=True)

REQUIRED_KEYS = ["kind", "title", "game", "engine", "route", "status", "date"]


def kb_root() -> Path:
    """The repo's knowledge/ dir. Override with AM_KB. Falls back to the package-relative location."""
    import os

    if os.environ.get("AM_KB"):
        return Path(os.environ["AM_KB"])
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "knowledge").is_dir():
            return parent / "knowledge"
    return Path.cwd() / "knowledge"


@dataclass
class Note:
    path: Path
    meta: dict
    body: str


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Minimal YAML front matter: `key: value`, lists as [a, b] or '- ' blocks. No external YAML needed."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    try:
        import yaml

        return yaml.safe_load(raw) or {}, body
    except Exception:
        pass
    meta: dict = {}
    key = None
    for line in raw.splitlines():
        if re.match(r"^\s*#", line) or not line.strip():
            continue
        if line.startswith("  - ") and key:
            meta.setdefault(key, [])
            if isinstance(meta[key], list):
                meta[key].append(line[4:].strip().strip('"'))
            continue
        m = re.match(r'^([A-Za-z_]+):\s*(.*)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                meta[key] = [v.strip().strip('"') for v in inner.split(",")] if inner else []
            elif val in ("", "|", ">"):
                meta[key] = []
            else:
                meta[key] = val.strip('"')
    return meta, body


def load_notes() -> list[Note]:
    notes = []
    tdir = kb_root() / "techniques"
    if not tdir.is_dir():
        return notes
    for p in sorted(tdir.glob("*.md")):
        meta, body = parse_front_matter(p.read_text(encoding="utf-8"))
        notes.append(Note(p, meta, body))
    return notes


@app.command()
def search(query: str, json_out: bool = typer.Option(False, "--json")):
    """Full-text search over field notes (title, game, engine, tags, body)."""
    q = query.lower()
    hits = []
    for n in load_notes():
        hay = " ".join(str(v) for v in n.meta.values()).lower() + " " + n.body.lower()
        if all(term in hay for term in q.split()):
            hits.append({"title": n.meta.get("title", n.path.stem), "game": n.meta.get("game"),
                         "engine": n.meta.get("engine"), "route": n.meta.get("route"),
                         "status": n.meta.get("status"), "file": str(n.path.relative_to(kb_root().parent))})
    if json_out:
        common.emit(hits, as_json=True)
    elif not hits:
        typer.echo(f"am: no notes match {query!r} (yet — write one with `am kb new`)")
    else:
        for h in hits:
            typer.echo(f"- {h['title']}  [{h['game']} / {h['engine']} / {h['route']}]\n    {h['file']}")


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:80] or "note"


@app.command()
def new(
    title: str = typer.Option(..., "--title", prompt=True),
    game: str = typer.Option(..., "--game", prompt=True),
    engine: str = typer.Option("unknown", "--engine"),
    route: str = typer.Option("other", "--route"),
):
    """Create a new field note from the template, pre-filled."""
    tpl = kb_root() / "TEMPLATE.md"
    text = tpl.read_text(encoding="utf-8") if tpl.exists() else "---\n---\n# {title}\n"
    meta, body = parse_front_matter(text)
    dest = kb_root() / "techniques" / f"{slugify(title)}.md"
    if dest.exists():
        common.die(f"already exists: {dest}")
    from datetime import date

    front = {**meta, "kind": "game", "title": title, "game": game, "engine": engine, "route": route,
             "status": "in-progress", "date": date.today().isoformat()}
    lines = ["---"]
    for k, v in front.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        else:
            lines.append(f'{k}: "{v}"' if isinstance(v, str) and (":" in v or "," in v) else f"{k}: {v}")
    lines.append("---\n")
    # keep the template's body (its section headings), dropping its own leading H1
    tail = re.sub(r"\A#[^\n]*\n", "", body).lstrip("\n") if body else ""
    dest.write_text("\n".join(lines) + f"\n# {title}\n\n" + tail, encoding="utf-8")
    typer.echo(f"am: wrote {dest}")


def build_index() -> tuple[str, list[dict]]:
    notes = load_notes()
    rows = []
    for n in notes:
        rows.append({k: n.meta.get(k) for k in ("title", "game", "engine", "route", "status", "date")}
                    | {"file": f"techniques/{n.path.name}"})
    rows.sort(key=lambda r: (str(r.get("game")), str(r.get("title"))))
    md = ["# Knowledge base index", "", f"{len(rows)} field note(s).", "",
          "| Title | Game | Engine | Route | Status |", "|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| [{r['title']}]({r['file']}) | {r['game']} | {r['engine']} | {r['route']} | {r['status']} |")
    return "\n".join(md) + "\n", rows


@app.command()
def index():
    """Rebuild knowledge/INDEX.md and knowledge/index.json from the notes."""
    md, rows = build_index()
    (kb_root() / "INDEX.md").write_text(md, encoding="utf-8")
    (kb_root() / "index.json").write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
    typer.echo(f"am: indexed {len(rows)} note(s)")


@app.command()
def check(index_fresh: bool = typer.Option(False, "--index", help="also fail if INDEX.md is stale")):
    """Validate every note's front matter; with --index, fail if the index is out of date (for CI)."""
    problems = []
    for n in load_notes():
        for key in REQUIRED_KEYS:
            if not n.meta.get(key):
                problems.append(f"{n.path.name}: missing '{key}'")
    if index_fresh:
        md, rows = build_index()
        cur = (kb_root() / "INDEX.md")
        if not cur.exists() or cur.read_text(encoding="utf-8") != md:
            problems.append("INDEX.md is stale — run `am kb index`")
    if problems:
        for p in problems:
            typer.echo(f"am: {p}", err=True)
        raise typer.Exit(1)
    typer.echo("am: knowledge base OK")


def register(parent: typer.Typer) -> None:
    parent.add_typer(app, name="kb")
