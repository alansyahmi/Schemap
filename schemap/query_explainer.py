from typing import List, Dict, Any, Tuple
from collections import deque
from .models import DatabaseSchemaModel
from .context import calculate_central_tables

def explain_table(schema: DatabaseSchemaModel, table_name: str) -> Dict[str, Any]:
    """
    Returns structured explanation metrics and breakdown for a target table.
    """
    target = next((t for t in schema.tables if t.name.lower() == table_name.lower()), None)
    if not target:
        raise ValueError(f"Table '{table_name}' not found in database schema.")

    centrality_rank = calculate_central_tables(schema)
    centrality_tuple = next((c for c in centrality_rank if c[0] == target.name), (target.name, 0.0, 0))

    # Calculate incoming relationships
    incoming_fks = []
    for other in schema.tables:
        if other.name == target.name:
            continue
        for fk in other.foreign_keys:
            if isinstance(fk, dict):
                ref_tbl = fk.get("ref_table")
                col = fk.get("column")
                ref_col = fk.get("ref_column")
            else:
                ref_tbl = getattr(fk, "foreign_table_name", getattr(fk, "ref_table", None))
                col = getattr(fk, "column_name", getattr(fk, "column", None))
                ref_col = getattr(fk, "foreign_column_name", getattr(fk, "ref_column", None))

            if ref_tbl == target.name:
                incoming_fks.append({
                    "from_table": other.name,
                    "from_column": col,
                    "to_column": ref_col
                })

    outgoing_fks = []
    for fk in target.foreign_keys:
        if isinstance(fk, dict):
            ref_tbl = fk.get("ref_table")
            col = fk.get("column")
            ref_col = fk.get("ref_column")
        else:
            ref_tbl = getattr(fk, "foreign_table_name", getattr(fk, "ref_table", None))
            col = getattr(fk, "column_name", getattr(fk, "column", None))
            ref_col = getattr(fk, "foreign_column_name", getattr(fk, "ref_column", None))

        outgoing_fks.append({
            "column": col,
            "ref_table": ref_tbl,
            "ref_column": ref_col
        })

    cols_info = []
    for c in target.columns:
        cols_info.append({
            "name": c.name,
            "data_type": c.data_type,
            "primary_key": c.primary_key,
            "nullable": c.is_nullable,
            "description": c.description or ""
        })

    return {
        "table": target.name,
        "business_name": target.business_name or "",
        "description": target.description or "No description provided.",
        "centrality_score": centrality_tuple[1],
        "degree_connections": centrality_tuple[2],
        "columns_count": len(target.columns),
        "columns": cols_info,
        "outgoing_relationships": outgoing_fks,
        "incoming_relationships": incoming_fks
    }

def find_join_path(schema: DatabaseSchemaModel, tables_to_join: List[str]) -> Dict[str, Any]:
    """
    Finds the shortest foreign-key join path across multiple tables and generates valid SQL.
    """
    if not tables_to_join:
        raise ValueError("Must provide at least 2 table names to calculate a join path.")

    # Build adjacency list: adj[t1] = [(t2, col1, col2), ...]
    adj: Dict[str, List[Tuple[str, str, str]]] = {t.name: [] for t in schema.tables}
    table_names_set = {t.name for t in schema.tables}

    for t in schema.tables:
        for fk in t.foreign_keys:
            if isinstance(fk, dict):
                ref_tbl = fk.get("ref_table")
                col = fk.get("column")
                ref_col = fk.get("ref_column")
            else:
                ref_tbl = getattr(fk, "foreign_table_name", getattr(fk, "ref_table", None))
                col = getattr(fk, "column_name", getattr(fk, "column", None))
                ref_col = getattr(fk, "foreign_column_name", getattr(fk, "ref_column", None))

            if ref_tbl and ref_tbl in table_names_set:
                adj[t.name].append((ref_tbl, col, ref_col))
                adj[ref_tbl].append((t.name, ref_col, col))

    start_table = tables_to_join[0]
    if start_table not in table_names_set:
        raise ValueError(f"Table '{start_table}' does not exist in schema.")

    # BFS from start_table to find path visiting all target tables
    # Path: list of (current_table, join_condition_str_or_None)
    visited_states = set()
    queue = deque([(start_table, [start_table], [])])

    found_path_tables = None
    found_join_steps = None

    target_set = set(tables_to_join)

    while queue:
        curr, path_nodes, join_steps = queue.popleft()

        if target_set.issubset(set(path_nodes)):
            found_path_tables = path_nodes
            found_join_steps = join_steps
            break

        for neighbor, col_from, col_to in adj.get(curr, []):
            if neighbor not in path_nodes:
                next_nodes = path_nodes + [neighbor]
                next_steps = join_steps + [(curr, col_from, neighbor, col_to)]
                queue.append((neighbor, next_nodes, next_steps))

    if not found_path_tables:
        # Fallback to direct pair searches if global tree BFS didn't complete
        return {
            "tables": tables_to_join,
            "status": "disconnected",
            "sql_snippet": f"-- Warning: Could not find continuous foreign key path joining {', '.join(tables_to_join)}"
        }

    # Generate SQL
    sql_lines = [f"SELECT *", f"FROM {start_table}"]
    for from_tbl, from_col, to_tbl, to_col in found_join_steps:
        sql_lines.append(f"JOIN {to_tbl} ON {from_tbl}.{from_col} = {to_tbl}.{to_col}")

    return {
        "tables": tables_to_join,
        "full_path": found_path_tables,
        "status": "connected",
        "sql_snippet": "\n".join(sql_lines) + ";"
    }
