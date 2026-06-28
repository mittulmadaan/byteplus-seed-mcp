"""seed status / watch — task management commands."""
from __future__ import annotations

import typer

from seed import SeedClient
from seed.exceptions import SeedError

from ..commands.generate import _watch_task
from ..console import console, err, info, ok

app = typer.Typer(help="Manage audio generation tasks.")


@app.command("status")
def status(
    request_id: str = typer.Argument(..., help="Request ID to check."),
    profile: str = typer.Option("default", "--profile", help="Credentials profile."),
) -> None:
    """Check the current status of a task."""
    client = SeedClient(profile=profile)
    try:
        result = client.check_task(request_id)
    except SeedError as exc:
        err(str(exc))
        raise typer.Exit(1) from exc

    console.print()
    if result.succeeded:
        ok(f"[task_id]{request_id}[/task_id]  status=[green]completed[/green]")
        console.print(f"\n  [url]{result.audio_url}[/url]\n")
    elif result.terminal:
        err(f"[task_id]{request_id}[/task_id]  status=[red]{result.status}[/red]")
        if result.error:
            info(f"Error: {result.error}")
        raise typer.Exit(1)
    else:
        info(f"[task_id]{request_id}[/task_id]  status=[yellow]{result.status}[/yellow]")
        console.print(f"\n  Watch live:  [cyan]seed watch {request_id}[/cyan]\n")


@app.command("watch")
def watch(
    request_id: str = typer.Argument(..., help="Request ID to watch."),
    poll_interval: int = typer.Option(5, "--poll-interval", help="Seconds between status checks."),
    profile: str = typer.Option("default", "--profile", help="Credentials profile."),
) -> None:
    """Stream live progress for a task until it completes."""
    client = SeedClient(profile=profile)
    _watch_task(client, request_id, poll_interval)
