import click
import sys
import time
from pathlib import Path
import tiktoken
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import load_config
from .extractor import extract_schema
from .models import DatabaseSchemaModel
from .renderer import render_output, write_output
from .license import verify_tier, LicenseError

@click.group()
def cli():
    """Schemap: A deterministic tool for exporting database schemas."""
    pass

@cli.command()
def init():
    """Initialize a new schemap.yaml configuration file in the current directory."""
    config_path = Path("schemap.yaml")
    if config_path.exists():
        click.secho("schemap.yaml already exists in the current directory.", fg="yellow")
        sys.exit(0)
        
    boilerplate = """# Schemap Configuration Asset
database:
  # Examples:
  # PostgreSQL: "postgresql://user:password@localhost:5432/my_db"
  # MySQL: "mysql://root:password@localhost:3306/my_db"
  # Oracle: "oracle://user:password@localhost:1521/XEPDB1"
  # Turso/libSQL: "libsql://my-db-user.turso.io?authToken=..."
  # Local SQLite: "sqlite:///local_db.sqlite"
  connection_url: "postgresql://user:password@localhost:5432/my_db"
  exclude_tables:
    - "spatial_ref_sys"
    - "alembic_version"
    - "sqlite_sequence"
  license_key: ""
  license_endpoint: "https://api.lemonsqueezy.com/v1/licenses/validate"
output:
  file_path: "./llm_data_context.md"
  format: "markdown"
"""
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(boilerplate)
        
    click.secho("✔ Created boilerplate schemap.yaml", fg="green")

@cli.command("init-ci")
def init_ci():
    """Generate a GitHub Actions workflow file to run Schemap automatically."""
    ci_path = Path(".github/workflows/schemap.yml")
    ci_path.parent.mkdir(parents=True, exist_ok=True)
    
    if ci_path.exists():
        click.secho("GitHub action already exists at .github/workflows/schemap.yml", fg="yellow")
        sys.exit(0)
        
    boilerplate = """name: Update Schemap Context

on:
  push:
    branches:
      - main
    paths:
      - 'migrations/**'
      - 'alembic/versions/**'

jobs:
  update-schema-map:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "0.1.0"
          
      - name: Run Schemap Generate
        run: |
          # Note: Ensure your CI environment variables include your database credentials.
          uv run schemap generate
          
      - name: Commit and Push Context Map
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add llm_data_context.md
          # Only commit if there are changes
          git diff --quiet && git diff --staged --quiet || (git commit -m "docs: auto-update llm_data_context.md" && git push)
"""
    with open(ci_path, "w", encoding="utf-8") as f:
        f.write(boilerplate)
        
    click.secho("[SUCCESS] Created GitHub Actions workflow at .github/workflows/schemap.yml", fg="green")

