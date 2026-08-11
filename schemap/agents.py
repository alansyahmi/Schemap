import difflib
from pathlib import Path
from typing import Dict, List, Union, Tuple

from .models import DatabaseSchemaModel
from .context import calculate_central_tables, generate_relationship_map

START_MARKER = "<!-- schemap:start -->"
END_MARKER = "<!-- schemap:end -->"

def generate_claude_md(schema_model: DatabaseSchemaModel) -> str:
    """Generate CLAUDE.md tailored for Claude Code and Anthropic models."""
    total_tables = len(schema_model.tables)
    central = calculate_central_tables(schema_model)
    top_tables = [c[0] for c in central[:5]]
    
    rel_map = generate_relationship_map(schema_model)
    
    out = []
    out.append("# Database Architecture & Context for Claude\n")
    out.append("This project relies on the database schema outlined below. Refer to this context when writing queries, migrations, or database-related business logic.\n")
    
    out.append("## Core Statistics")
    out.append(f"- **Active Tables**: {total_tables}")
    out.append(f"- **Key Hub Entities**: {', '.join(top_tables)}\n")
    
    out.append("## Central Tables Overview")
    for name in top_tables:
        t_model = next((t for t in schema_model.tables if t.name == name), None)
        if t_model:
            cols = [f"`{c.name}` ({c.data_type})" for c in t_model.columns[:6]]
            more = f" ...+{len(t_model.columns)-6} more" if len(t_model.columns) > 6 else ""
            out.append(f"- **`{t_model.name}`**: {t_model.description or 'No description'}")
            out.append(f"  Columns: {', '.join(cols)}{more}")
    out.append("")
    
    out.append("## Schema Relationships")
    out.append("```")
    out.extend(rel_map[:10])
    if len(rel_map) > 10:
        out.append(f"... and {len(rel_map)-10} more relationships.")
    out.append("```\n")
    
    out.append("## Query Guidelines")
    out.append("- Always verify foreign key constraints before building multi-table joins.")
    out.append("- Use standard indexed columns (`id`, `*_id`) for joins.\n")
    
    return "\n".join(out)

def generate_agents_md(schema_model: DatabaseSchemaModel) -> str:
    """Generate AGENTS.md for generic AI coding agents (Codex, Cursor, Copilot, etc.)."""
    total_tables = len(schema_model.tables)
    central = calculate_central_tables(schema_model)
    top_tables = [c[0] for c in central[:5]]
    
    out = []
    out.append("# AGENTS.md — Database Context\n")
    out.append("This file provides automated database context for AI agents working in this repository.\n")
    
    out.append("## Database Summary")
    out.append(f"- Total Tables: {total_tables}")
    out.append(f"- Key Central Tables: {', '.join(top_tables)}\n")
    
    out.append("## Table Map")
    for t in schema_model.tables:
        col_summary = ", ".join([c.name for c in t.columns])
        out.append(f"### Table: `{t.name}`")
        if t.description:
            out.append(f"Description: {t.description}")
        out.append(f"Columns: {col_summary}")
        if t.foreign_keys:
            fk_strs = []
            for fk in t.foreign_keys:
                if isinstance(fk, dict):
                    col = fk.get('column')
                    ref_tbl = fk.get('ref_table')
                    ref_col = fk.get('ref_column')
                else:
                    col = getattr(fk, 'column_name', getattr(fk, 'column', None))
                    ref_tbl = getattr(fk, 'foreign_table_name', getattr(fk, 'ref_table', None))
                    ref_col = getattr(fk, 'foreign_column_name', getattr(fk, 'ref_column', None))
                fk_strs.append(f"{col} -> {ref_tbl}.{ref_col}")
            out.append(f"Foreign Keys: {', '.join(fk_strs)}")
        out.append("")
        
    return "\n".join(out)

def merge_content_with_markers(existing_content: str, new_generated_content: str, force: bool = False) -> str:
    """Safely merge newly generated content into existing file using markers."""
    block = f"{START_MARKER}\n{new_generated_content.strip()}\n{END_MARKER}"
    if force or not existing_content or not existing_content.strip():
        return block + "\n"

    if START_MARKER in existing_content and END_MARKER in existing_content:
        before = existing_content.split(START_MARKER)[0]
        after = existing_content.split(END_MARKER)[1]
        return f"{before.rstrip()}\n\n{block}\n{after.lstrip()}"
    else:
        return f"{existing_content.rstrip()}\n\n{block}\n"

def parse_targets(targets: Union[str, List[str], None]) -> set[str]:
    """Parse comma-separated or list targets into normalized set."""
    if not targets or targets == "all":
        return {"codex", "claude", "cursor", "agents"}
    if isinstance(targets, str):
        t_list = [t.strip().lower() for t in targets.split(",") if t.strip()]
    else:
        t_list = [t.strip().lower() for t in targets if t and t.strip()]
    return set(t_list)

def write_agent_files(
    schema_model: DatabaseSchemaModel,
    target_dir: str = ".",
    targets: Union[str, List[str], None] = None,
    dry_run: bool = False,
    diff: bool = False,
    merge: bool = True,
    force: bool = False
) -> Dict[str, str]:
    """
    Generate and write AI agent files (AGENTS.md, CLAUDE.md, .cursorrules)
    supporting target filtering, marker preservation, dry-run, and unified diff.
    """
    base = Path(target_dir)
    target_set = parse_targets(targets)
    
    files_to_generate: Dict[str, str] = {}
    
    if "claude" in target_set:
        files_to_generate["CLAUDE.md"] = generate_claude_md(schema_model)
        
    if "codex" in target_set or "agents" in target_set or "copilot" in target_set or "general" in target_set or "all" in target_set:
        files_to_generate["AGENTS.md"] = generate_agents_md(schema_model)
        
    if "cursor" in target_set:
        cursor_dir = base / ".cursor" / "rules"
        cursor_path_rel = ".cursor/rules/schemap.mdc"
        files_to_generate[cursor_path_rel] = generate_agents_md(schema_model)
        if "AGENTS.md" not in files_to_generate:
            files_to_generate["AGENTS.md"] = generate_agents_md(schema_model)

    results: Dict[str, str] = {}
    
    for fname, raw_content in files_to_generate.items():
        file_path = base / fname
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        existing_content = ""
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
                
        final_content = merge_content_with_markers(existing_content, raw_content, force=(force or not merge))
        
        if diff:
            existing_lines = existing_content.splitlines(keepends=True)
            final_lines = final_content.splitlines(keepends=True)
            udiff = "".join(difflib.unified_diff(existing_lines, final_lines, fromfile=f"a/{fname}", tofile=f"b/{fname}"))
            results[fname] = udiff if udiff else "No changes."
        elif dry_run:
            results[fname] = final_content
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_content)
            results[fname] = str(file_path)
            
    return results

