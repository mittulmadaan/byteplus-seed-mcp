"""seed generate — submit audio generation jobs."""
from __future__ import annotations

import time

import typer
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from seed import SeedClient
from seed.exceptions import SeedError

from ..console import console, err, info, ok

app = typer.Typer(help="Generate audio with Seed Audio 1.0.")


@app.callback(invoke_without_command=True)
def generate(
    ctx: typer.Context,
    prompt: str = typer.Option(..., "--prompt", "-p", help="Text to synthesize or audio description. Reference clones as @Audio1…"),
    voice: str = typer.Option("", "--voice", "-v", help="Preset voice id (see `seed voices`). Omit when using --audio-ref."),
    audio_ref: list[str] | None = typer.Option(None, "--audio-ref", help="Public reference audio URL for voice cloning. Repeatable, max 3. Tag as @Audio1…"),
    image: str = typer.Option("", "--image-url", help="Public reference image URL (mutually exclusive with --audio-ref)."),
    output_format: str = typer.Option("mp3", "--format", "-f", help="mp3 | wav | pcm | ogg_opus."),
    sample_rate: int = typer.Option(24000, "--sample-rate", help="8000 | 16000 | 24000 | 32000 | 44100 | 48000."),
    speed: float = typer.Option(1.0, "--speed", help="Speech speed (0.5–2.0)."),
    volume: float = typer.Option(1.0, "--volume", help="Volume (0.5–2.0)."),
    pitch: int | None = typer.Option(None, "--pitch", help="Pitch shift in semitones (-12…12)."),
    watch: bool = typer.Option(False, "--watch", "-w", help="Auto-poll until the audio is ready."),
    poll_interval: int = typer.Option(5, "--poll-interval", help="Seconds between status checks (--watch mode)."),
    profile: str = typer.Option("default", "--profile", help="Credentials profile."),
) -> None:
    """Submit a Seed Audio generation job.

    Without --watch, prints the request_id and exits immediately.
    Use --watch to poll until the audio URL is ready.
    """
    if ctx.invoked_subcommand is not None:
        return

    client = SeedClient(profile=profile)
    console.print()

    with Live(Text("  Submitting…", style="dim"), console=console, refresh_per_second=8, transient=True) as live:
        live.update(Spinner("dots", text="  Submitting job…", style="cyan"))
        try:
            result = client.submit_audio(
                prompt,
                voice=voice or None,
                audio_urls=audio_ref or None,
                image_url=image or None,
                output_format=output_format,
                sample_rate=sample_rate,
                speed=speed,
                volume=volume,
                pitch=pitch,
            )
        except SeedError as exc:
            err(str(exc))
            raise typer.Exit(1) from exc

    # Synchronous providers (e.g. BytePlus) return the audio immediately.
    if result.succeeded and result.audio_url:
        ok("Audio ready!")
        console.print(f"\n  [url]{result.audio_url}[/url]\n")
        return

    ok(f"Job submitted  [request_id=[task_id]{result.request_id}[/task_id]]")

    if not watch:
        console.print(
            f"\n  Poll status:  [cyan]seed status {result.request_id}[/cyan]\n"
            f"  Watch live:   [cyan]seed watch {result.request_id}[/cyan]\n"
        )
        return

    _watch_task(client, result.request_id, poll_interval)


def _watch_task(client: SeedClient, request_id: str, poll_interval: int) -> None:
    """Poll request_id until terminal, streaming progress."""
    console.print(f"\n  Watching [task_id]{request_id}[/task_id] (polling every {poll_interval}s)…\n")
    elapsed = 0

    with Live(console=console, refresh_per_second=4, transient=True) as live:
        while True:
            live.update(Spinner("dots", text=f"  Generating… [{elapsed}s elapsed]", style="cyan"))
            time.sleep(poll_interval)
            elapsed += poll_interval

            try:
                status = client.check_task(request_id)
            except SeedError as exc:
                err(f"Poll error: {exc}")
                continue

            if status.succeeded:
                live.stop()
                console.print()
                ok(f"Audio ready!  [{elapsed}s]")
                console.print(f"\n  [url]{status.audio_url}[/url]\n")
                return

            if status.terminal:
                live.stop()
                err(f"Task ended with status '{status.status}'.")
                if status.error:
                    info(f"Error details: {status.error}")
                raise typer.Exit(1) from None
