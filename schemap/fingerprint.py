import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple
from .models import DatabaseSchemaModel

def get_fingerprint_path() -> Path:
    p = Path(".schemap")
    p.mkdir(exist_ok=True)
    return p / "fingerprint.json"

def calculate_schema_fingerprint(schema: DatabaseSchemaModel) -> str:
    """
    Calculate a deterministic SHA256 fingerprint hash of the schema's structure
    (table names, column names, column data types, primary keys, foreign keys).
    """
    elements = []
    # Sort tables by name for determinism
    sorted_tables = sorted(schema.tables, key=lambda t: t.name)
    for t in sorted_tables:
        elements.append(f"TABLE:{t.name}")
        sorted_cols = sorted(t.columns, key=lambda c: c.name)
        for c in sorted_cols:
            elements.append(f"COL:{t.name}.{c.name}:{c.data_type}:{c.primary_key}")
        sorted_fks = sorted(
            t.foreign_keys,
            key=lambda fk: (
                fk.get('column') if isinstance(fk, dict) else fk.column_name,
                fk.get('ref_table') if isinstance(fk, dict) else fk.foreign_table_name,
                fk.get('ref_column') if isinstance(fk, dict) else fk.foreign_column_name
            )
        )
        for fk in sorted_fks:
            if isinstance(fk, dict):
                col = fk.get('column')
                ref_tbl = fk.get('ref_table')
                ref_col = fk.get('ref_column')
            else:
                col = getattr(fk, 'column_name', getattr(fk, 'column', None))
                ref_tbl = getattr(fk, 'foreign_table_name', getattr(fk, 'ref_table', None))
                ref_col = getattr(fk, 'foreign_column_name', getattr(fk, 'ref_column', None))
            elements.append(f"FK:{t.name}.{col}->{ref_tbl}.{ref_col}")

    payload = "\n".join(elements).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def get_cached_fingerprint() -> str | None:
    path = get_fingerprint_path()
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("fingerprint")
    except Exception:
        return None

def save_fingerprint(fingerprint: str):
    path = get_fingerprint_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"fingerprint": fingerprint}, f, indent=2)
