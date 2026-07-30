from pathlib import Path
from typing import Dict
from .models import DatabaseSchemaModel
from .context import calculate_central_tables, generate_relationship_map

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

def write_agent_files(schema_model: DatabaseSchemaModel, target_dir: str = ".") -> Dict[str, str]:
    """Generate and write CLAUDE.md and AGENTS.md files."""
    base = Path(target_dir)
    
    claude_content = generate_claude_md(schema_model)
    claude_path = base / "CLAUDE.md"
    with open(claude_path, "w", encoding="utf-8") as f:
        f.write(claude_content)
        
    agents_content = generate_agents_md(schema_model)
    agents_path = base / "AGENTS.md"
    with open(agents_path, "w", encoding="utf-8") as f:
        f.write(agents_content)
        
    return {
        "CLAUDE.md": str(claude_path),
        "AGENTS.md": str(agents_path)
    }
