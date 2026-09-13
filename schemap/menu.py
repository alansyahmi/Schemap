"""
Schemap Interactive TUI Menu.

Provides an intuitive arrow-key driven interactive menu when users type `schemap`
without any subcommands, powered by questionary and prompt_toolkit.
"""

import sys
from typing import Optional
import click
import questionary
from questionary import Choice, Style

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from . import __version__ as CURRENT_VERSION

# Premium styling matching Schemap cyan/green palette
SCHEMAP_MENU_STYLE = Style([
    ("qmark", "fg:#00d7ff bold"),           # Cyan ? symbol
    ("question", "bold"),                   # Question text
    ("answer", "fg:#00d7ff bold"),          # Selected answer
    ("pointer", "fg:#00d7ff bold"),         # ▸ pointer
    ("highlighted", "fg:#00d7ff bold"),     # Active selection
    ("selected", "fg:#00d7ff"),             # Selected
    ("separator", "fg:#6c757d"),            # Dim separators
    ("instruction", "fg:#888888 italic"),   # Navigation instructions
])


def print_banner(db_info: Optional[str] = None):
    """Print the stylized Schemap header banner before opening the menu."""
    banner_title = f"🗺️  SCHEMAP — AI Database Context & Safety Engine (v{CURRENT_VERSION})"
    border = "═" * 75
    click.secho(f"╔{border}╗", fg="cyan", bold=True)
    click.secho(f"║ {banner_title:<73} ║", fg="cyan", bold=True)
    click.secho(f"╚{border}╝", fg="cyan", bold=True)

    if db_info:
        click.echo(
            click.style(" Active Database: ", dim=True) +
            click.style(db_info, fg="green", bold=True)
        )
    click.echo()


def run_interactive_menu() -> Optional[str]:
    """
    Run the full interactive arrow-key selection menu using questionary.
    Returns the selected subcommand string or None if cancelled.
    """
    # Detect active db from local schemap.yaml if present
    db_info = None
    try:
        from .config import load_config
        cfg = load_config("schemap.yaml")
        if cfg and cfg.database and cfg.database.connection_url:
            raw_url = cfg.database.connection_url
            if "@" in raw_url:
                prefix = raw_url.split("@")[0].split("://")[0]
                host = raw_url.split("@")[1]
                db_info = f"{prefix}://***@{host}"
            else:
                db_info = raw_url
    except Exception:
        pass

    print_banner(db_info=db_info)

    choices = [
        Choice(
            title="sync          — Regenerate AI Context & Guardrails (AGENTS.md, CLAUDE.md)",
            value="sync",
        ),
        Choice(
            title="quickstart    — Interactive Setup & Database Auto-Detect",
            value="quickstart",
        ),
        Choice(
            title="doctor        — Run Schema Health Check & AI Readiness Score",
            value="doctor",
        ),
        Choice(
            title="mcp           — Start Model Context Protocol (MCP) Server for Cursor & Claude",
            value="mcp",
        ),
        Choice(
            title="join          — Solve Shortest Multi-hop SQL JOIN Path",
            value="join",
        ),
        Choice(
            title="benchmark     — Measure Context Window & Dollar Savings",
            value="benchmark",
        ),
        Choice(
            title="hook install  — Install Git Pre-Commit Auto-Sync Hook",
            value="hook install",
        ),
        questionary.Separator(),
        Choice(
            title="exit          — Exit",
            value="exit",
        ),
    ]

    try:
        selected = questionary.select(
            "Select a command to run:",
            choices=choices,
            style=SCHEMAP_MENU_STYLE,
            instruction="(Use ↑/↓ arrows, Enter to confirm, Ctrl+C to exit)",
            use_indicator=True,
            use_shortcuts=True,
        ).ask()

        if selected is None or selected == "exit":
            return None

        return selected
    except (KeyboardInterrupt, Exception):
        return None
