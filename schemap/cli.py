import os
import click
import sys
import time
from pathlib import Path
import tiktoken
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .config import load_config
from .extractor import extract_schema
from .models import DatabaseSchemaModel
from .renderer import render_output, write_output
from .license import (
    verify_tier,
    verify_license_online,
    deactivate_license_online,
    fetch_seats_status,
    create_customer_portal_session,
    get_or_create_device_id,
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
from .enrichment import apply_heuristics, apply_llm, apply_description_overrides, apply_fk_overrides
from .linter import calculate_score
from .diff import save_current_state, load_previous_state, calculate_diff, calculate_detailed_diff
from .export import generate_langchain, generate_llamaindex, generate_mcp_tools
from .context import generate_database_context
from .agents import write_agent_files
from .doctor import get_doctor_report
from .benchmark import calculate_benchmark
from .gate import evaluate_gate, generate_gate_markdown_report
from .fingerprint import calculate_schema_fingerprint, get_cached_fingerprint, save_fingerprint
from .quickstart import run_quickstart
from .fix import run_fix
from .skills import install_agent_skills
from .state import get_trial_status, start_trial, record_successful_run, mark_review_prompted
import webbrowser
import urllib.parse

@click.group()
@click.version_option("3.1.2", package_name="schemap-tool", message="Schemap %(version)s")
@click.option('--profile', default=None, help="Named profile to load from schemap.yaml.")
@click.option('--quiet', '-q', is_flag=True, help="Suppress informational messages.")
@click.option('--no-color', is_flag=True, help="Disable color output.")
@click.option('--output', 'output_fmt', default=None, help="Global default output format.")
@click.option('--output-file', default=None, help="Redirect output to a file.")
@click.pass_context
def cli(ctx, profile, quiet, no_color, output_fmt, output_file):
    """Schemap: AI Database Context Compiler - The fastest way to make your database AI-ready."""
    ctx.ensure_object(dict)
    ctx.obj['profile'] = profile
    ctx.obj['quiet'] = quiet
    ctx.obj['no_color'] = no_color
    ctx.obj['output_fmt'] = output_fmt
    ctx.obj['output_file'] = output_file
    if no_color:
        ctx.color = False


@cli.command()
@click.option('--full', is_flag=True, help="Generate full boilerplate with domain mappings and schema description overrides.")
@click.option('--interactive/--non-interactive', default=True, help="Run interactively or auto-pick defaults.")
@click.option('--db', default=None, help="Database connection URL.")
@click.option('--output-path', default=None, help="Context output file path.")
@click.option('--targets', default=None, help="Target agent targets e.g. codex,claude,cursor or all.")
def quickstart(full, interactive, db, output_path, targets):
    """Run interactive schemap quickstart onboarding flow."""
    run_quickstart(
        interactive=interactive,
        target_db=db,
        output_path=output_path,
        targets=targets
    )

@cli.command()
@click.option('--full', is_flag=True, help="Generate full boilerplate with domain mappings and schema description overrides.")
@click.option('--interactive/--non-interactive', default=True, help="Run interactively or write standard template.")
@click.pass_context
def init(ctx, full, interactive):
    """Initialize a new schemap.yaml configuration file in the current directory."""
    config_path = Path("schemap.yaml")
    if config_path.exists():
        click.secho("schemap.yaml already exists in the current directory.", fg="yellow")
        sys.exit(0)

    if interactive and not full and sys.stdin.isatty():
        run_quickstart(interactive=True)
        return
        
    if full:
        boilerplate = """# Schemap Full Configuration Asset
database:
  connection_url: "postgresql://user:password@localhost:5432/my_db"
  exclude_tables:
    - "spatial_ref_sys"
    - "alembic_version"
output:
  file_path: "./schemap_database_context.md"
  format: "markdown"
domain:
  name: "ecommerce"
  mappings:
    cust: "Customer"
    tx: "Transaction"
    inv: "Invoice"
    acct: "Account"
    amt: "Amount"
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
license_endpoint: "https://schemap-license-api.alansyahmi2004.workers.dev/v1/licenses/verify"
"""
    else:
        boilerplate = """# Schemap Configuration
database:
  connection_url: "sqlite:///test.db"

output:
  file_path: "./schemap_database_context.md"

domain:
  mappings:
    cust: "Customer"
    tx: "Transaction"
    inv: "Invoice"
    acct: "Account"
"""

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(boilerplate)
        
    click.secho("[OK] Created schemap.yaml", fg="green")

def _process_schema(cfg, enrich: bool, quiet: bool = False, required_feature: str | None = None):
    if not quiet:
        click.echo("-> Connecting to database... ", nl=False)
    db_schemas = getattr(cfg.database, "schemas", None)
    raw_tables = extract_schema(cfg.database.connection_url, cfg.database.exclude_tables, schemas=db_schemas)

    if not quiet:
        click.secho(f"Connected. Found {len(raw_tables)} active tables", fg="green")
        click.echo("-> Verifying license tier... ", nl=False)
    try:
        active_key, _ = resolve_license_key(config_key=cfg.license_key)
        verified_tier = verify_tier(
            tables_count=len(raw_tables),
            license_key=active_key,
            endpoint=resolve_license_endpoint(cfg.license_endpoint),
            required_feature=required_feature
        )
        if not quiet:
            tier_badge = f"OK [{verified_tier.upper()}]" if verified_tier != "free" else "OK [FREE]"
            click.secho(tier_badge, fg="green")
    except LicenseError as le:
        click.secho(f"\n[ERROR] {str(le)}", fg="red")
        sys.exit(1)

        
    schema_model = DatabaseSchemaModel(tables=raw_tables)
    schema_model, unresolved = apply_heuristics(schema_model, cfg.domain.mappings, cfg.domain.ignore_abbreviations)
    schema_model = apply_description_overrides(schema_model, cfg.schema_descriptions)
    schema_model = apply_fk_overrides(schema_model, cfg.foreign_key_overrides)
    if hasattr(cfg, "semantics") and cfg.semantics:
        from .semantics import apply_semantics
        schema_model = apply_semantics(schema_model, cfg.semantics)

    if enrich:
        if not active_key:
            click.secho("\n[ERROR] The --enrich LLM layer requires an active Schemap Pro license key.", fg="red")
            click.secho("Run `schemap activate <LICENSE_KEY>` or upgrade at https://schemap.dev/#pricing", fg="yellow")
            sys.exit(1)

        if cfg.llm.api_key:
            if not quiet:
                click.echo("-> Calling Beta LLM Enrichment Layer... ", nl=False)
            schema_model = apply_llm(schema_model, cfg.llm.api_key, cfg.llm.model)
            if not quiet:
                click.secho("OK", fg="green")
        else:
            if not quiet:
                click.secho("\n[WARNING] --enrich flag passed (Beta Feature) but no llm.api_key found in config. Using deterministic heuristics.", fg="yellow")

    if unresolved and not quiet:
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
    _maybe_prompt_feedback(cmd_name="context", tokens_saved=max(0, original_token_count - final_token_count))

def _maybe_prompt_feedback(cmd_name: str = "run", tokens_saved: int = 0):
    """
    Non-intrusive review/feedback prompt shown only on 2nd or 3rd successful value run.
    Bypassed in CI, quiet mode, or non-interactive terminals.
    """
    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    if is_ci or not sys.stdout.isatty():
        return

    should_prompt = record_successful_run(cmd_name)
    if not should_prompt:
        return

    trial_active, days_remaining, _ = get_trial_status()
    has_key, _ = resolve_license_key()

    savings_msg = f"Saved ~{tokens_saved:,} tokens on this run!" if tokens_saved > 0 else "Schemap run completed!"

    click.echo("")
    click.secho("+-------------------------------------------------------------+", fg="cyan")
    click.secho(f"|  {savings_msg:<57}  |", fg="cyan", bold=True)
    click.secho("|                                                             |", fg="cyan")
    click.secho("|  Enjoying Schemap? Help us build in public:                 |", fg="cyan")
    click.secho("|  [1] Star repository on GitHub (github.com/alansyahmi/schemap)|", fg="cyan")
    click.secho("|  [2] Share on X / Tweet your token savings                  |", fg="cyan")
    if not has_key:
        click.secho("|  [3] Unlock Pro ($1.99/mo launch special)                  |", fg="cyan")
    click.secho("|  [Enter to skip]                                            |", fg="cyan")
    click.secho("+-------------------------------------------------------------+", fg="cyan")
    
    try:
        choice = click.prompt("Your choice", default="", show_default=False).strip()
        mark_review_prompted()
        
        if choice == "1":
            click.secho("-> Opening GitHub repository... Thank you for the star!", fg="green")
            webbrowser.open("https://github.com/alansyahmi/schemap")
        elif choice == "2":
            tweet_text = f"Just shaved {tokens_saved:,} tokens from my database schema with @schemap_ai! Check it out:" if tokens_saved > 0 else "Loving @schemap_ai for AI database context generation! Check it out:"
            intent_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(tweet_text)}&url={urllib.parse.quote('https://schemap.dev')}"
            click.secho("-> Opening X/Twitter... Thank you for the shoutout!", fg="green")
            webbrowser.open(intent_url)
        elif choice == "3" and not has_key:
            checkout_url = "https://buy.stripe.com/dRm00jeG13kpfoA131dIA01"
            click.secho(f"-> Opening Pro checkout link ({checkout_url})...", fg="green")
            webbrowser.open(checkout_url)
    except Exception:
        mark_review_prompted()

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
@click.option('--cost', is_flag=True, help="Display monetary LLM cost savings estimates.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def benchmark(config, json_output, cost, verbose):
    """Run Database Context Benchmark (tables, raw vs schemap tokens, compression, monetary savings, AI score, latency)."""
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
        click.echo(f"  Tokens Saved/Prompt:  {bench_data.get('tokens_saved_per_prompt', 0):,}")
        click.echo(f"  Cost Saved/Prompt:    ", nl=False)
        click.secho(f"{bench_data.get('estimated_savings_per_prompt_usd', '$0.00')}", fg="green", bold=True)
        click.echo(f"  Est. Monthly/Dev:     ", nl=False)
        click.secho(f"{bench_data.get('estimated_monthly_savings_per_dev_usd', '$0.00')}", fg="green", bold=True)
        click.echo(f"  Relationships Mapped: {bench_data['relationships_mapped']}")
        click.echo(f"  AI Readiness Score:   {bench_data['ai_readiness_score']}/100")
        click.echo(f"  Generation Latency:   {bench_data['generation_latency_ms']}")
        click.secho("=" * 50 + "\n", fg="magenta", bold=True)
        
        _maybe_prompt_feedback(cmd_name="benchmark", tokens_saved=bench_data.get('tokens_saved_per_prompt', 0))
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
@click.option('--scope', default='all', help="Filter schema scope by role profile (all, analytics, backend, core).")
@click.option('--sanitize', is_flag=True, help="Automatically redact sensitive PII and credential columns for AI safety.")
@click.option('--enrich', is_flag=True, help="[BETA] Apply optional LLM enrichment for table descriptions.")
@click.option('--track/--no-track', default=True, help="Track schema state for diff intelligence.")
def context(config, verbose, fmt, scope, sanitize, enrich, track):
    """Generate AI-optimized database context (schemap_database_context.md)."""
    try:
        cfg = load_config(config)
        schema_model, raw_tables, _ = _process_schema(cfg, enrich, required_feature="sanitize" if sanitize else None)
        
        if track:
            save_current_state(schema_model)

            
        target_fmt = fmt if fmt else cfg.output.format
        out_path = Path(cfg.output.file_path) if cfg.output.file_path else Path("schemap_database_context.md")
        
        click.echo(f"-> Compiling AI context engine [{target_fmt}] (scope: {scope}, sanitize: {sanitize})... ", nl=False)
        if target_fmt == "markdown":
            rendered_output = generate_database_context(schema_model, scope=scope, sanitize=sanitize)
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
    # The license API may return either `activated` or `valid` for a
    # successful verification. Accept both so activation matches the normal
    # license verification path.
    if res.get("activated") or res.get("valid"):
        saved_path = save_credentials(key, endpoint)
        click.secho("OK", fg="green")
        click.secho(f"\n[SUCCESS] License activated successfully! Credentials saved to {saved_path}", fg="green", bold=True)
    else:
        err = res.get("error", "Invalid or expired license key.")
        click.secho("FAILED", fg="red")
        click.secho(f"\n[ERROR] License activation failed: {err}", fg="red")
        sys.exit(1)

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--json', 'json_output', is_flag=True, help="Output diff report in machine-readable JSON.")
@click.option('--fail-on-breaking', is_flag=True, help="Exit with status code 2 if breaking changes are detected.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def diff(ctx, config, json_output, fail_on_breaking, verbose):
    """Compare current database schema to the last tracked state."""
    try:
        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        old_schema = load_previous_state()
        if not old_schema:
            click.secho("[INFO] No previous schema state found. Run `schemap context` first to track state.", fg="yellow")
            return
            
        schema_model, _, _ = _process_schema(cfg, enrich=False)
        diffs, report = calculate_detailed_diff(old_schema, schema_model)
        
        if json_output:
            import json
            click.echo(json.dumps(report, indent=2))
            if fail_on_breaking and report["breaking_changes"]:
                sys.exit(2)
            return

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
        
        if fail_on_breaking and report["breaking_changes"]:
            click.secho(f"[BREAKING CHANGES DETECTED] {len(report['breaking_changes'])} breaking change(s) found:", fg="red", bold=True)
            for b in report["breaking_changes"]:
                click.secho(f"  - {b}", fg="red")
            sys.exit(2)

    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.argument('entity_type', type=click.Choice(['table'], case_sensitive=False), default='table')
@click.argument('name')
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--json', 'json_output', is_flag=True, help="Output explanation in JSON format.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def explain(ctx, entity_type, name, config, json_output, verbose):
    """Explain table architecture, columns, relationships, and centrality."""
    try:
        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        schema_model, _, _ = _process_schema(cfg, enrich=False)
        info = explain_table(schema_model, name)
        
        if json_output:
            import json
            click.echo(json.dumps(info, indent=2))
            return
            
        click.secho("\n" + "=" * 55, fg="cyan", bold=True)
        click.secho(f" Table Explanation: {info['table']}", fg="cyan", bold=True)
        click.secho("=" * 55, fg="cyan", bold=True)
        click.echo(f"  Business Name:     {info['business_name'] or 'N/A'}")
        click.echo(f"  Description:       {info['description']}")
        click.echo(f"  Centrality Rank:   {info['centrality_score']} ({info['degree_connections']} connections)")
        click.echo("-" * 55)
        click.secho("  Columns:", fg="yellow")
        for c in info['columns']:
            pk_tag = " [PK]" if c['primary_key'] else ""
            null_tag = "" if c['nullable'] else " NOT NULL"
            click.echo(f"   - {c['name']} ({c['data_type']}){pk_tag}{null_tag}")

        if info['outgoing_relationships']:
            click.echo("-" * 55)
            click.secho("  Outgoing Relationships (Foreign Keys):", fg="yellow")
            for r in info['outgoing_relationships']:
                click.echo(f"   - {r['column']} --> {r['ref_table']}.{r['ref_column']}")

        if info['incoming_relationships']:
            click.echo("-" * 55)
            click.secho("  Incoming Relationships (Referenced By):", fg="yellow")
            for r in info['incoming_relationships']:
                click.echo(f"   - {r['from_table']}.{r['from_column']} --> {r['to_column']}")

        click.secho("=" * 55 + "\n", fg="cyan", bold=True)

    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command(name="join")
@click.argument('tables', nargs=-1, required=True)
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--json', 'json_output', is_flag=True, help="Output join metadata in JSON format.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def join_tables(ctx, tables, config, json_output, verbose):
    """Find foreign key join path and generate SQL JOIN snippet."""
    try:
        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        schema_model, _, _ = _process_schema(cfg, enrich=False)
        result = find_join_path(schema_model, list(tables))

        if json_output:
            import json
            click.echo(json.dumps(result, indent=2))
            return

        click.secho("\n" + "=" * 55, fg="cyan", bold=True)
        click.secho(" Foreign Key Join Query Solver", fg="cyan", bold=True)
        click.secho("=" * 55, fg="cyan", bold=True)
        if result.get("full_path"):
            click.echo(f"  Joining Path: {' -> '.join(result['full_path'])}")
        click.echo("-" * 55)
        click.secho("  Generated SQL JOIN Snippet:", fg="yellow", bold=True)
        click.secho(f"\n{result['sql_snippet']}\n", fg="green")
        click.secho("=" * 55 + "\n", fg="cyan", bold=True)

    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--targets', default=None, help="Target frameworks e.g. codex,claude,cursor or comma-separated.")
@click.option('--scope', default='all', help="Filter schema scope by role profile (all, analytics, backend, core).")
@click.option('--sanitize', is_flag=True, help="Automatically redact sensitive PII and credential columns for AI safety.")
@click.option('--dir', 'target_dir', default=".", help="Target directory for agent files.")
@click.option('--dry-run', is_flag=True, help="Preview output without writing files.")
@click.option('--diff', is_flag=True, help="Show unified diff of proposed changes.")
@click.option('--merge/--no-merge', default=True, help="Safely merge with existing user content using markers.")
@click.option('--force', is_flag=True, help="Force overwrite existing agent files.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def agents(ctx, config, targets, scope, sanitize, target_dir, dry_run, diff, merge, force, verbose):
    """Generate CLAUDE.md, AGENTS.md, and agent rules for AI coding agents."""
    try:
        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        schema_model, _, _ = _process_schema(cfg, enrich=False, required_feature="sanitize" if sanitize else None)

        
        click.echo(f"-> Compiling AI agent context rules (scope: {scope}, sanitize: {sanitize})... ", nl=False)
        res = write_agent_files(
            schema_model=schema_model,
            target_dir=target_dir,
            targets=targets,
            dry_run=dry_run,
            diff=diff,
            merge=merge,
            force=force,
            scope=scope,
            sanitize=sanitize
        )
        click.secho("OK", fg="green")
        
        if dry_run or diff:
            click.secho("\n[PREVIEW] Generated Agent Output:", fg="cyan", bold=True)
            for fname, content in res.items():
                click.secho(f"\n--- {fname} ---", fg="yellow")
                try:
                    click.echo(content)
                except UnicodeEncodeError:
                    sys.stdout.buffer.write(content.encode("utf-8", errors="replace") + b"\n")
        else:
            click.secho("\n[SUCCESS] AI Agent Context files generated successfully:", fg="green", bold=True)
            for fname, fpath in res.items():
                click.echo(f"  [OK] {fname} -> {fpath}")
            click.echo("")
            
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--interactive/--non-interactive', default=True, help="Prompt interactively or use defaults.")
@click.option('--accept-all', is_flag=True, help="Auto-accept all inferred FK candidates and abbreviation mappings.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def fix(config, interactive, accept_all, verbose):
    """Interactively accept/reject suggested FK overrides and domain mappings, persisting them to YAML."""
    try:
        run_fix(config_path=config, interactive=interactive, accept_all=accept_all)
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise


@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--min-score', default=None, type=int, help="Minimum AI readiness score threshold (default: 80 or config).")
@click.option('--fail-on-breaking', is_flag=True, default=None, help="Fail gate on breaking schema changes (dropped tables/columns, removed FKs).")
@click.option('--output-report', default=None, help="File path to write the markdown PR quality report (e.g. pr-report.md).")
@click.option('--step-summary/--no-step-summary', default=True, help="Automatically append report to GITHUB_STEP_SUMMARY in CI.")
@click.option('--json', 'json_output', is_flag=True, help="Output gate evaluation results in JSON format.")
@click.option('--save-state', is_flag=True, help="Save current schema state to cache for next comparison.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def gate(ctx, config, min_score, fail_on_breaking, output_report, step_summary, json_output, save_state, verbose):
    """Evaluate AI readiness score & detect breaking changes as a CI/CD Quality Gate."""
    try:
        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        is_quiet = json_output or (ctx.obj and ctx.obj.get('quiet'))
        schema_model, _, unresolved = _process_schema(cfg, enrich=False, quiet=is_quiet, required_feature="gate")


        # Resolve thresholds from CLI flags or config defaults
        threshold = min_score if min_score is not None else cfg.gate.min_score
        breaking_flag = fail_on_breaking if fail_on_breaking is not None else cfg.gate.fail_on_breaking

        prev_schema = load_previous_state()
        gate_res = evaluate_gate(
            current_schema=schema_model,
            previous_schema=prev_schema,
            min_score=threshold,
            fail_on_breaking=breaking_flag,
            unresolved_abbrs=unresolved
        )

        project_name = (cfg.domain.project_name or cfg.domain.name) if (hasattr(cfg, 'domain') and cfg.domain) else None
        md_report = generate_gate_markdown_report(gate_res, project_name=project_name)

        # 1. Output Report to file if requested
        if output_report:
            out_p = Path(output_report)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                f.write(md_report)

        # 2. Append to GitHub Step Summary if running in CI
        if step_summary:
            gh_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
            if gh_summary_file:
                try:
                    with open(gh_summary_file, "a", encoding="utf-8") as f:
                        f.write("\n" + md_report + "\n")
                except Exception:
                    pass

        # 3. Handle JSON output
        if json_output:
            import json
            click.echo(json.dumps(gate_res.to_dict(), indent=2))
        else:
            # Console rendering
            click.echo("")
            if gate_res.passed:
                click.secho("=======================================================", fg="green", bold=True)
                click.secho(f" [PASSED] Schemap CI/CD AI Quality Gate: {gate_res.score}/100", fg="green", bold=True)
                click.secho("=======================================================", fg="green", bold=True)
                click.secho(f"  AI Readiness Score: {gate_res.score}/100 (Threshold: >= {gate_res.min_score}/100)", fg="cyan")
                if gate_res.score_delta is not None:
                    delta_sign = f"+{gate_res.score_delta}" if gate_res.score_delta >= 0 else str(gate_res.score_delta)
                    click.secho(f"  Score Delta: {delta_sign} pts compared to cached schema state", fg="cyan")
                if gate_res.blast_radius and gate_res.blast_radius.get("severity") != "NONE":
                    sev = gate_res.blast_radius.get("severity")
                    click.secho(f"  Blast Radius Risk: {sev} ({gate_res.blast_radius.get('impacted_tables_count')} tables affected)", fg="yellow")
                click.secho("\n Schema is ready for AI coding agents (Claude Code, Cursor, Copilot).\n", fg="green")
            else:
                click.secho("=======================================================", fg="red", bold=True)
                click.secho(f" [BLOCKED] Schemap CI/CD AI Quality Gate: {gate_res.score}/100", fg="red", bold=True)
                click.secho("=======================================================", fg="red", bold=True)
                click.secho(f"  AI Readiness Score: {gate_res.score}/100 (Threshold: >= {gate_res.min_score}/100)", fg="yellow")
                click.secho("\n Gate Violations:", fg="red", bold=True)
                for reason in gate_res.failure_reasons:
                    click.secho(f"  [X] {reason}", fg="red")
                if gate_res.issues:
                    click.secho("\n Recommended Remediation:", fg="yellow", bold=True)
                    for issue in gate_res.issues:
                        click.echo(f"  - {issue}")
                click.secho("\n Run 'schemap fix' or update schemap.yaml to resolve schema issues.\n", fg="yellow")

        # 4. Save state if requested
        if save_state:
            save_current_state(schema_model)

        if not gate_res.passed:
            sys.exit(1)

    except LicenseError as le:
        click.secho(f"\n[LICENSE ERROR] {str(le)}", fg="red", bold=True)
        sys.exit(1)
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise
        sys.exit(1)




@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--targets', default=None, help="Target agent targets.")
@click.option('--dir', 'target_dir', default=".", help="Target directory.")
@click.option('--force', is_flag=True, help="Force re-compilation even if schema fingerprint is unchanged.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def sync(ctx, config, targets, target_dir, force, verbose):
    """Regenerate database context and agent rules ONLY when the schema fingerprint changes."""
    try:
        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        schema_model, raw_tables, _ = _process_schema(cfg, enrich=False)
        
        current_fp = calculate_schema_fingerprint(schema_model)
        cached_fp = get_cached_fingerprint()
        
        if not force and cached_fp == current_fp:
            click.secho("[INFO] Schema fingerprint unchanged. Skipping context generation.", fg="cyan")
            return
            
        click.echo("-> Schema fingerprint changed (or --force). Syncing context maps... ", nl=False)
        out_path = Path(cfg.output.file_path) if cfg.output.file_path else Path("schemap_database_context.md")
        rendered_output = generate_database_context(schema_model)
        write_output(rendered_output, str(out_path))
        
        write_agent_files(schema_model, target_dir=target_dir, targets=targets, force=force)
        save_fingerprint(current_fp)
        
        click.secho("OK", fg="green")
        click.secho(f"[SUCCESS] Context and agent files synced. Updated fingerprint [{current_fp[:10]}...]", fg="green", bold=True)
        
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command(name="status")
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--verify', is_flag=True, help="Force online license verification.")
def license_status(config, verify):
    """Display configured license status, active seats, device ID, and plan details."""
    _show_license_status(config, verify)

@cli.command(name="license")
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--verify', is_flag=True, help="Force online license verification.")
def license_cmd(config, verify):
    """Display configured license status, active seats, device ID, and plan details."""
    _show_license_status(config, verify)

def _show_license_status(config, verify):
    config_key = None
    cfg_endpoint = None
    try:
        cfg = load_config(config)
        config_key = cfg.license_key
        cfg_endpoint = cfg.license_endpoint
    except Exception:
        pass

    active_key, source = resolve_license_key(config_key=config_key)
    device_id = get_or_create_device_id()

    click.secho("\n" + "=" * 50, fg="cyan", bold=True)
    click.secho(" Schemap License Status", fg="cyan", bold=True)
    click.secho("=" * 50, fg="cyan", bold=True)

    if active_key:
        masked_key = active_key[:8] + "..." + active_key[-4:] if len(active_key) > 12 else active_key
        endpoint = resolve_license_endpoint(config_endpoint=cfg_endpoint)
        
        result = verify_license_online(active_key, endpoint)
        
        if result.get("activated") or result.get("valid"):
            active_tier_name = (result.get("tier") or result.get("plan_tier") or "Pro").title()
            click.echo("  Tier:             ", nl=False)
            click.secho(f"{active_tier_name} (Active)", fg="green", bold=True)
            click.echo(f"  Active Key:       {masked_key}")
            click.echo(f"  Key Source:       {source}")
            
            seats_used = result.get("seats_used", 1)
            max_seats = result.get("max_seats", 3)
            click.echo("  Seats Connected:  ", nl=False)
            click.secho(f"{seats_used} / {max_seats} devices active", fg="cyan", bold=True)
            
            click.echo(f"  Device ID:        {device_id}")
            
            plan = result.get("plan", "pro")
            plan_label = {
                "monthly": "Monthly Pro",
                "quarterly": "Quarterly Pro",
                "semiannual": "6-Month Pro",
                "annual": "Annual Pro",
                "lifetime": "Founder Lifetime Pro",
                "team": "Team Subscription",
                "enterprise": "Enterprise Subscription"
            }.get(plan.lower(), f"{plan.capitalize()}")
            click.echo(f"  Plan:             {plan_label}")
            
            exp = result.get("expires_at")
            if exp:
                try:
                    exp_clean = exp.split("T")[0]
                    click.echo(f"  Expires:          {exp_clean}")
                except Exception:
                    click.echo(f"  Expires:          {exp}")
            else:
                click.echo("  Expires:          Lifetime Access (No Expiration)")
        else:
            from .license import _read_cache
            last_verified, cached_tier = _read_cache(active_key)
            if last_verified is not None:
                age_days = (time.time() - last_verified) / 86400.0
                tier_title = (cached_tier or "Pro").title()
                click.echo("  Tier:             ", nl=False)
                click.secho(f"{tier_title} (Active via Local Cache)", fg="green", bold=True)
                click.echo(f"  Active Key:       {masked_key}")
                click.echo(f"  Key Source:       {source}")
                click.echo(f"  Device ID:        {device_id}")
                click.echo(f"  Cache Status:     Valid (verified {age_days:.1f} days ago)")
            else:
                click.echo("  Tier:             ", nl=False)
                click.secho("Pro (Unverified / Error)", fg="yellow", bold=True)
                click.echo(f"  Active Key:       {masked_key}")
                click.echo(f"  Key Source:       {source}")
                click.echo(f"  Device ID:        {device_id}")
                click.secho(f"  Verification:     Failed ({result.get('error', 'Invalid or expired license.')})", fg="red")


        click.echo("-" * 50)
        click.secho("  Tip: Run 'schemap deactivate' to disconnect this device.", fg="yellow")
    else:
        click.echo("  Tier:             ", nl=False)
        click.secho("Free Tier", fg="yellow", bold=True)
        click.echo(f"  Table Limit:      {FREE_TABLE_LIMIT} tables")
        click.echo(f"  Device ID:        {device_id}")
        click.echo(f"  CI Automation:    Blocked on Free Tier")
        click.echo(f"  Key Source:       None")
        click.echo("-" * 50)
        click.secho("  [$] Launch Pricing: $1.99/mo | $4.99/qtr | $8.99/6mo | $15.99/yr | $29 Founder Lifetime", fg="magenta")
        click.secho("  Tip: Run 'schemap activate <license-key>' to activate Pro.", fg="yellow")

    click.echo(f"  Credentials File: {CREDENTIALS_FILE}")
    click.secho("=" * 50 + "\n", fg="cyan", bold=True)

@cli.group()
def trial():
    """Manage Schemap 7-Day Free Pro trial."""
    pass

@trial.command(name="start")
def trial_start():
    """Open Schemap Pro / Trial checkout page."""
    checkout_url = "https://buy.stripe.com/dRm00jeG13kpfoA131dIA01"
    click.secho("\n" + "=" * 50, fg="cyan", bold=True)
    click.secho(" Schemap Pro Trial & Launch Checkout", fg="cyan", bold=True)
    click.secho("=" * 50, fg="cyan", bold=True)
    click.echo(f"  -> Opening Pro checkout link: {checkout_url}")
    click.echo("  Launch special: $1.99/mo or $29 Founder Lifetime")
    click.secho("=" * 50 + "\n", fg="cyan", bold=True)
    try:
        webbrowser.open(checkout_url)
    except Exception:
        pass

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
def deactivate(config):
    """Deactivate Schemap Pro license on this device to free up a seat."""
    config_key = None
    try:
        cfg = load_config(config)
        config_key = cfg.license_key
    except Exception:
        pass

    active_key, source = resolve_license_key(config_key=config_key)
    if not active_key:
        click.secho("[INFO] No active license configured on this machine.", fg="yellow")
        sys.exit(0)

    endpoint = resolve_license_endpoint(config_endpoint=cfg.license_endpoint if 'cfg' in locals() else None)
    click.echo(f"-> Deactivating seat for active license key '{active_key[:12]}...'... ", nl=False)

    deactivate_license_online(active_key, endpoint)
    clear_credentials()
    click.secho("OK", fg="green")
    click.secho("\n[SUCCESS] License deactivated on this device. (1 seat freed)", fg="green", bold=True)

@cli.command()
def logout():
    """Clear global credentials and local license validation cache."""
    clear_credentials()
    click.secho("\n[SUCCESS] Successfully logged out. Cleared global credentials and license cache.", fg="green")

@cli.group()
def skills():
    """Manage AI Agent skills (Codex, Claude, Cursor)."""
    pass

@skills.command(name="install")
@click.option('--targets', default="all", help="Target agent frameworks e.g. codex,claude,cursor or all.")
@click.option('--dir', 'target_dir', default=".", help="Target root directory.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
def install_skills(targets, target_dir, verbose):
    """Install agent-native schemap AI skills for Codex, Claude, and Cursor."""
    try:
        click.echo(f"-> Installing Schemap AI Agent skills (targets: {targets})... ", nl=False)
        paths = install_agent_skills(targets=targets, base_dir=target_dir)
        click.secho("OK", fg="green")
        click.secho("\n[SUCCESS] Installed AI Agent Skills:", fg="green", bold=True)
        for p in paths:
            click.echo(f"  [OK] {p}")
        click.echo("")
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--json', 'json_output', is_flag=True, help="Output canonical queries in JSON format.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def examples(ctx, config, json_output, verbose):
    """Generate canonical reference SQL JOIN queries from database relationships."""
    try:
        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        schema_model, _, _ = _process_schema(cfg, enrich=False)
        from .context import generate_query_examples
        queries = generate_query_examples(schema_model)
        
        if json_output:
            import json
            click.echo(json.dumps({"canonical_sql_examples": queries}, indent=2))
            return
            
        click.secho("\n" + "=" * 55, fg="cyan", bold=True)
        click.secho(" Canonical Reference SQL Examples", fg="cyan", bold=True)
        click.secho("=" * 55, fg="cyan", bold=True)
        if queries:
            for q in queries:
                click.secho(f"{q}\n", fg="green")
        else:
            click.echo("No foreign key relationships detected to auto-generate queries.")
        click.secho("=" * 55 + "\n", fg="cyan", bold=True)
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise

@cli.group()
def hook():
    """Manage Git pre-commit hooks for automatic Schemap context sync."""
    pass

@hook.command(name="install")
def hook_install():
    """Install a Git pre-commit hook to auto-sync database context on SQL migration commits."""
    git_dir = Path(".git")
    if not git_dir.exists():
        click.secho("[ERROR] Not a Git repository (.git folder not found).", fg="red")
        sys.exit(1)
        
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_file = hooks_dir / "pre-commit"
    
    script = """#!/bin/sh
# Schemap auto-sync pre-commit hook
echo "[Schemap] Auto-syncing database context map..."
if command -v schemap >/dev/null 2>&1; then
    schemap sync --quiet
fi
"""
    with open(hook_file, "w", encoding="utf-8") as f:
        f.write(script)
    import os
    try:
        os.chmod(hook_file, 0o755)
    except Exception:
        pass
        
    click.secho(f"[OK] Installed Git pre-commit hook at {hook_file}", fg="green", bold=True)


@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--json', 'json_output', is_flag=True, help="Output glossary in JSON format.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def glossary(ctx, config, json_output, verbose):
    """View compiled domain business glossary and calculations."""
    try:
        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        is_quiet = json_output or (ctx.obj and ctx.obj.get('quiet'))
        schema_model, _, _ = _process_schema(cfg, enrich=False, quiet=is_quiet)

        if json_output:
            import json
            click.echo(json.dumps({
                "glossary": schema_model.glossary,
                "global_guardrails": schema_model.global_guardrails
            }, indent=2))
            return

        click.echo("")
        click.secho("=" * 60, fg="cyan", bold=True)
        click.secho("  Schemap Business Semantics & Glossary", fg="cyan", bold=True)
        click.secho("=" * 60, fg="cyan", bold=True)

        if schema_model.glossary:
            click.secho("\n  [Business Glossary]", fg="yellow", bold=True)
            for term, defn in schema_model.glossary.items():
                click.echo(f"  * {term:15} : {defn}")
        else:
            click.echo("  No glossary terms defined. Add them under 'semantics.glossary' in schemap.yaml.")

        if schema_model.global_guardrails:
            click.secho("\n  [Global AI Guardrails & Policies]", fg="yellow", bold=True)
            for r in schema_model.global_guardrails:
                click.echo(f"  - {r}")

        click.secho("\n" + "=" * 60 + "\n", fg="cyan", bold=True)

    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise


@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--output', default=".schemap/semantics.yaml", help="Output path for starter semantics file.")
@click.option('--force', is_flag=True, help="Overwrite existing semantics file.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def annotate(ctx, config, output, force, verbose):
    """Scaffold a starter business semantics template populated with discovered tables."""
    try:
        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        schema_model, _, _ = _process_schema(cfg, enrich=False)
        from .semantics import generate_default_semantics_template

        out_path = Path(output)
        if out_path.exists() and not force:
            click.secho(f"\n[WARNING] {out_path} already exists. Use --force to overwrite.", fg="yellow")
            return

        out_path.parent.mkdir(parents=True, exist_ok=True)
        content = generate_default_semantics_template(schema_model)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        click.secho(f"\n[SUCCESS] Generated starter semantics template at {out_path}", fg="green", bold=True)
        click.echo("Edit this file to define owners, glossary terms, virtual relations, and query guardrails.")

    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise


@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--snippet', type=click.Choice(['cursor', 'claude', 'all'], case_sensitive=False), default=None, help="Print MCP client configuration JSON snippet.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def mcp(ctx, config, snippet, verbose):
    """Start Schemap Model Context Protocol (MCP) server for dynamic AI agent integration."""
    try:
        from .mcp import run_mcp_server, generate_mcp_config_snippet

        if snippet:
            click.echo(generate_mcp_config_snippet(platform=snippet.lower()))
            return

        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        schema_model, _, _ = _process_schema(cfg, enrich=False, quiet=True)
        run_mcp_server(schema_model)

    except Exception as e:
        sys.stderr.write(f"[MCP ERROR] {str(e)}\n")
        if verbose:
            raise


@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--team-size', default=10, type=int, help="Engineering team size using AI tools (default: 10).")
@click.option('--prompts-per-day', default=50, type=int, help="Estimated AI queries/prompts per developer per day (default: 50).")
@click.option('--hourly-rate', default=85.0, type=float, help="Average developer hourly loaded cost in USD (default: $85.00).")
@click.option('--output-report', default=None, help="File path to write the markdown ROI report (e.g. roi-summary.md).")
@click.option('--json', 'json_output', is_flag=True, help="Output ROI metrics in JSON format.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def roi(ctx, config, team_size, prompts_per_day, hourly_rate, output_report, json_output, verbose):
    """Calculate and export enterprise token savings & team productivity ROI metrics."""
    try:
        from .roi import calculate_team_roi, generate_roi_report

        prof = ctx.obj.get('profile') if ctx.obj else None
        cfg = load_config(config, profile=prof)
        is_quiet = json_output or (ctx.obj and ctx.obj.get('quiet'))
        schema_model, raw_tables, unresolved = _process_schema(cfg, enrich=False, quiet=is_quiet, required_feature="roi")

        roi_data = calculate_team_roi(
            schema_model=schema_model,
            raw_tables=raw_tables,
            team_size=team_size,
            prompts_per_dev_day=prompts_per_day,
            dev_hourly_rate=hourly_rate,
            unresolved_abbrs=unresolved
        )

        project_name = (cfg.domain.project_name or cfg.domain.name) if (hasattr(cfg, 'domain') and cfg.domain) else None
        report_md = generate_roi_report(roi_data, project_name=project_name)

        if output_report:
            out_p = Path(output_report)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                f.write(report_md)

        if json_output:
            import json
            click.echo(json.dumps(roi_data, indent=2))
        else:
            click.echo("")
            click.secho("================================================================", fg="cyan", bold=True)
            click.secho(f"  Schemap Enterprise ROI Dashboard ({team_size} Developers)", fg="cyan", bold=True)
            click.secho("================================================================", fg="cyan", bold=True)
            rs = roi_data["roi_summary"]
            te = roi_data["token_economics"]
            pe = roi_data["productivity_economics"]
            click.secho(f"  * Estimated Annual Economic ROI: {rs['roi_multiple']} ({rs['net_economic_benefit_usd']:,.2f} Net Benefit)", fg="green", bold=True)
            click.echo(f"  * Direct Annual Token Savings:   ${te['annual_token_savings_usd']:,.2f} (Compression: {te['compression_percentage']})")
            click.echo(f"  * Engineering Velocity Gain:     ${pe['annual_productivity_value_usd']:,.2f} ({pe['total_annual_hours_saved']} dev hours saved)")
            click.echo(f"  * Schemap Team Subscription:     ${rs['schemap_annual_cost_usd']:,.2f}/yr")
            click.secho("================================================================\n", fg="cyan", bold=True)
            if output_report:
                click.secho(f"[SUCCESS] Exported detailed executive ROI report to: {output_report}\n", fg="green")

    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise


@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--revoke', default=None, help="Device ID or fingerprint to revoke from active license seats.")
@click.option('--portal', is_flag=True, help="Generate and open Stripe Customer Billing Portal link for seat adjustments.")
@click.option('--json', 'json_output', is_flag=True, help="Output seat status in JSON format.")
def seats(config, revoke, portal, json_output):
    """View team seat allocation, active devices, and manage license concurrency."""
    try:
        config_key = None
        cfg_endpoint = None
        try:
            cfg = load_config(config)
            config_key = cfg.license_key
            cfg_endpoint = cfg.license_endpoint
        except Exception:
            pass

        active_key, source = resolve_license_key(config_key=config_key)
        if not active_key:
            click.secho("\n[ERROR] No active license key found. Run `schemap activate <LICENSE_KEY>` first.", fg="red")
            sys.exit(1)

        endpoint = resolve_license_endpoint(config_endpoint=cfg_endpoint)

        if portal:
            click.echo("-> Generating Stripe Customer Billing Portal link... ", nl=False)
            res = create_customer_portal_session(active_key, endpoint)
            portal_url = res.get("url")
            if portal_url:
                click.secho("OK", fg="green")
                click.echo(f"\nBilling Portal URL:\n  {portal_url}\n")
                try:
                    import webbrowser
                    webbrowser.open(portal_url)
                    click.secho("Opened Customer Billing Portal in default browser.", fg="green")
                except Exception:
                    pass
            else:
                click.secho(f"\n[ERROR] Failed to generate portal link: {res.get('error')}", fg="red")
            return

        if revoke:
            click.echo(f"-> Revoking seat for device '{revoke}'... ", nl=False)
            res = deactivate_license_online(active_key, endpoint, device_id_to_revoke=revoke)
            if res.get("valid") or res.get("deactivated"):
                click.secho("OK", fg="green")
                click.secho(f"\n[SUCCESS] Revoked device '{revoke}' from team license.", fg="green", bold=True)
            else:
                click.secho(f"\n[ERROR] Failed to revoke device: {res.get('error')}", fg="red")
            return

        status = fetch_seats_status(active_key, endpoint)
        if json_output:
            import json
            click.echo(json.dumps(status, indent=2))
            return

        click.echo("")
        click.secho("=======================================================", fg="cyan", bold=True)
        click.secho("  Schemap Team Seat & Device Management", fg="cyan", bold=True)
        click.secho("=======================================================", fg="cyan", bold=True)
        click.echo(f"  Plan Tier:        {status.get('tier', 'team').upper()}")
        click.echo(f"  Billing Mode:     {status.get('plan', 'subscription')}")
        click.echo(f"  Seats Active:     {status.get('seats_used', 1)} / {status.get('max_seats', 10)}")
        click.echo(f"  Current Device:   {get_or_create_device_id()}")

        devices = status.get("devices", [])
        if devices:
            click.secho("\n  [Connected Devices / CI Runners]", fg="yellow", bold=True)
            for d in devices:
                fp = d.get("device_fingerprint", "")
                fp_short = fp[:12] + "..." if len(fp) > 12 else fp
                inst = d.get("instance_name", "developer-machine")
                seen = d.get("last_seen_at", "active")
                click.echo(f"  * [{fp_short}] {inst:<24} (Last seen: {seen})")
            click.echo("\n  Tip: Run 'schemap seats --revoke <device_id>' to free up a seat.")

        click.secho("=======================================================\n", fg="cyan", bold=True)


    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        sys.exit(1)


@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--no-open', is_flag=True, help="Print URL only without opening browser.")
def portal(config, no_open):
    """Open Stripe Customer Billing Portal to adjust team seats, plans, and invoices."""
    try:
        config_key = None
        cfg_endpoint = None
        try:
            cfg = load_config(config)
            config_key = cfg.license_key
            cfg_endpoint = cfg.license_endpoint
        except Exception:
            pass

        active_key, _ = resolve_license_key(config_key=config_key)
        if not active_key:
            click.secho("\n[ERROR] No active license key found. Run `schemap activate <LICENSE_KEY>` first.", fg="red")
            sys.exit(1)

        endpoint = resolve_license_endpoint(config_endpoint=cfg_endpoint)
        click.echo("-> Generating Stripe Customer Billing Portal link... ", nl=False)
        res = create_customer_portal_session(active_key, endpoint)
        portal_url = res.get("url")
        if portal_url:
            click.secho("OK", fg="green")
            click.echo(f"\nBilling Portal URL:\n  {portal_url}\n")
            if not no_open:
                try:
                    import webbrowser
                    webbrowser.open(portal_url)
                    click.secho("Opened Customer Billing Portal in default browser.", fg="green")
                except Exception:
                    pass
        else:
            click.secho(f"\n[ERROR] Failed to generate portal link: {res.get('error')}", fg="red")
            sys.exit(1)
    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        sys.exit(1)



@cli.command()
@click.option('--config', default="schemap.yaml", help="Path to configuration file.")
@click.option('--watch-path', '-w', multiple=True, help="Additional files or directories to watch (e.g. prisma/migrations).")
@click.option('--poll-db', default=0, type=int, help="Periodic database polling interval in seconds (0 = disabled).")
@click.option('--webhook-url', default=None, help="Slack, Discord, or HTTP webhook URL for breaking change alerts.")
@click.option('--once', is_flag=True, help="Perform a single synchronization cycle and exit.")
@click.option('--verbose', is_flag=True, help="Enable verbose output.")
@click.pass_context
def watch(ctx, config, watch_path, poll_db, webhook_url, once, verbose):
    """Run continuous schema watcher to auto-regenerate AI agent context on migrations/changes."""
    try:
        from .watcher import SchemaWatcher

        prof = ctx.obj.get('profile') if ctx.obj else None
        
        watcher = SchemaWatcher(
            config_path=config,
            profile=prof,
            custom_watch_paths=list(watch_path),
            poll_db_interval=poll_db,
            webhook_url=webhook_url,
            logger=lambda msg: click.echo(msg)
        )

        if once:
            res = watcher.sync_once()
            click.secho(f"\n[SUCCESS] Synchronized AI agent context files (Score: {res['ai_readiness_score']}/100)", fg="green", bold=True)
            if res["breaking_changes"]:
                click.secho(f"[WARNING] {len(res['breaking_changes'])} breaking changes detected!", fg="yellow")
            return

        click.secho("\n================================================================", fg="cyan", bold=True)
        click.secho("  Schemap Continuous Schema & AI Agent Synchronizer", fg="cyan", bold=True)
        click.secho("================================================================\n", fg="cyan", bold=True)
        watcher.start()

    except Exception as e:
        click.secho(f"\n[ERROR] {str(e)}", fg="red")
        if verbose:
            raise


if __name__ == "__main__":
    cli()





