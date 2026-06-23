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
from .enrichment import apply_heuristics, apply_llm
from .linter import calculate_score
from .diff import save_current_state, load_previous_state, calculate_diff
from .export import generate_langchain, generate_llamaindex, generate_mcp_tools

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
  connection_url: "postgresql://user:password@localhost:5432/my_db"
  exclude_tables:
    - "spatial_ref_sys"
    - "alembic_version"
  license_key: ""
  license_endpoint: "https://api.lemonsqueezy.com/v1/licenses/validate"
output:
  file_path: "./llm_data_context.md"
  format: "markdown"
domain:
  name: "ecommerce"
  mappings:
    inv: "Invoice"
    cust: "Customer"
llm:
  provider: "openai"
  model: "gpt-4o-mini"
  api_key: ""
"""
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(boilerplate)
        
    click.secho("✔ Created boilerplate schemap.yaml", fg="green")

def _process_schema(cfg, enrich: bool):
    click.echo("-> Connecting to database... ", nl=False)
    raw_tables = extract_schema(cfg.database.connection_url, cfg.database.exclude_tables)
    click.secho(f"Connected. Found {len(raw_tables)} active tables", fg="green")
    
    click.echo("-> Verifying license tier... ", nl=False)
    try:
        verify_tier(len(raw_tables), cfg.license_key, cfg.license_endpoint)
        click.secho("OK", fg="green")
    except LicenseError as le:
        click.secho(f"\n[ERROR] {str(le)}", fg="red")
        sys.exit(1)
        
    schema_model = DatabaseSchemaModel(tables=raw_tables)
    schema_model, unresolved = apply_heuristics(schema_model, cfg.domain.mappings)
    
    if enrich and cfg.llm.api_key:
        click.echo("-> Calling LLM Enrichment Layer... ", nl=False)
        schema_model = apply_llm(schema_model, cfg.llm.api_key, cfg.llm.model)
        click.secho("OK", fg="green")
    elif enrich:
        click.secho("\n[WARNING] --enrich flag passed but no llm.api_key found in config. Using heuristics only.", fg="yellow")

    if unresolved:
        click.secho("\n[WARNING] Unresolved abbreviations detected. Add these to your domain mappings:", fg="yellow")
        for u in unresolved[:5]:
            click.echo(f"  - {u}")
        if len(unresolved) > 5:
            click.echo(f"  ... and {len(unresolved) - 5} more.")
            
    return schema_model, raw_tables, unresolved

def _generate(config: str, verbose: bool, format_override: str = None, enrich: bool = False, track: bool = True):
    try:
        click.echo(f"-> Loading configuration from ./{config}... ", nl=False)
        cfg = load_config(config)
        click.secho("OK", fg="green")
        
        schema_model, raw_tables, unresolved = _process_schema(cfg, enrich)
        
        # Save state for diffing
        if track:
            save_current_state(schema_model)
        
        fmt = format_override if format_override else cfg.output.format
        fmt = fmt.lower()
        
        out_path = Path(cfg.output.file_path)
        if fmt == "json" or fmt == "mcp" or fmt == "mcp-tools":
            out_path = out_path.with_suffix(".json")
        elif fmt == "yaml":
            out_path = out_path.with_suffix(".yaml")
        elif fmt == "xml":
            out_path = out_path.with_suffix(".xml")
        elif fmt == "ai":
            out_path = out_path.with_suffix(".txt")
        else:
            out_path = out_path.with_suffix(".md")
            
        click.echo(f"-> Compiling context engine [{fmt}]... ", nl=False)
        rendered_output = render_output(schema_model, fmt=fmt)
        write_output(rendered_output, str(out_path))
        click.secho("OK", fg="green")
        
        enc = tiktoken.get_encoding("cl100k_base")
        final_token_count = len(enc.encode(rendered_output))
        
        raw_sql_str = ""
        for t in raw_tables:
            raw_sql_str += f"CREATE TABLE {t['name']} (\n"
            for c in t['columns']:
                raw_sql_str += f"  {c['name']} {c['data_type']},\n"
            raw_sql_str += ");\n"
        raw_sql_str *= 3 
        original_token_count = max(len(enc.encode(raw_sql_str)), 1)
        reduction = max(0, 100 - (final_token_count / original_token_count) * 100)
        
        file_size_kb = out_path.stat().st_size / 1024.0
        
        click.secho(f"\n[SUCCESS] Context map generated successfully at {out_path} [{file_size_kb:.1f} KB]", fg="green", bold=True)
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
@click.option('--format', 'fmt', type=click.Choice(['markdown', 'json', 'yaml', 'xml', 'mcp', 'ai'], case_sensitive=False), help="Override the output format.")
@click.option('--enrich', is_flag=True, help="Use OpenAI LLM to powerfully enrich table and column business definitions.")
@click.option('--track/--no-track', default=True, help="Track schema state for diff intelligence.")
def generate(config, verbose, fmt, enrich, track):
    """Connect to the database, extract schema, and generate the LLM context."""
    _generate(config, verbose, fmt, enrich, track)

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to the configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def diff(config, verbose):
    """Compare current database schema to the last known tracked state."""
    try:
        cfg = load_config(config)
        old_schema = load_previous_state()
        if not old_schema:
            click.secho("[INFO] No previous schema state found. Run `schemap generate` first to build the cache.", fg="yellow")
            return
            
        schema_model, _, _ = _process_schema(cfg, enrich=False)
        
        diffs = calculate_diff(old_schema, schema_model)
        
        click.secho("\n" + "=" * 50, fg="cyan", bold=True)
        click.secho(f" Schema Diff Intelligence", fg="cyan", bold=True)
        click.secho("=" * 50, fg="cyan", bold=True)
        
        if not diffs:
            click.secho("  No changes detected since last run.", fg="green")
        else:
            for d in diffs:
                if d.startswith("+"):
                    click.secho(f"  {d}", fg="green")
                elif d.startswith("-"):
                    click.secho(f"  {d}", fg="red")
                elif d.startswith("~"):
                    click.secho(f"  {d}", fg="yellow")
                    
        click.secho("=" * 50 + "\n", fg="cyan", bold=True)
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--framework', type=click.Choice(['langchain', 'llamaindex', 'mcp-tools', 'json'], case_sensitive=False), required=True, help="Target agent framework.")
@click.option('--config', default="schemap.yaml", help="Path to the configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def export(framework, config, verbose):
    """Export the schema as copy-pasteable, highly contextual Python code or JSON for Agent Frameworks."""
    try:
        cfg = load_config(config)
        schema_model, _, _ = _process_schema(cfg, enrich=False)
        
        click.echo(f"-> Generating {framework} export... ", nl=False)
        
        out_path = Path("schemap_tools")
        if framework == "langchain":
            content = generate_langchain(schema_model)
            out_path = out_path.with_suffix(".py")
        elif framework == "llamaindex":
            content = generate_llamaindex(schema_model)
            out_path = out_path.with_suffix(".py")
        elif framework == "mcp-tools":
            content = generate_mcp_tools(schema_model)
            out_path = out_path.with_suffix(".json")
        elif framework == "json":
            content = render_output(schema_model, fmt="json")
            out_path = out_path.with_suffix(".json")
            
        write_output(content, str(out_path))
        click.secho("OK", fg="green")
        
        click.secho(f"\n[SUCCESS] AI-ready {framework} context module exported to {out_path}", fg="green", bold=True)
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to the configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def score(config, verbose):
    """Analyze the database schema and calculate its AI-Readiness Score."""
    try:
        cfg = load_config(config)
        schema_model, _, unresolved = _process_schema(cfg, enrich=False)
        
        ai_score, issues = calculate_score(schema_model, unresolved)
        
        click.secho("\n" + "=" * 50, fg="magenta", bold=True)
        click.secho(f" Schema AI Quality Score", fg="magenta", bold=True)
        click.secho("=" * 50, fg="magenta", bold=True)
        
        color = "green" if ai_score >= 80 else "yellow" if ai_score >= 50 else "red"
        click.echo(f"  Score: ", nl=False)
        click.secho(f"{ai_score}/100", fg=color, bold=True)
        
        if issues:
            click.echo("\n  Issues Found:")
            for issue in issues:
                click.secho(f"  - {issue}", fg="yellow")
        else:
            click.secho("\n  Perfect score! Your schema is perfectly structured for LLM consumption.", fg="green")
            
        click.secho("=" * 50 + "\n", fg="magenta", bold=True)
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

class MigrationHandler(FileSystemEventHandler):
    def __init__(self, config: str, verbose: bool, fmt: str = None, enrich: bool = False, track: bool = True):
        self.config = config
        self.verbose = verbose
        self.fmt = fmt
        self.enrich = enrich
        self.track = track
        self.last_run = 0

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.py') or event.src_path.endswith('.sql'):
            now = time.time()
            if now - self.last_run > 2:
                click.secho(f"\n[WATCH] Change detected in {event.src_path}. Regenerating...", fg="cyan")
                _generate(self.config, self.verbose, self.fmt, self.enrich, self.track)
                self.last_run = time.time()

@cli.command()
@click.option('--dir', 'watch_dir', default=".", help="Directory to watch for migration changes.")
@click.option('--config', default="schemap.yaml", help="Path to the configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.option('--format', 'fmt', type=click.Choice(['markdown', 'json', 'yaml', 'xml', 'mcp', 'ai'], case_sensitive=False), help="Override the output format.")
@click.option('--enrich', is_flag=True, help="Use OpenAI LLM to powerfully enrich table and column business definitions.")
@click.option('--track/--no-track', default=True, help="Track schema state for diff intelligence.")
def watch(watch_dir, config, verbose, fmt, enrich, track):
    """Watch a local directory for changes and automatically regenerate the context map."""
    path = Path(watch_dir).resolve()
    if not path.exists():
        click.secho(f"[ERROR] Watch directory {path} does not exist.", fg="red")
        sys.exit(1)
        
    click.secho(f"Starting Schemap watch mode on {path}...", fg="cyan")
    click.secho("Press Ctrl+C to stop.", fg="cyan")
    
    _generate(config, verbose, fmt, enrich, track)
    
    event_handler = MigrationHandler(config, verbose, fmt, enrich, track)
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
