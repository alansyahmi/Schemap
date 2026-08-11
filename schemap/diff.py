import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from .models import DatabaseSchemaModel

def get_cache_path() -> Path:
    p = Path(".schemap")
    p.mkdir(exist_ok=True)
    return p / "cache.json"

def save_current_state(schema: DatabaseSchemaModel):
    cache_path = get_cache_path()
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(schema.model_dump_json(indent=2))

def load_previous_state() -> DatabaseSchemaModel | None:
    cache_path = get_cache_path()
    if not cache_path.exists():
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return DatabaseSchemaModel(**data)
    except Exception:
        return None

def calculate_diff(old_schema: DatabaseSchemaModel, new_schema: DatabaseSchemaModel) -> list[str]:
    diffs, _ = calculate_detailed_diff(old_schema, new_schema)
    return diffs

def calculate_detailed_diff(old_schema: DatabaseSchemaModel, new_schema: DatabaseSchemaModel) -> Tuple[list[str], Dict[str, Any]]:
    diffs = []
    report = {
        "added_tables": [],
        "removed_tables": [],
        "added_columns": [],
        "removed_columns": [],
        "changed_columns": [],
        "added_relationships": [],
        "removed_relationships": [],
        "breaking_changes": []
    }
    
    old_tables = {t.name: t for t in old_schema.tables}
    new_tables = {t.name: t for t in new_schema.tables}
    
    # Table level
    for t in new_tables:
        if t not in old_tables:
            diffs.append(f"+ added table `{t}`")
            report["added_tables"].append(t)

    for t in old_tables:
        if t not in new_tables:
            diffs.append(f"- removed table `{t}`")
            report["removed_tables"].append(t)
            report["breaking_changes"].append(f"Removed table `{t}`")
            
    # Column level & Relationships
    for t in new_tables:
        if t in old_tables:
            old_t = old_tables[t]
            new_t = new_tables[t]
            
            old_cols = {c.name: c for c in old_t.columns}
            new_cols = {c.name: c for c in new_t.columns}
            
            for c in new_cols:
                if c not in old_cols:
                    diffs.append(f"+ added column `{t}.{c}` ({new_cols[c].data_type})")
                    report["added_columns"].append({"table": t, "column": c, "type": new_cols[c].data_type})
                else:
                    if old_cols[c].data_type != new_cols[c].data_type:
                        change_str = f"changed column `{t}.{c}` type from {old_cols[c].data_type} to {new_cols[c].data_type}"
                        diffs.append(f"~ {change_str}")
                        report["changed_columns"].append({
                            "table": t,
                            "column": c,
                            "old_type": old_cols[c].data_type,
                            "new_type": new_cols[c].data_type
                        })
                        report["breaking_changes"].append(change_str)

            for c in old_cols:
                if c not in new_cols:
                    diffs.append(f"- removed column `{t}.{c}`")
                    report["removed_columns"].append({"table": t, "column": c})
                    report["breaking_changes"].append(f"Removed column `{t}.{c}`")
                    
            # Relationships
            old_fks = {fk.column_name: fk for fk in old_t.foreign_keys}
            new_fks = {fk.column_name: fk for fk in new_t.foreign_keys}
            
            for fk_col in new_fks:
                if fk_col not in old_fks:
                    fk = new_fks[fk_col]
                    diffs.append(f"+ added relationship `{t}.{fk.column_name}` -> `{fk.foreign_table_name}.{fk.foreign_column_name}`")
                    report["added_relationships"].append({
                        "table": t,
                        "column": fk.column_name,
                        "ref_table": fk.foreign_table_name,
                        "ref_column": fk.foreign_column_name
                    })

            for fk_col in old_fks:
                if fk_col not in new_fks:
                    fk = old_fks[fk_col]
                    diffs.append(f"- removed relationship `{t}.{fk.column_name}` -> `{fk.foreign_table_name}.{fk.foreign_column_name}`")
                    report["removed_relationships"].append({
                        "table": t,
                        "column": fk.column_name,
                        "ref_table": fk.foreign_table_name,
                        "ref_column": fk.foreign_column_name
                    })
                    report["breaking_changes"].append(f"Removed relationship `{t}.{fk.column_name}` -> `{fk.foreign_table_name}.{fk.foreign_column_name}`")

    return diffs, report