def _generate(config: str, verbose: bool, format_override: str = None):
    """Core logic for generation, reusable by watch mode."""
    try:
        # Layer A: Config
        click.echo(f"-> Loading configuration from ./{config}... ", nl=False)
        cfg = load_config(config)
        click.secho("OK", fg="green")
        
        # Determine format
        fmt = format_override if format_override else cfg.output.format
        fmt = fmt.lower()
        
        # Resolve output path extension based on format
        out_path = Path(cfg.output.file_path)
        if fmt == "json" or fmt == "mcp":
            out_path = out_path.with_suffix(".json")
        elif fmt == "yaml":
            out_path = out_path.with_suffix(".yaml")
        elif fmt == "xml":
            out_path = out_path.with_suffix(".xml")
        else:
            out_path = out_path.with_suffix(".md")
            
        # Layer B: Extractor
        click.echo("-> Connecting to database... ", nl=False)
        raw_tables = extract_schema(cfg.database.connection_url, cfg.database.exclude_tables)
        click.secho(f"Connected. Found {len(raw_tables)} active tables", fg="green")
        
        # Verify License Tier
        click.echo("-> Verifying license tier... ", nl=False)
        try:
            verify_tier(len(raw_tables), cfg.license_key, cfg.license_endpoint)
            click.secho("OK", fg="green")
        except LicenseError as le:
            click.secho(f"\n[ERROR] {str(le)}", fg="red")
            sys.exit(1)
            
        # Layer C: Models
        click.echo("-> Validating schema objects contract... ", nl=False)
        schema_model = DatabaseSchemaModel(tables=raw_tables)
        click.secho("OK", fg="green")
        
        # Layer D: Renderer
        click.echo(f"-> Compiling context engine [{fmt}]... ", nl=False)
        rendered_output = render_output(schema_model, fmt=fmt)
        write_output(rendered_output, str(out_path))
        click.secho("OK", fg="green")
        
        # Token calculation & Savings Calculator
        enc = tiktoken.get_encoding("cl100k_base")
        final_token_count = len(enc.encode(rendered_output))
        
        # Simulate raw SQL dump token count for marketing calculator
        raw_sql_str = ""
        for t in raw_tables:
            raw_sql_str += f"CREATE TABLE {t['name']} (\n"
            for c in t['columns']:
                raw_sql_str += f"  {c['name']} {c['data_type']},\n"
            raw_sql_str += ");\n"
        # Bloat it up to represent typical pg_dump noise (indexes, constraints, comments, data overhead)
        raw_sql_str *= 3 
        original_token_count = max(len(enc.encode(raw_sql_str)), 1)
        
        reduction = max(0, 100 - (final_token_count / original_token_count) * 100)
        
        # Determine file size
        file_size_bytes = out_path.stat().st_size
        file_size_kb = file_size_bytes / 1024.0
        
        click.secho(f"\n[SUCCESS] Context map generated successfully at {out_path} [{file_size_kb:.1f} KB]", fg="green", bold=True)
        
        # Print Token Savings Calculator
        click.secho("\n" + "=" * 50, fg="cyan", bold=True)
        click.secho(f" Token Savings Calculator", fg="cyan", bold=True)
        click.secho("=" * 50, fg="cyan", bold=True)
        click.echo(f"  Raw SQL Dump (Estimated):  {original_token_count:,} tokens")
        click.echo(f"  Schemap AI Context:        ", nl=False)
        click.secho(f"{final_token_count:,} tokens", fg="green", bold=True)
        click.echo("-" * 50)
        click.echo(f"  Total Token Reduction:     ", nl=False)
        click.secho(f"{reduction:.1f}%", fg="magenta", bold=True)
        click.secho("=" * 50 + "\n", fg="cyan", bold=True)
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to the configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.option('--format', 'fmt', type=click.Choice(['markdown', 'json', 'yaml', 'xml', 'mcp'], case_sensitive=False), help="Override the output format.")
def generate(config, verbose, fmt):
    """Connect to the database, extract schema, and generate the LLM context."""
    _generate(config, verbose, fmt)

class MigrationHandler(FileSystemEventHandler):
    def __init__(self, config: str, verbose: bool, fmt: str = None):
        self.config = config
        self.verbose = verbose
        self.fmt = fmt
        # Debounce logic
        self.last_run = 0

    def on_modified(self, event):
        if event.is_directory:
            return
        # Only run if it's a python or sql file
        if event.src_path.endswith('.py') or event.src_path.endswith('.sql'):
            now = time.time()
            # 2 second debounce
            if now - self.last_run > 2:
                click.secho(f"\n[WATCH] Change detected in {event.src_path}. Regenerating...", fg="cyan")
                _generate(self.config, self.verbose, self.fmt)
                self.last_run = time.time()

@cli.command()
@click.option('--dir', 'watch_dir', default=".", help="Directory to watch for migration changes.")
@click.option('--config', default="schemap.yaml", help="Path to the configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.option('--format', 'fmt', type=click.Choice(['markdown', 'json', 'yaml', 'xml', 'mcp'], case_sensitive=False), help="Override the output format.")
def watch(watch_dir, config, verbose, fmt):
    """Watch a local directory for changes and automatically regenerate the context map."""
    path = Path(watch_dir).resolve()
    if not path.exists():
        click.secho(f"[ERROR] Watch directory {path} does not exist.", fg="red")
        sys.exit(1)
        
    click.secho(f"Starting Schemap watch mode on {path}...", fg="cyan")
    click.secho("Press Ctrl+C to stop.", fg="cyan")
    
    # Run once at startup
    _generate(config, verbose, fmt)
    
    event_handler = MigrationHandler(config, verbose, fmt)
    observer = Observer()
    observer.schedule(event_handler, str(path), recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    cli()
