"""seed skill — install/uninstall the Claude Code skill and MCP server config."""
from __future__ import annotations

import json
import platform
import shutil
import sys
from pathlib import Path

import typer

from ..console import console, err, info, ok, warn

app = typer.Typer(help="Install the Seed skill into Claude Desktop / Claude Code.")

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def _claude_desktop_config() -> Path:
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if system == "Windows":
        return Path(str(Path.home())) / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    return Path.home() / ".config" / "claude" / "claude_desktop_config.json"


def _claude_code_settings() -> Path:
    return Path.home() / ".claude" / "settings.json"


def _claude_code_skills_dir() -> Path:
    return Path.home() / ".claude" / "skills"


def _skill_source() -> Path:
    """Locate the bundled skills/seed.md relative to this package."""
    candidate = Path(__file__).parent.parent.parent.parent.parent / "skills" / "seed.md"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        "skills/seed.md not found. "
        "If you installed seed-cli via pip, ensure you're working inside the repo "
        "or re-install from the repo root."
    )


_MCP_BLOCK = {
    "command": sys.executable,
    "args": ["-m", "seed_mcp"],
}

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command("install")
def install(
    target: str = typer.Option(
        "all", "--target", "-t",
        help="Where to install: all | claude-desktop | claude-code",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would change without writing."),
) -> None:
    """Install the Seed MCP server config and Claude Code skill.

    Idempotent — safe to re-run. Patches existing config files rather than
    overwriting them.

    Requires seed-mcp to be installed (pip install seed-mcp or
    pip install 'seed-cli[mcp]').
    """
    _check_mcp_installed()
    console.print()

    if target in ("all", "claude-desktop"):
        _install_claude_desktop(dry_run)

    if target in ("all", "claude-code"):
        _install_claude_code_settings(dry_run)
        _install_skill_file(dry_run)

    if not dry_run:
        console.print(
            "\n  [success]Done![/success]  Restart Claude Desktop / Claude Code to pick up the changes.\n"
        )


@app.command("uninstall")
def uninstall(
    target: str = typer.Option("all", "--target", "-t", help="all | claude-desktop | claude-code"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Remove Seed MCP config from Claude Desktop and/or Claude Code."""
    if not yes:
        typer.confirm("Remove Seed from Claude clients?", abort=True)

    if target in ("all", "claude-desktop"):
        _remove_from_config(_claude_desktop_config(), "mcpServers", "seed")

    if target in ("all", "claude-code"):
        _remove_from_config(_claude_code_settings(), "mcpServers", "seed")
        _remove_skill_file()

    ok("Seed removed. Restart your Claude clients.")


@app.command("check")
def check() -> None:
    """Show the current install status of the Seed skill."""
    console.print()

    _show_config_status("Claude Desktop", _claude_desktop_config())
    _show_config_status("Claude Code settings", _claude_code_settings())

    skill_path = _claude_code_skills_dir() / "seed" / "SKILL.md"
    refs_path = _claude_code_skills_dir() / "seed" / "references"
    installed = skill_path.exists()
    refs_ok = refs_path.is_dir()
    mark = "[success]✔[/success]" if (installed and refs_ok) else "[error]✖[/error]"
    if installed and refs_ok:
        state = "installed"
    elif installed:
        state = "installed but references/ MISSING — re-run 'seed skill install'"
    else:
        state = "not installed"
    console.print(f"  {mark}  Claude Code skill   [dim]{skill_path}[/dim]  {state}")

    try:
        import seed_mcp  # noqa: F401
        console.print("  [success]✔[/success]  seed-mcp package  installed")
    except ImportError:
        console.print("  [error]✖[/error]  seed-mcp package  not installed")
        console.print("       Install: [cyan]pip install seed-mcp[/cyan]")

    console.print()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_mcp_installed() -> None:
    try:
        import seed_mcp  # noqa: F401
    except ImportError as exc:
        err("seed-mcp is not installed.")
        info("Install it with:  pip install seed-mcp")
        info("Or:               pip install 'seed-cli[mcp]'")
        raise typer.Exit(1) from exc


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        warn(f"Could not parse {path} — will create a fresh config.")
        return {}


def _write_json(path: Path, data: dict, dry_run: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    formatted = json.dumps(data, indent=2)
    if dry_run:
        console.print(f"\n  [dim]Would write to {path}:[/dim]")
        console.print(f"  [dim]{formatted[:300]}…[/dim]")
    else:
        path.write_text(formatted)


def _install_claude_desktop(dry_run: bool) -> None:
    path = _claude_desktop_config()
    data = _load_json(path)
    data.setdefault("mcpServers", {})

    if data["mcpServers"].get("seed") == _MCP_BLOCK:
        info(f"Claude Desktop  [dim]{path}[/dim]  already configured")
        return

    data["mcpServers"]["seed"] = _MCP_BLOCK
    _write_json(path, data, dry_run)
    verb = "Would add" if dry_run else "Added"
    ok(f"{verb} Seed MCP server to Claude Desktop  [dim]{path}[/dim]")


def _install_claude_code_settings(dry_run: bool) -> None:
    path = _claude_code_settings()
    data = _load_json(path)
    data.setdefault("mcpServers", {})

    if data["mcpServers"].get("seed") == _MCP_BLOCK:
        info(f"Claude Code settings  [dim]{path}[/dim]  already configured")
        return

    data["mcpServers"]["seed"] = _MCP_BLOCK
    _write_json(path, data, dry_run)
    verb = "Would add" if dry_run else "Added"
    ok(f"{verb} Seed MCP server to Claude Code settings  [dim]{path}[/dim]")


def _install_skill_file(dry_run: bool) -> None:
    skills_dir = _claude_code_skills_dir()
    # Claude Code skills are directories: <skills>/seed/SKILL.md plus references/.
    dest_dir = skills_dir / "seed"
    dest_skill = dest_dir / "SKILL.md"
    dest_refs = dest_dir / "references"

    try:
        src = _skill_source()  # .../skills/seed.md
    except FileNotFoundError as exc:
        warn(str(exc))
        return

    src_refs = src.parent / "references"

    if (
        dest_skill.exists()
        and dest_skill.read_text() == src.read_text()
        and (not src_refs.is_dir() or dest_refs.is_dir())
    ):
        info(f"Claude Code skill  [dim]{dest_dir}[/dim]  already up to date")
        return

    if dry_run:
        console.print(f"  [dim]Would copy {src} → {dest_skill}[/dim]")
        if src_refs.is_dir():
            console.print(f"  [dim]Would copy {src_refs}/ → {dest_refs}/[/dim]")
    else:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest_skill)
        if src_refs.is_dir():
            if dest_refs.exists() and not dest_refs.is_symlink():
                shutil.rmtree(dest_refs)
            elif dest_refs.is_symlink():
                dest_refs.unlink()
            shutil.copytree(src_refs, dest_refs)
    verb = "Would install" if dry_run else "Installed"
    ok(f"{verb} Claude Code skill  [dim]{dest_dir}[/dim]")


def _remove_from_config(path: Path, section: str, key: str) -> None:
    if not path.exists():
        return
    data = _load_json(path)
    if section in data and key in data[section]:
        del data[section][key]
        path.write_text(json.dumps(data, indent=2))
        ok(f"Removed '{key}' from {path}")
    else:
        info(f"'{key}' not found in {path} — skipping")


def _remove_skill_file() -> None:
    skills_dir = _claude_code_skills_dir()
    dest_dir = skills_dir / "seed"
    removed = False

    if dest_dir.is_symlink():
        dest_dir.unlink()
        ok(f"Removed skill symlink  {dest_dir}")
        removed = True
    elif dest_dir.exists():
        shutil.rmtree(dest_dir)
        ok(f"Removed skill directory  {dest_dir}")
        removed = True

    if not removed:
        info("Skill not found — skipping")


def _show_config_status(label: str, path: Path) -> None:
    data = _load_json(path)
    has_seed = bool(data.get("mcpServers", {}).get("seed"))
    mark = "[success]✔[/success]" if has_seed else "[error]✖[/error]"
    state = "configured" if has_seed else "not configured"
    console.print(f"  {mark}  {label:28s}  [dim]{path}[/dim]  {state}")
