import json
from pathlib import Path
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
    diffs = []
    
    old_tables = {t.name: t for t in old_schema.tables}
    new_tables = {t.name: t for t in new_schema.tables}
    
    # Table level
    for t in new_tables:
        if t not in old_tables:
            diffs.append(f"+ added table `{t}`")
    for t in old_tables:
        if t not in new_tables:
            diffs.append(f"- removed table `{t}`")
            
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
                else:
                    if old_cols[c].data_type != new_cols[c].data_type:
                        diffs.append(f"~ changed column `{t}.{c}` type from {old_cols[c].data_type} to {new_cols[c].data_type}")
            for c in old_cols:
                if c not in new_cols:
                    diffs.append(f"- removed column `{t}.{c}`")
                    
            # Relationships
            old_fks = {fk.column_name: fk for fk in old_t.foreign_keys}
            new_fks = {fk.column_name: fk for fk in new_t.foreign_keys}
            
            for fk_col in new_fks:
                if fk_col not in old_fks:
                    fk = new_fks[fk_col]
                    diffs.append(f"+ added relationship `{t}.{fk.column_name}` -> `{fk.foreign_table_name}.{fk.foreign_column_name}`")
            for fk_col in old_fks:
                if fk_col not in new_fks:
                    fk = old_fks[fk_col]
                    diffs.append(f"- removed relationship `{t}.{fk.column_name}` -> `{fk.foreign_table_name}.{fk.foreign_column_name}`")

    return diffs
