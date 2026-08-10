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
from .license import (
    verify_tier,
    verify_license_online,
    resolve_license_key,
    resolve_license_endpoint,
    save_credentials,
    load_credentials,
    clear_credentials,
    CREDENTIALS_FILE,
    DEFAULT_LICENSE_ENDPOINT,
    FREE_TABLE_LIMIT,
    LicenseError
)
from .enrichment import apply_heuristics, apply_llm, apply_description_overrides
from .linter import calculate_score
from .diff import save_current_state, load_previous_state, calculate_diff
from .export import generate_langchain, generate_llamaindex, generate_mcp_tools
from .context import generate_database_context
from .agents import write_agent_files
from .doctor import get_doctor_report
from .benchmark import calculate_benchmark

@click.group()
def cli():
    """Schemap: AI Database Context Compiler — The fastest way to make your database AI-ready."""
    pass

@cli.command()
@click.option('--full', is_flag=True, help="Generate full boilerplate with domain mappings and schema description overrides.")
def init(full):
    """Initialize a new schemap.yaml configuration file in the current directory."""
    config_path = Path("schemap.yaml")
    if config_path.exists():
        click.secho("schemap.yaml already exists in the current directory.", fg="yellow")
        sys.exit(0)
        
    if full:
        boilerplate = """# Schemap Full Configuration Asset
database:
  connection_url: "postgresql://user:password@localhost:5432/my_db"
  exclude_tables:
    - "spatial_ref_sys"
    - "alembic_version"
output:
  file_path: "./database_context.md"
  format: "markdown"
domain:
  name: "ecommerce"
  mappings:
    inv: "Invoice"
    cust: "Customer"
  ignore_abbreviations:
    - "slug"
    - "pos"
schema_descriptions:
  users:
    description: "Custom table override details"
    columns:
      pos:
        description: "Position index of the element"
license_key: ""
license_endpoint: "https://api.schemap.com/v1/licenses/verify"
"""
    else:
        boilerplate = """# Schemap Configuration
database:
  connection_url: "sqlite:///test.db"

output:
  file_path: "./database_context.md"

domain:
  mappings: {}
"""

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(boilerplate)
        
    click.secho("✔ Created schemap.yaml", fg="green")

def _process_schema(cfg, enrich: bool):
    click.echo("-> Connecting to database... ", nl=False)
    raw_tables = extract_schema(cfg.database.connection_url, cfg.database.exclude_tables)
    click.secho(f"Connected. Found {len(raw_tables)} active tables", fg="green")

    click.echo("-> Verifying license tier... ", nl=False)
    try:
        active_key, _ = resolve_license_key(config_key=cfg.license_key)
        verify_tier(len(raw_tables), active_key, resolve_license_endpoint(cfg.license_endpoint))
        click.secho("OK", fg="green")
    except LicenseError as le:
        click.secho(f"\n[ERROR] {str(le)}", fg="red")
        sys.exit(1)
        
    schema_model = DatabaseSchemaModel(tables=raw_tables)
    schema_model, unresolved = apply_heuristics(schema_model, cfg.domain.mappings, cfg.domain.ignore_abbreviations)
    schema_model = apply_description_overrides(schema_model, cfg.schema_descriptions)

    if enrich:
        if cfg.llm.api_key:
            click.echo("-> Calling Beta LLM Enrichment Layer... ", nl=False)
            schema_model = apply_llm(schema_model, cfg.llm.api_key, cfg.llm.model)
            click.secho("OK", fg="green")
        else:
            click.secho("\n[WARNING] --enrich flag passed (Beta Feature) but no llm.api_key found in config. Using deterministic heuristics.", fg="yellow")

    if unresolved:
        click.secho("\n[WARNING] Unresolved abbreviations detected. Add these to your domain mappings:", fg="yellow")
        for u in unresolved[:5]:
            click.echo(f"  - {u}")
        if len(unresolved) > 5:
            click.echo(f"  ... and {len(unresolved) - 5} more.")
            
    return schema_model, raw_tables, unresolved

