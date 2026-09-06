"""
Schemap CI/CD AI Quality Gate & Governance Reporting Engine.

Evaluates database schemas in CI/CD pipelines:
1. Calculates AI Readiness Score via linter & diagnostic rules.
2. Checks for breaking schema mutations (dropped tables/columns, removed FKs, type mismatches).
3. Performs Blast-Radius Analysis on affected tables and agent workflows.
4. Generates rich Markdown Pull Request Quality Reports & Step Summaries.
5. Enforces minimum score threshold and fail-on-breaking policies.
"""

from typing import Dict, Any, List, Tuple
from .models import DatabaseSchemaModel
from .linter import calculate_score
from .diff import calculate_detailed_diff, load_previous_state, save_current_state


class GateResult:
    def __init__(
        self,
        passed: bool,
        score: int,
        min_score: int,
        issues: List[str],
        breaking_changes: List[str],
        diff_summary: Dict[str, Any],
        failure_reasons: List[str],
        previous_score: int | None = None,
        score_delta: int | None = None,
        metrics: Dict[str, Any] | None = None,
        blast_radius: Dict[str, Any] | None = None,
    ):
        self.passed = passed
        self.score = score
        self.min_score = min_score
        self.issues = issues
        self.breaking_changes = breaking_changes
        self.diff_summary = diff_summary
        self.failure_reasons = failure_reasons
        self.previous_score = previous_score
        self.score_delta = score_delta
        self.metrics = metrics or {}
        self.blast_radius = blast_radius or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "min_score": self.min_score,
            "previous_score": self.previous_score,
            "score_delta": self.score_delta,
            "metrics": self.metrics,
            "issues": self.issues,
            "breaking_changes": self.breaking_changes,
            "blast_radius": self.blast_radius,
            "diff_summary": self.diff_summary,
            "failure_reasons": self.failure_reasons,
        }


