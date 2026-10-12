"""`am` command line: one entry point for every tool, so skills can say `am <group> <cmd>`."""
from __future__ import annotations

import typer

from am import __version__, apk, backup, device, fal, kb, publish, safety, scan, sprite

app = typer.Typer(
    name="am",
    help="android-modder: mod Android games you own, offline — recon, APK toolchain, capture, assets, "
         "field notes. Every group has --help.",
    no_args_is_help=True,
    add_completion=False,
)

for module in (scan, apk, device, backup, fal, sprite, publish, kb):
    module.register(app)


def _version(value: bool):
    if value:
        typer.echo(f"android-modder {__version__}")
        raise typer.Exit()


def _rules(value: bool):
    if value:
        for r in safety.HARD_RULES:
            typer.echo(f"- {r}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(False, "--version", callback=_version, is_eager=True, help="show version"),
    rules: bool = typer.Option(False, "--rules", callback=_rules, is_eager=True,
                               help="print the hard rules and exit"),
):
    pass


def main(argv=None):
    app()


if __name__ == "__main__":
    main()
