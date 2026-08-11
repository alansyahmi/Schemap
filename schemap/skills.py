from pathlib import Path
from typing import List, Union
from .agents import parse_targets

SKILL_TEMPLATE = """---
name: schemap
description: AI Database Context & Schema Guardrails Skill for Schemap-managed projects.
---

# Schemap AI Database Agent Skill

Use this skill whenever reading, querying, or writing SQL queries, migrations, or database-related business code in this repository.

## Core Rules & Execution Flow

1. **Inspect Schema Context First**:
   - Before writing any SQL query or database migration, ALWAYS read the database context in `AGENTS.md` or `schemap_database_context.md`.
   - Never invent or guess table names, column names, or foreign key join paths.

2. **Enforce Verified Foreign Key Joins**:
   - Only perform multi-table JOINs using verified foreign key relationships defined in `AGENTS.md`.
   - You can run `schemap join <table1> <table2>` to auto-generate valid SQL JOIN clauses.

3. **Verify Schema Post-Migration**:
   - After writing or applying database migrations, run `schemap diff` to inspect changes.
   - Run `schemap sync` to automatically update project context files (`AGENTS.md`, `CLAUDE.md`).

4. **Flag Ambiguous Business Logic**:
   - If column descriptions or business semantics are missing or ambiguous, flag them for review or run `schemap doctor` / `schemap fix --interactive` rather than inventing semantics.
"""

def generate_schemap_skill_md() -> str:
    """Generate the content of the agent-native schemap skill."""
    return SKILL_TEMPLATE

def install_agent_skills(targets: Union[str, List[str], None] = None, base_dir: str = ".") -> List[str]:
    """
    Installs the schemap AI skill across target agent frameworks (.codex, .claude, .cursor).
    Returns list of written file paths.
    """
    target_set = parse_targets(targets)
    base = Path(base_dir)
    skill_content = generate_schemap_skill_md()

    installed_paths = []

    if "codex" in target_set or "all" in target_set or "agents" in target_set:
        codex_path = base / ".codex" / "skills" / "schemap" / "SKILL.md"
        codex_path.parent.mkdir(parents=True, exist_ok=True)
        with open(codex_path, "w", encoding="utf-8") as f:
            f.write(skill_content)
        installed_paths.append(str(codex_path))

    if "claude" in target_set or "all" in target_set:
        claude_path = base / ".claude" / "skills" / "schemap" / "SKILL.md"
        claude_path.parent.mkdir(parents=True, exist_ok=True)
        with open(claude_path, "w", encoding="utf-8") as f:
            f.write(skill_content)
        installed_paths.append(str(claude_path))

    if "cursor" in target_set or "all" in target_set:
        cursor_path = base / ".cursor" / "rules" / "schemap.mdc"
        cursor_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cursor_path, "w", encoding="utf-8") as f:
            f.write(skill_content)
        installed_paths.append(str(cursor_path))

    return installed_paths