def _analyze_blast_radius(
    current_schema: DatabaseSchemaModel,
    diff_report: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes blast radius impact of schema modifications on dependent tables & agent queries.
    """
    impacted_tables: set[str] = set()
    high_risk_items: list[str] = []
    medium_risk_items: list[str] = []
    low_risk_items: list[str] = []

    # Map current foreign key dependents
    dependents_map: dict[str, list[str]] = {}
    for table in current_schema.tables:
        for fk in table.foreign_keys:
            dependents_map.setdefault(fk.foreign_table_name, []).append(table.name)

    # 1. Removed tables (High Risk)
    for t in diff_report.get("removed_tables", []):
        impacted_tables.add(t)
        deps = dependents_map.get(t, [])
        if deps:
            high_risk_items.append(f"Dropped table `{t}` breaks dependent foreign keys in: `{', '.join(deps)}`")
        else:
            high_risk_items.append(f"Dropped table `{t}` entirely removed from agent context")

    # 2. Changed column types (High/Medium Risk)
    for c in diff_report.get("changed_columns", []):
        t = c["table"]
        col = c["column"]
        impacted_tables.add(t)
        high_risk_items.append(f"Type mutation on `{t}.{col}` ({c['old_type']} -> {c['new_type']}) may cause SQL casting/agent generation failures")

    # 3. Removed columns (High Risk)
    for c in diff_report.get("removed_columns", []):
        t = c["table"]
        col = c["column"]
        impacted_tables.add(t)
        high_risk_items.append(f"Removed column `{t}.{col}` invalidates active agent queries targeting this field")

    # 4. Removed relationships (Medium Risk)
    for r in diff_report.get("removed_relationships", []):
        t = r["table"]
        impacted_tables.add(t)
        impacted_tables.add(r["ref_table"])
        medium_risk_items.append(f"Severed JOIN path: `{t}.{r['column']}` ↛ `{r['ref_table']}.{r['ref_column']}`")

    # 5. Added tables / columns (Low Risk / Expansion)
    for t in diff_report.get("added_tables", []):
        impacted_tables.add(t)
        low_risk_items.append(f"Added new table `{t}` (AI context needs updated descriptions)")

    for c in diff_report.get("added_columns", []):
        impacted_tables.add(c["table"])
        low_risk_items.append(f"Added column `{c['table']}.{c['column']}` ({c['type']})")

    # Overall risk level
    if high_risk_items:
        severity = "HIGH"
    elif medium_risk_items:
        severity = "MEDIUM"
    elif low_risk_items:
        severity = "LOW"
    else:
        severity = "NONE"

    return {
        "severity": severity,
        "impacted_tables_count": len(impacted_tables),
        "impacted_tables": sorted(list(impacted_tables)),
        "high_risk_items": high_risk_items,
        "medium_risk_items": medium_risk_items,
        "low_risk_items": low_risk_items,
    }


def evaluate_gate(
    current_schema: DatabaseSchemaModel,
    previous_schema: DatabaseSchemaModel | None = None,
    min_score: int = 80,
    fail_on_breaking: bool = False,
    unresolved_abbrs: List[str] | None = None
) -> GateResult:
    """
    Evaluates current schema against quality thresholds and breaking change rules.
    """
    if unresolved_abbrs is None:
        unresolved_abbrs = []

    # 1. Calculate AI Readiness Score & Metrics
    score, issues = calculate_score(current_schema, unresolved_abbrs)
    
    total_tables = len(current_schema.tables)
    total_columns = sum(len(t.columns) for t in current_schema.tables)
    tables_with_desc = sum(1 for t in current_schema.tables if t.description)
    tables_with_pk = sum(1 for t in current_schema.tables if any(c.primary_key for c in t.columns))
    total_fks = sum(len(t.foreign_keys) for t in current_schema.tables)

    metrics = {
        "total_tables": total_tables,
        "total_columns": total_columns,
        "documented_tables": tables_with_desc,
        "documentation_coverage_pct": round((tables_with_desc / total_tables * 100) if total_tables > 0 else 0, 1),
        "primary_key_coverage_pct": round((tables_with_pk / total_tables * 100) if total_tables > 0 else 0, 1),
        "total_foreign_keys": total_fks,
        "unresolved_abbr_count": len(unresolved_abbrs),
    }

    # 2. Calculate Diffs & Breaking Changes against previous state
    breaking_changes = []
    diff_report: Dict[str, Any] = {
        "added_tables": [],
        "removed_tables": [],
        "added_columns": [],
        "removed_columns": [],
        "changed_columns": [],
        "added_relationships": [],
        "removed_relationships": [],
        "breaking_changes": []
    }
    previous_score = None
    score_delta = None

    if previous_schema is not None:
        prev_score, _ = calculate_score(previous_schema, [])
        previous_score = prev_score
        score_delta = score - prev_score
        _, diff_report = calculate_detailed_diff(previous_schema, current_schema)
        breaking_changes = diff_report.get("breaking_changes", [])

    # 3. Blast Radius Analysis
    blast_radius = _analyze_blast_radius(current_schema, diff_report)

    # 4. Evaluate Pass/Fail
    failure_reasons = []
    if score < min_score:
        failure_reasons.append(
            f"AI Readiness Score ({score}/100) is below the required threshold of {min_score}/100."
        )

    if fail_on_breaking and breaking_changes:
        failure_reasons.append(
            f"Found {len(breaking_changes)} breaking schema changes: {'; '.join(breaking_changes[:3])}"
            + (f" and {len(breaking_changes) - 3} more" if len(breaking_changes) > 3 else "")
        )

    passed = len(failure_reasons) == 0

    return GateResult(
        passed=passed,
        score=score,
        min_score=min_score,
        issues=issues,
        breaking_changes=breaking_changes,
        diff_summary=diff_report,
        failure_reasons=failure_reasons,
        previous_score=previous_score,
        score_delta=score_delta,
        metrics=metrics,
        blast_radius=blast_radius
    )


def generate_gate_markdown_report(result: GateResult, project_name: str | None = None) -> str:
    """
    Generates a high-impact, rich Markdown report suitable for GitHub PR comments and CI step summaries.
    """
    proj_header = f" for **{project_name}**" if project_name else ""
    
    # Status Banner & Badges
    if result.passed:
        status_badge = "![Quality Gate Passed](https://img.shields.io/badge/Schemap%20AI%20Gate-PASSED-brightgreen?style=for-the-badge&logo=checkmarx)"
        status_title = f"### 🟢 Schemap AI Quality Gate: PASSED{proj_header}"
    else:
        status_badge = "![Quality Gate Blocked](https://img.shields.io/badge/Schemap%20AI%20Gate-BLOCKED-crimson?style=for-the-badge&logo=githubactions)"
        status_title = f"### 🔴 Schemap AI Quality Gate: BLOCKED{proj_header}"

    score_delta_str = ""
    if result.score_delta is not None:
        if result.score_delta > 0:
            score_delta_str = f" `+{result.score_delta}` 📈"
        elif result.score_delta < 0:
            score_delta_str = f" `{result.score_delta}` 📉"
        else:
            score_delta_str = " `±0` (Unchanged)"

    lines: list[str] = [
        status_title,
        "",
        status_badge,
        "",
    ]

    # Gate Failures Alert if failed
    if not result.passed:
        lines.extend([
            "> [!CAUTION]",
            "> **Pull Request Gate Violations**:",
        ])
        for reason in result.failure_reasons:
            lines.append(f"> - ❌ {reason}")
        lines.append("")

    # Scorecard Table
    m = result.metrics
    lines.extend([
        "#### 📊 AI Readiness & Schema Governance Scorecard",
        "",
        "| Metric | Current Value | Target / Status |",
        "| :--- | :--- | :--- |",
        f"| **AI Readiness Score** | **`{result.score}/100`**{score_delta_str} | Threshold: `≥ {result.min_score}/100` |",
        f"| **Documentation Coverage** | `{m.get('documented_tables', 0)} / {m.get('total_tables', 0)}` tables ({m.get('documentation_coverage_pct', 0)}%) | Recommended: `100%` |",
        f"| **Primary Key Integrity** | `{m.get('primary_key_coverage_pct', 0)}%` | Required: `100%` |",
        f"| **Explicit Foreign Keys** | `{m.get('total_foreign_keys', 0)}` relationships | Relational Graph Linkage |",
        f"| **Ambiguous Abbreviations** | `{m.get('unresolved_abbr_count', 0)}` unresolved | Clean Domain Semantics |",
        "",
    ])

    # Blast Radius & Risk Assessment
    br = result.blast_radius
    if br and br.get("severity") != "NONE":
        sev = br.get("severity", "LOW")
        sev_icon = "🔴" if sev == "HIGH" else ("🟡" if sev == "MEDIUM" else "🟢")
        lines.extend([
            f"#### 💥 Blast Radius & Agent Impact Analysis ({sev_icon} Risk: `{sev}`)",
            "",
            f"- **Impacted Database Entities**: `{br.get('impacted_tables_count', 0)}` tables modified or affected.",
        ])

        if br.get("high_risk_items"):
            lines.append("- **Critical Risks (Agent Query Breaking)**:")
            for item in br["high_risk_items"]:
                lines.append(f"  - ⚠️ {item}")

        if br.get("medium_risk_items"):
            lines.append("- **Relationship Changes**:")
            for item in br["medium_risk_items"]:
                lines.append(f"  - 🔄 {item}")

        if br.get("low_risk_items"):
            lines.append("- **Schema Expansions**:")
            for item in br["low_risk_items"]:
                lines.append(f"  - ➕ {item}")
        lines.append("")

    # Schema Diffs Details
    diff = result.diff_summary
    has_diffs = any(diff.get(k) for k in ["added_tables", "removed_tables", "added_columns", "removed_columns", "changed_columns", "added_relationships", "removed_relationships"])
    if has_diffs:
        lines.extend([
            "<details>",
            "<summary>🔍 <b>View Detailed Schema Mutations</b></summary>",
            "",
            "| Change Type | Entity / Details |",
            "| :--- | :--- |",
        ])
        for t in diff.get("added_tables", []):
            lines.append(f"| 🟢 Added Table | `{t}` |")
        for t in diff.get("removed_tables", []):
            lines.append(f"| 🔴 Dropped Table | `{t}` |")
        for c in diff.get("added_columns", []):
            lines.append(f"| 🟢 Added Column | `{c['table']}.{c['column']}` (`{c['type']}`) |")
        for c in diff.get("removed_columns", []):
            lines.append(f"| 🔴 Dropped Column | `{c['table']}.{c['column']}` |")
        for c in diff.get("changed_columns", []):
            lines.append(f"| 🟡 Changed Column Type | `{c['table']}.{c['column']}`: `{c['old_type']}` → `{c['new_type']}` |")
        for r in diff.get("added_relationships", []):
            lines.append(f"| 🔗 Added Foreign Key | `{r['table']}.{r['column']}` → `{r['ref_table']}.{r['ref_column']}` |")
        for r in diff.get("removed_relationships", []):
            lines.append(f"| ✂️ Removed Foreign Key | `{r['table']}.{r['column']}` ↛ `{r['ref_table']}.{r['ref_column']}` |")
        lines.extend([
            "",
            "</details>",
            "",
        ])

    # Remediation Suggestions
    if result.issues:
        lines.extend([
            "#### 💡 Recommended Actions to Raise AI Readiness Score",
            "",
        ])
        for issue in result.issues:
            lines.append(f"- {issue}")
        lines.extend([
            "",
            "> ⚡ **Tip**: Run `schemap fix` or update `schemap.yaml` descriptions to resolve these issues and update your deterministic agent rules.",
            "",
        ])

    lines.extend([
        "---",
        "<sub>Powered by <a href='https://schemap-tool.pages.dev'>Schemap</a> — The AI Database Context & Governance Control Plane</sub>",
        ""
    ])

    return "\n".join(lines)

