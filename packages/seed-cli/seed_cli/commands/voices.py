"""seed voices — list available preset voices."""
from __future__ import annotations

import typer

from seed import SeedClient
from seed.exceptions import SeedError

from ..console import console, err
from ..formatters import voices_table

app = typer.Typer(help="List Seed Audio preset voices.")


@app.callback(invoke_without_command=True)
def voices(
    ctx: typer.Context,
    profile: str = typer.Option("default", "--profile", help="Credentials profile."),
) -> None:
    """List all available Seed Audio preset voice ids."""
    if ctx.invoked_subcommand is not None:
        return

    client = SeedClient(profile=profile)
    try:
        data = client.list_voices()
    except SeedError as exc:
        err(str(exc))
        raise typer.Exit(1) from exc

    console.print()
    voices_table(data["voices"])
    console.print(
        f"\n  {data['count']} preset voices. "
        "Or clone a voice with [cyan]--audio-ref <url>[/cyan].\n"
    )