def _display_token_savings(rendered_output: str, raw_tables: list, out_path: Path):
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
    
    file_size_kb = out_path.stat().st_size / 1024.0 if out_path.exists() else 0.0
    
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

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--json', 'json_output', is_flag=True, help="Output health report in machine-readable JSON.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def doctor(config, json_output, verbose):
    """Run Schemap AI Database Health Check & Onboarding Diagnostic."""
    try:
        cfg = load_config(config)
        schema_model, raw_tables, unresolved = _process_schema(cfg, enrich=False)

        report = get_doctor_report(schema_model, raw_tables, unresolved)

        if json_output:
            import json
            click.echo(json.dumps(report, indent=2))
            return
            
        click.secho("\n" + "=" * 50, fg="cyan", bold=True)
        click.secho(" Schemap AI Database Health Check", fg="cyan", bold=True)
        click.secho("=" * 50, fg="cyan", bold=True)
        click.echo(f"  Connection:            Connected ({report['tables_count']} tables)")
        click.echo(f"  Relationships Analyzed: {report['relationships_count']}")
        click.echo("-" * 50)
        click.echo("  AI Readiness Score:")
        color = "green" if report['ai_readiness_score'] >= 80 else "yellow" if report['ai_readiness_score'] >= 50 else "red"
        click.secho(f"  {report['progress_bar']}", fg=color, bold=True)

        if report['issues']:
            click.echo("\n  Top Issues Identified:")
            for issue in report['issues'][:5]:
                click.secho(f"  - {issue}", fg="yellow")
                
        click.secho("-" * 50, fg="cyan")
        click.secho(f" Recommendation: {report['recommendation']}", fg="green", bold=True)
        click.secho("=" * 50 + "\n", fg="cyan", bold=True)
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--json', 'json_output', is_flag=True, help="Output benchmark data in JSON format.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def benchmark(config, json_output, verbose):
    """Run Database Context Benchmark (tables, raw vs schemap tokens, compression, relationships, AI score, latency)."""
    try:
        cfg = load_config(config)
        schema_model, raw_tables, unresolved = _process_schema(cfg, enrich=False)
        
        bench_data = calculate_benchmark(schema_model, raw_tables, unresolved)
        
        if json_output:
            import json
            click.echo(json.dumps(bench_data, indent=2))
            return
            
        click.secho("\n" + "=" * 50, fg="magenta", bold=True)
        click.secho(" Database Context Benchmark", fg="magenta", bold=True)
        click.secho("=" * 50, fg="magenta", bold=True)
        click.echo(f"  Tables:               {bench_data['tables_count']}")
        click.echo(f"  Raw Schema:           {bench_data['raw_sql_tokens']:,} tokens")
        click.echo(f"  Schemap Context:      ", nl=False)
        click.secho(f"{bench_data['schemap_tokens']:,} tokens", fg="green", bold=True)
        click.echo(f"  Compression:          ", nl=False)
        click.secho(f"{bench_data['compression_percentage']}", fg="magenta", bold=True)
        click.echo("-" * 50)
        click.echo(f"  Relationships Mapped: {bench_data['relationships_mapped']}")
        click.echo(f"  AI Readiness Score:   {bench_data['ai_readiness_score']}/100")
        click.echo(f"  Generation Latency:   {bench_data['generation_latency_ms']}")
        click.secho("=" * 50 + "\n", fg="magenta", bold=True)
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--json', 'json_output', is_flag=True, help="Output metadata in JSON format.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def inspect(config, json_output, verbose):
    """Extract database metadata and display a clean structural summary."""
    try:
        cfg = load_config(config)
        schema_model, raw_tables, _ = _process_schema(cfg, enrich=False)
        
        total_cols = sum(len(t['columns']) for t in raw_tables)
        total_fks = sum(len(t.get('foreign_keys', [])) for t in raw_tables)
        total_indexes = sum(len(t.get('indexes', [])) for t in raw_tables)
        
        if json_output:
            import json
            payload = {
                "tables_count": len(raw_tables),
                "columns_count": total_cols,
                "foreign_keys_count": total_fks,
                "indexes_count": total_indexes,
                "tables": [t['name'] for t in raw_tables]
            }
            click.echo(json.dumps(payload, indent=2))
            return
            
        click.secho("\n" + "=" * 50, fg="cyan", bold=True)
        click.secho(" Database Inspection Intelligence", fg="cyan", bold=True)
        click.secho("=" * 50, fg="cyan", bold=True)
        click.echo(f"  Tables Extracted:          {len(raw_tables)}")
        click.echo(f"  Total Columns:             {total_cols}")
        click.echo(f"  Foreign Key Constraints:   {total_fks}")
        click.echo(f"  Indexes Discovered:        {total_indexes}")
        click.secho("-" * 50, fg="cyan")
        click.echo("  Table Breakdown:")
        for t in raw_tables:
            fks = len(t.get('foreign_keys', []))
            click.echo(f"   - {t['name']} ({len(t['columns'])} cols, {fks} FKs)")
        click.secho("=" * 50 + "\n", fg="cyan", bold=True)
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to the configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.option('--format', 'fmt', type=click.Choice(['markdown', 'json', 'yaml', 'xml', 'mcp', 'ai'], case_sensitive=False), help="Override the output format.")
@click.option('--enrich', is_flag=True, help="[BETA] Apply optional LLM enrichment for table descriptions.")
@click.option('--track/--no-track', default=True, help="Track schema state for diff intelligence.")
def context(config, verbose, fmt, enrich, track):
    """Generate AI-optimized database context (database_context.md)."""
    try:
        cfg = load_config(config)
        schema_model, raw_tables, _ = _process_schema(cfg, enrich)
        
        if track:
            save_current_state(schema_model)
            
        target_fmt = fmt if fmt else cfg.output.format
        out_path = Path("database_context.md") if target_fmt == "markdown" else Path(cfg.output.file_path)
        
        click.echo(f"-> Compiling AI context engine [{target_fmt}]... ", nl=False)
        if target_fmt == "markdown":
            rendered_output = generate_database_context(schema_model)
        else:
            rendered_output = render_output(schema_model, fmt=target_fmt)
            
        write_output(rendered_output, str(out_path))
        click.secho("OK", fg="green")
        
        _display_token_savings(rendered_output, raw_tables, out_path)
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--dir', 'target_dir', default=".", help="Target directory for agent files.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def agents(config, target_dir, verbose):
    """Generate CLAUDE.md and AGENTS.md for AI coding agents."""
    try:
        cfg = load_config(config)
        schema_model, _, _ = _process_schema(cfg, enrich=False)
        
        click.echo("-> Compiling AI agent context rules... ", nl=False)
        files = write_agent_files(schema_model, target_dir)
        click.secho("OK", fg="green")
        
        click.secho("\n[SUCCESS] AI Agent Context files generated successfully:", fg="green", bold=True)
        for fname, fpath in files.items():
            click.echo(f"  [OK] {fname} -> {fpath}")
        click.echo("")
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def score(config, verbose):
    """Calculate AI Readiness Score for the database schema."""
    try:
        cfg = load_config(config)
        schema_model, _, unresolved = _process_schema(cfg, enrich=False)
        
        ai_score, issues = calculate_score(schema_model, unresolved)
        
        click.secho("\n" + "=" * 50, fg="magenta", bold=True)
        click.secho(f" AI Readiness Score", fg="magenta", bold=True)
        click.secho("=" * 50, fg="magenta", bold=True)
        
        color = "green" if ai_score >= 80 else "yellow" if ai_score >= 50 else "red"
        click.echo(f"  Score: ", nl=False)
        click.secho(f"{ai_score}/100", fg=color, bold=True)
        
        if issues:
            click.echo("\n  Issues Found:")
            for issue in issues:
                click.secho(f"  - {issue}", fg="yellow")
        else:
            click.secho("\n  Perfect score! Your database schema is 100% AI-ready.", fg="green")
            
        click.secho("=" * 50 + "\n", fg="magenta", bold=True)
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def diff(config, verbose):
    """Compare current database schema to the last tracked state."""
    try:
        cfg = load_config(config)
        old_schema = load_previous_state()
        if not old_schema:
            click.secho("[INFO] No previous schema state found. Run `schemap context` first to track state.", fg="yellow")
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

