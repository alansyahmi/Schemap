import random
import sqlite3
from typing import List, Dict, Any
from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel

def generate_synthetic_schema_models(num_tables: int = 100, fk_density: float = 0.3) -> DatabaseSchemaModel:
    """
    Generate an in-memory DatabaseSchemaModel with `num_tables` tables,
    realistic columns, foreign keys, circular dependencies, and utility log tables.
    """
    tables: List[TableModel] = []
    table_names = [f"table_{i}" for i in range(num_tables)]
    
    # Introduce domain table names and utility table names
    special_names = ["users", "accounts", "orders", "products", "audit_logs", "session_tokens", "schema_migrations"]
    for i in range(min(len(special_names), num_tables)):
        table_names[i] = special_names[i]
        
    for i, name in enumerate(table_names):
        cols = [
            ColumnModel(name="id", data_type="INTEGER", primary_key=True),
            ColumnModel(name="created_at", data_type="TIMESTAMP"),
            ColumnModel(name=f"{name}_val", data_type="VARCHAR")
        ]
        
        # Add random columns
        num_cols = random.randint(3, 15)
        for c in range(num_cols):
            cols.append(ColumnModel(name=f"col_{c}", data_type="VARCHAR"))
            
        fks: List[ForeignKeyModel] = []
        # Add foreign keys pointing to previous or self tables (including circular dependencies)
        if i > 0 and random.random() < fk_density:
            target_table = random.choice(table_names[:i])
            fks.append(ForeignKeyModel(column_name=f"{target_table}_id", foreign_table_name=target_table, foreign_column_name="id"))
            cols.append(ColumnModel(name=f"{target_table}_id", data_type="INTEGER"))
            
        # Add self-referencing FK to test circular tree logic
        if random.random() < 0.1:
            fks.append(ForeignKeyModel(column_name="parent_id", foreign_table_name=name, foreign_column_name="id"))
            cols.append(ColumnModel(name="parent_id", data_type="INTEGER"))
            
        tables.append(TableModel(name=name, columns=cols, foreign_keys=fks))
        
    # Introduce deliberate circular dependency: table_A -> table_B -> table_A
    if num_tables >= 2:
        t0 = tables[0]
        t1 = tables[1]
        t0.foreign_keys.append(ForeignKeyModel(column_name=f"{t1.name}_id", foreign_table_name=t1.name, foreign_column_name="id"))
        t1.foreign_keys.append(ForeignKeyModel(column_name=f"{t0.name}_id", foreign_table_name=t0.name, foreign_column_name="id"))
        
    return DatabaseSchemaModel(tables=tables)

def create_synthetic_sqlite_db(db_path: str, num_tables: int = 50):
    """Create a physical SQLite database populated with `num_tables` tables for end-to-end extraction testing."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for i in range(num_tables):
        tname = f"ent_table_{i}"
        cursor.execute(f"CREATE TABLE {tname} (id INTEGER PRIMARY KEY, val TEXT, created_at TIMESTAMP);")
        
    conn.commit()
    conn.close()
