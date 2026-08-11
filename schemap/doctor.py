from typing import Dict, Any, List
from .models import DatabaseSchemaModel
from .linter import calculate_score

def render_ascii_bar(score: int, width: int = 20) -> str:
    """Render a clean progress bar e.g. [##########----------] 53/100"""
    score = max(0, min(100, score))
    filled = int(round((score / 100.0) * width))
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {score}/100"

def infer_foreign_key_candidates(schema: DatabaseSchemaModel) -> List[Dict[str, Any]]:
    """
    Analyzes table columns for un-enforced foreign key candidate patterns (e.g. user_id -> users.id).
    Returns list of dicts with candidate table, column, ref_table, ref_column, confidence score, and rationale.
    """
    table_map = {t.name.lower(): t for t in schema.tables}
    table_singular_map = {}
    for tname in table_map:
        table_singular_map[tname] = tname
        if tname.endswith("s"):
            table_singular_map[tname[:-1]] = tname
        if tname.endswith("ies"):
            table_singular_map[tname[:-3] + "y"] = tname

    candidates = []
    
    for tbl in schema.tables:
        existing_fk_cols = set()
        for fk in tbl.foreign_keys:
            if isinstance(fk, dict):
                existing_fk_cols.add(fk.get("column"))
            else:
                existing_fk_cols.add(getattr(fk, "column_name", getattr(fk, "column", None)))

        for col in tbl.columns:
            if col.name in existing_fk_cols or col.primary_key:
                continue

            cname = col.name.lower()
            if cname.endswith("_id"):
                prefix = cname[:-3]
                target_table_name = None
                confidence = 0
                
                if prefix in table_map:
                    target_table_name = table_map[prefix].name
                    confidence = 95
                elif prefix in table_singular_map:
                    target_table_name = table_map[table_singular_map[prefix]].name
                    confidence = 90
                elif (prefix + "s") in table_map:
                    target_table_name = table_map[prefix + "s"].name
                    confidence = 95

                if target_table_name and target_table_name != tbl.name:
                    target_tbl_obj = next((t for t in schema.tables if t.name == target_table_name), None)
                    pk_col = "id"
                    if target_tbl_obj:
                        pks = [c.name for c in target_tbl_obj.columns if c.primary_key]
                        if pks:
                            pk_col = pks[0]
                            
                    candidates.append({
                        "table": tbl.name,
                        "column": col.name,
                        "ref_table": target_table_name,
                        "ref_column": pk_col,
                        "confidence": confidence,
                        "reason": f"Column '{col.name}' matches primary key '{pk_col}' of table '{target_table_name}'"
                    })

    return candidates

def get_doctor_report(schema_model: DatabaseSchemaModel, raw_tables: List[Dict[str, Any]], unresolved_abbrs: List[str]) -> Dict[str, Any]:
    """Generate doctor health check metrics and actionable diagnosis."""
    total_tables = len(raw_tables)
    total_fks = sum(len(t.get('foreign_keys', [])) for t in raw_tables)
    
    ai_score, categorized_issues = calculate_score(schema_model, unresolved_abbrs)
    
    fk_candidates = infer_foreign_key_candidates(schema_model)
    
    missing_desc_tables = [t.name for t in schema_model.tables if not t.description]
    yaml_desc_snippet = ""
    if missing_desc_tables:
        yaml_lines = ["schema_descriptions:"]
        for tname in missing_desc_tables[:5]:
            yaml_lines.append(f"  {tname}:")
            yaml_lines.append(f'    description: "Add clear business purpose for table {tname}"')
        yaml_desc_snippet = "\n".join(yaml_lines)

    abbrev_suggestions = {}
    for abbr in unresolved_abbrs:
        abbrev_suggestions[abbr] = abbr.capitalize()

    return {
        "status": "ok",
        "tables_count": total_tables,
        "relationships_count": total_fks,
        "ai_readiness_score": ai_score,
        "progress_bar": render_ascii_bar(ai_score),
        "issues": categorized_issues,
        "actionable_fixes": {
            "foreign_key_candidates": fk_candidates,
            "unresolved_abbreviations": abbrev_suggestions,
            "missing_descriptions_tables": missing_desc_tables,
            "config_snippet": yaml_desc_snippet
        },
        "recommendation": "Run `schemap fix --interactive` to resolve missing relationships and definitions automatically."
    }