@cli.command(hidden=True)
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.option('--format', 'fmt', type=click.Choice(['markdown', 'json', 'yaml', 'xml', 'mcp', 'ai'], case_sensitive=False), help="Override format.")
@click.option('--enrich', is_flag=True, help="[BETA] Apply optional LLM enrichment.")
@click.option('--track/--no-track', default=True, help="Track schema state.")
@click.pass_context
def generate(ctx, config, verbose, fmt, enrich, track):
    """Legacy alias for `schemap context`."""
    ctx.invoke(context, config=config, verbose=verbose, fmt=fmt, enrich=enrich, track=track)

@cli.command()
@click.option('--framework', type=click.Choice(['langchain', 'llamaindex', 'mcp-tools', 'json'], case_sensitive=False), required=True, help="Target agent framework.")
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def export(framework, config, verbose):
    """Export schema as code or JSON for Agent Frameworks."""
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
                context(self.config, self.verbose, self.fmt, self.enrich, self.track)
                self.last_run = time.time()

@cli.command()
@click.option('--dir', 'watch_dir', default=".", help="Directory to watch for migration changes.")
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.option('--format', 'fmt', type=click.Choice(['markdown', 'json', 'yaml', 'xml', 'mcp', 'ai'], case_sensitive=False), help="Override format.")
@click.option('--enrich', is_flag=True, help="[BETA] Apply optional LLM enrichment.")
@click.option('--track/--no-track', default=True, help="Track schema state.")
def watch(watch_dir, config, verbose, fmt, enrich, track):
    """Watch local directory for changes and automatically regenerate context map."""
    path = Path(watch_dir).resolve()
    if not path.exists():
        click.secho(f"[ERROR] Watch directory {path} does not exist.", fg="red")
        sys.exit(1)
        
    click.secho(f"Starting Schemap watch mode on {path}...", fg="cyan")
    click.secho("Press Ctrl+C to stop.", fg="cyan")
    
    context(config, verbose, fmt, enrich, track)
    
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

