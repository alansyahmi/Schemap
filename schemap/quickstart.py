import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import click
import yaml

from .config import load_config
from .extractor import extract_schema
from .models import DatabaseSchemaModel
from .context import generate_database_context
from .renderer import write_output
from .agents import write_agent_files
from .doctor import get_doctor_report
from .enrichment import apply_heuristics, apply_description_overrides, apply_fk_overrides

def detect_local_databases() -> List[Tuple[str, str]]:
    """
    Detect local SQLite files and environment database connection strings.
    Returns a list of tuples: (label/source, connection_url)
    """
    results = []
    env_keys = ["SCHEMAP_DATABASE_URL", "DATABASE_URL", "POSTGRES_URL", "MYSQL_URL", "SQLITE_URL"]
    for key in env_keys:
        val = os.environ.get(key)
        if val:
            results.append((f"Env ({key})", val))

    cwd = Path.cwd()
    patterns = ["*.db", "*.sqlite", "*.sqlite3"]
    for p in patterns:
        for f in cwd.glob(p):
            if f.is_file():
                results.append((f"Local File ({f.name})", f"sqlite:///{f.name}"))

    return results

def run_quickstart(
    interactive: bool = True,
    target_db: str | None = None,
    output_path: str | None = None,
    targets: str | None = None,
    skills: bool = True
) -> Dict[str, Any]:
    """
    Run full onboarding quickstart flow: detect DB, write config, compile context, write agent files, install skills, and display readiness card.
    """
    click.secho("\n" + "=" * 55, fg="cyan", bold=True)
    click.secho(" 🚀 Schemap Quickstart & AI Readiness Setup", fg="cyan", bold=True)
    click.secho("=" * 55 + "\n", fg="cyan", bold=True)

    detected = detect_local_databases()
    selected_url = target_db

    if not selected_url:
        if interactive and sys.stdin.isatty():
            click.echo("🔍 Auto-detecting local database sources...")
            if detected:
                click.echo("  Discovered databases:")
                for i, (label, url) in enumerate(detected, 1):
                    click.echo(f"   [{i}] {label} -> {url}")
                click.echo(f"   [{len(detected)+1}] Enter custom connection URL")

                choice = click.prompt(
                    "Select a database source",
                    type=int,
                    default=1
                )
                if 1 <= choice <= len(detected):
                    selected_url = detected[choice - 1][1]
                else:
                    selected_url = click.prompt("Enter database connection URL", type=str)
            else:
                selected_url = click.prompt(
                    "No local database detected. Enter database connection URL",
                    type=str,
                    default="sqlite:///demo_ecommerce.db"
                )
        else:
            selected_url = detected[0][1] if detected else "sqlite:///demo_ecommerce.db"

    if not output_path:
        if interactive and sys.stdin.isatty():
            output_path = click.prompt(
                "Where should schemap write database context?",
                type=str,
                default="./schemap_database_context.md"
            )
        else:
            output_path = "./schemap_database_context.md"

    if not targets:
        if interactive and sys.stdin.isatty():
            targets = click.prompt(
                "Which AI agent targets to support? (codex, claude, cursor, or all)",
                type=str,
                default="all"
            )
        else:
            targets = "all"

    # 1. Write schemap.yaml
    config_data = {
        "database": {
            "connection_url": selected_url
        },
        "output": {
            "file_path": output_path,
            "format": "markdown"
        },
        "domain": {
            "mappings": {
                "cust": "Customer",
                "tx": "Transaction",
                "inv": "Invoice",
                "acct": "Account",
                "amt": "Amount"
            }
        }
    }

    config_path = Path("schemap.yaml")
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, sort_keys=False)
    click.secho("✔ Created schemap.yaml configuration file", fg="green")

    # 2. Extract & Doctor
    cfg = load_config("schemap.yaml")
    click.echo("-> Extracting schema and running doctor diagnostic... ", nl=False)
    raw_tables = extract_schema(cfg.database.connection_url, cfg.database.exclude_tables)
    schema_model = DatabaseSchemaModel(tables=raw_tables)
    schema_model, unresolved = apply_heuristics(schema_model, cfg.domain.mappings, cfg.domain.ignore_abbreviations)
    schema_model = apply_description_overrides(schema_model, cfg.schema_descriptions)
    schema_model = apply_fk_overrides(schema_model, cfg.foreign_key_overrides)
    click.secho("OK", fg="green")

    doc_report = get_doctor_report(schema_model, raw_tables, unresolved)

    # 3. Generate context
    click.echo(f"-> Generating database context map at {output_path}... ", nl=False)
    context_content = generate_database_context(schema_model)
    write_output(context_content, output_path)
    click.secho("OK", fg="green")

    # 4. Generate agent context files
    click.echo(f"-> Installing AI agent context files (targets: {targets})... ", nl=False)
    agent_files = write_agent_files(schema_model, targets=targets)
    click.secho("OK", fg="green")

    # 5. Install skills if requested
    skills_installed = []
    if skills:
        try:
            from .skills import install_agent_skills
            skills_installed = install_agent_skills(targets=targets)
        except Exception:
            pass

    # Display summary card
    click.secho("\n" + "=" * 55, fg="cyan", bold=True)
    click.secho(" 📊 AI Readiness Summary Card", fg="cyan", bold=True)
    click.secho("=" * 55, fg="cyan", bold=True)
    click.echo(f"  Database URL:          {selected_url}")
    click.echo(f"  Tables Mapped:         {doc_report['tables_count']}")
    click.echo(f"  Relationships Found:   {doc_report['relationships_count']}")
    click.echo("-" * 55)
    click.echo("  AI Readiness Score:")
    color = "green" if doc_report['ai_readiness_score'] >= 80 else "yellow" if doc_report['ai_readiness_score'] >= 50 else "red"
    click.secho(f"  {doc_report['progress_bar']}", fg=color, bold=True)
    click.echo("-" * 55)
    click.echo("  Generated Context Assets:")
    click.echo(f"   [Context] {output_path}")
    for fname, fpath in agent_files.items():
        click.echo(f"   [Agent]   {fname} -> {fpath}")
    for sk in skills_installed:
        click.echo(f"   [Skill]   {sk}")

    click.secho("-" * 55, fg="cyan")
    click.secho(" Recommended Next Commands:", fg="yellow", bold=True)
    click.echo("  1. schemap doctor                   # View detailed schema health check")
    click.echo("  2. schemap fix --interactive         # Automatically fix missing FKs & descriptions")
    click.echo("  3. schemap explain table orders     # Inspect table details directly")
    click.echo("  4. schemap join users orders        # Generate SQL join snippets")
    click.echo("  5. schemap watch                    # Auto-update context when schema changes")
    click.secho("=" * 55 + "\n", fg="cyan", bold=True)

    return {
        "status": "success",
        "database_url": selected_url,
        "output_path": output_path,
        "ai_readiness_score": doc_report['ai_readiness_score'],
        "agent_files": agent_files
    }
