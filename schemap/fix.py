import sys
from pathlib import Path
from typing import Dict, Any, List
import click
import yaml

from .config import load_config
from .extractor import extract_schema
from .models import DatabaseSchemaModel
from .enrichment import apply_heuristics, apply_description_overrides, apply_fk_overrides
from .doctor import get_doctor_report, infer_foreign_key_candidates

def run_fix(
    config_path: str = "schemap.yaml",
    interactive: bool = True,
    accept_all: bool = False
) -> Dict[str, Any]:
    """
    Interactively or automatically accept suggested FK overrides, domain mappings, and column descriptions, persisting them to schemap.yaml.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file {config_path} not found.")

    with open(path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f) or {}

    cfg = load_config(config_path)
    raw_tables = extract_schema(cfg.database.connection_url, cfg.database.exclude_tables)
    schema_model = DatabaseSchemaModel(tables=raw_tables)
    schema_model, unresolved = apply_heuristics(schema_model, cfg.domain.mappings, cfg.domain.ignore_abbreviations)
    schema_model = apply_description_overrides(schema_model, cfg.schema_descriptions)
    schema_model = apply_fk_overrides(schema_model, cfg.foreign_key_overrides)

    doctor_report = get_doctor_report(schema_model, raw_tables, unresolved)
    actionable = doctor_report.get("actionable_fixes", {})

    fk_candidates = actionable.get("foreign_key_candidates", [])
    unresolved_abbrs = actionable.get("unresolved_abbreviations", {})

    accepted_fks = []
    accepted_mappings = {}

    is_tty = sys.stdin.isatty() and interactive and not accept_all

    click.secho("\n" + "=" * 55, fg="cyan", bold=True)
    click.secho(" 🛠️  Schemap Interactive Schema Fixer", fg="cyan", bold=True)
    click.secho("=" * 55 + "\n", fg="cyan", bold=True)

    # 1. Foreign Key Candidates
    if fk_candidates:
        click.secho("🔗 Suggested Foreign Key Candidate Relationships:", fg="yellow", bold=True)
        for cand in fk_candidates:
            rel_str = f"{cand['table']}.{cand['column']} --> {cand['ref_table']}.{cand['ref_column']}"
            conf_str = f"Confidence: {cand['confidence']}% ({cand['reason']})"
            
            should_accept = False
            if accept_all or not is_tty:
                should_accept = True
                click.echo(f"  [AUTO-ACCEPT] {rel_str} ({conf_str})")
            else:
                should_accept = click.confirm(f"Accept relationship: {rel_str}?", default=True)

            if should_accept:
                accepted_fks.append({
                    "table": cand["table"],
                    "column": cand["column"],
                    "ref_table": cand["ref_table"],
                    "ref_column": cand["ref_column"]
                })

    # 2. Unresolved Abbreviations
    if unresolved_abbrs:
        click.secho("\n🔤 Unresolved Abbreviation Mappings:", fg="yellow", bold=True)
        for abbr, default_exp in unresolved_abbrs.items():
            if accept_all or not is_tty:
                accepted_mappings[abbr] = default_exp
                click.echo(f"  [AUTO-ACCEPT] {abbr} -> {default_exp}")
            else:
                exp = click.prompt(f"Expansion for '{abbr}'", default=default_exp)
                accepted_mappings[abbr] = exp

    # Update raw_config dict
    if accepted_fks:
        existing_fks = raw_config.get("foreign_key_overrides", [])
        for fk in accepted_fks:
            if fk not in existing_fks:
                existing_fks.append(fk)
        raw_config["foreign_key_overrides"] = existing_fks

    if accepted_mappings:
        if "domain" not in raw_config or not isinstance(raw_config["domain"], dict):
            raw_config["domain"] = {}
        if "mappings" not in raw_config["domain"] or not isinstance(raw_config["domain"]["mappings"], dict):
            raw_config["domain"]["mappings"] = {}
        raw_config["domain"]["mappings"].update(accepted_mappings)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(raw_config, f, sort_keys=False)

    click.secho(f"\n[SUCCESS] Updated {config_path} with {len(accepted_fks)} FK relationship(s) and {len(accepted_mappings)} abbreviation mapping(s)!", fg="green", bold=True)
    click.secho("=" * 55 + "\n", fg="cyan", bold=True)

    return {
        "accepted_foreign_keys": accepted_fks,
        "accepted_mappings": accepted_mappings
    }