@cli.command()
@click.argument('key')
@click.option('--endpoint', default=None, help="Custom license verification endpoint.")
def activate(key, endpoint):
    """Activate a Schemap Pro license key and save credentials globally."""
    endpoint_to_use = endpoint or DEFAULT_LICENSE_ENDPOINT
    click.echo(f"-> Verifying license key '{key[:12]}...' with {endpoint_to_use}... ", nl=False)

    res = verify_license_online(key, endpoint_to_use)
    if res.get("activated"):
        saved_path = save_credentials(key, endpoint)
        click.secho("OK", fg="green")
        click.secho(f"\n[SUCCESS] License activated successfully! Credentials saved to {saved_path}", fg="green", bold=True)
    else:
        err = res.get("error", "Invalid or expired license key.")
        click.secho("FAILED", fg="red")
        click.secho(f"\n[ERROR] License activation failed: {err}", fg="red")
        sys.exit(1)

@cli.command(name="status")
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--verify', is_flag=True, help="Verify the active key against the license service.")
def license_status(config, verify):
    """Display configured license state; optionally verify it online."""
    config_key = None
    try:
        cfg = load_config(config)
        config_key = cfg.license_key
    except Exception:
        pass

    active_key, source = resolve_license_key(config_key=config_key)

    click.secho("\n" + "=" * 50, fg="cyan", bold=True)
    click.secho(" Schemap License Status", fg="cyan", bold=True)
    click.secho("=" * 50, fg="cyan", bold=True)

    if active_key:
        masked_key = active_key[:8] + "..." + active_key[-4:] if len(active_key) > 12 else active_key
        click.echo("  Tier:             ", nl=False)
        click.secho("Pro (configured)", fg="green", bold=True)
        click.echo(f"  Active Key:       {masked_key}")
        click.echo(f"  Key Source:       {source}")

        from .license import _read_cache
        last_verified = _read_cache(active_key)
        if verify:
            endpoint = resolve_license_endpoint(config_endpoint=cfg.license_endpoint if 'cfg' in locals() else None)
            result = verify_license_online(active_key, endpoint)
            if result.get("activated"):
                click.secho("  Verification:     Active", fg="green")
                if result.get("plan"):
                    click.echo(f"  Plan:             {result['plan']}")
                if result.get("expires_at"):
                    click.echo(f"  Expires:          {result['expires_at']}")
            else:
                click.secho("  Verification:     Failed", fg="red")
                click.echo(f"  Verification error: {result.get('error', 'Invalid or expired license.')}")
        elif last_verified:
            age_days = (time.time() - last_verified) / 86400.0
            click.echo(f"  Cache Status:     Valid (verified {age_days:.1f} days ago)")
        else:
            click.echo("  Verification:     Not checked (use --verify)")
    else:
        click.echo("  Tier:             ", nl=False)
        click.secho("Free Tier", fg="yellow", bold=True)
        click.echo(f"  Table Limit:      {FREE_TABLE_LIMIT} tables")
        click.echo(f"  CI Automation:    Blocked on Free Tier")
        click.echo(f"  Key Source:       None")

    click.echo(f"  Credentials File: {CREDENTIALS_FILE}")
    click.secho("=" * 50 + "\n", fg="cyan", bold=True)

@cli.command()
def logout():
    """Clear global credentials and local license validation cache."""
    clear_credentials()
    click.secho("\n[SUCCESS] Successfully logged out. Cleared global credentials and license cache.", fg="green")

if __name__ == "__main__":
    cli()
