"""seed auth — credential management commands."""
from __future__ import annotations

import typer
from rich.prompt import Prompt

from seed import SeedClient
from seed.credentials import (
    clear_credentials,
    credentials_configured,
    write_credentials,
)
from seed.exceptions import SeedError

from ..console import console, err, info, ok, warn

app = typer.Typer(help="Manage Seed credentials.")


@app.command("login")
def login(
    profile: str = typer.Option("default", help="Credentials profile name."),
) -> None:
    """Interactively store FAL_KEY in ~/.seed/credentials."""
    console.print("\n[bold]Seed — credential setup[/bold]")
    console.print("Credentials are stored in [cyan]~/.seed/credentials[/cyan] (chmod 600).\n")
    console.print("Seed Audio currently runs on fal.ai.")
    console.print("Get a key at: [url]https://fal.ai/dashboard/keys[/url]\n")

    fal_key = Prompt.ask("  FAL_KEY  (fal.ai API key)", password=True)

    if not fal_key:
        err("FAL_KEY is required. Aborting.")
        raise typer.Exit(1)

    write_credentials(fal_key.strip(), profile=profile)
    ok(f"Credentials saved to ~/.seed/credentials  [profile: {profile}]")

    info("Verifying configuration with seed ping…")
    try:
        result = SeedClient(fal_key=fal_key.strip(), profile=profile).ping()
        ok(f"Ready  (SDK v{result['version']}, provider: {result['provider']})")
    except SeedError as exc:
        warn(f"Saved, but ping failed: {exc}")


@app.command("check")
def check(
    profile: str = typer.Option("default", help="Credentials profile name."),
) -> None:
    """Check which credentials are currently configured."""
    status = credentials_configured(profile=profile)
    console.print(f"\n[bold]Credential status[/bold]  (profile: [cyan]{profile}[/cyan])\n")

    for key, label in [
        ("fal_key", "FAL_KEY                (audio generation)   "),
        ("byteplus_seed_api_key", "BYTEPLUS_SEED_API_KEY  (future native API)  "),
    ]:
        mark = "[success]✔[/success]" if status[key] else "[error]✖[/error]"
        state = "configured" if status[key] else "missing"
        console.print(f"  {mark}  {label}  [dim]{state}[/dim]")

    if status["fal_key"]:
        console.print("\n  [success]FAL_KEY is configured — ready to generate.[/success]\n")
    else:
        console.print("\n  [error]Missing:[/error] FAL_KEY")
        console.print("  Run [cyan]seed auth login[/cyan] to configure.\n")
        raise typer.Exit(1)


@app.command("logout")
def logout(
    profile: str = typer.Option("default", help="Credentials profile to remove."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
) -> None:
    """Remove stored credentials for a profile."""
    if not yes:
        typer.confirm(f"Remove credentials for profile '{profile}'?", abort=True)
    existed = clear_credentials(profile=profile)
    if existed:
        ok(f"Credentials removed for profile '{profile}'.")
    else:
        warn("No credentials file found — nothing to remove.")
