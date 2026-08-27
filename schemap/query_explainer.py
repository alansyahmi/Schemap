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

    # Build adjacency list: adj[t1] = [(t2, col1, col2, is_virtual), ...]
    adj: Dict[str, List[Tuple[str, str, str, bool]]] = {t.name: [] for t in schema.tables}
    table_names_set = {t.name for t in schema.tables}

    for t in schema.tables:
        # Physical Foreign Keys
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
                adj[t.name].append((ref_tbl, col, ref_col, False))
                adj[ref_tbl].append((t.name, ref_col, col, False))

        # Virtual Foreign Keys
        for vfk in getattr(t, "virtual_relationships", []):
            if isinstance(vfk, dict):
                ref_tbl = vfk.get("ref_table")
                col = vfk.get("column")
                ref_col = vfk.get("ref_column")
            else:
                ref_tbl = getattr(vfk, "foreign_table_name", getattr(vfk, "ref_table", None))
                col = getattr(vfk, "column_name", getattr(vfk, "column", None))
                ref_col = getattr(vfk, "foreign_column_name", getattr(vfk, "ref_column", None))

            if ref_tbl and ref_tbl in table_names_set:
                adj[t.name].append((ref_tbl, col, ref_col, True))
                adj[ref_tbl].append((t.name, ref_col, col, True))

    start_table = tables_to_join[0]
    if start_table not in table_names_set:
        raise ValueError(f"Table '{start_table}' does not exist in schema.")

    # BFS from start_table to find path visiting all target tables
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

        for neighbor, col_from, col_to, is_virt in adj.get(curr, []):
            if neighbor not in path_nodes:
                next_nodes = path_nodes + [neighbor]
                next_steps = join_steps + [(curr, col_from, neighbor, col_to, is_virt)]
                queue.append((neighbor, next_nodes, next_steps))

    if not found_path_tables:
        return {
            "tables": tables_to_join,
            "status": "disconnected",
            "sql_snippet": f"-- Warning: Could not find continuous foreign key path joining {', '.join(tables_to_join)}"
        }

    # Generate SQL
    sql_lines = [f"SELECT *", f"FROM {start_table}"]
    for from_tbl, from_col, to_tbl, to_col, is_virt in found_join_steps:
        comment = " /* Virtual/Logical Relation */" if is_virt else ""
        sql_lines.append(f"JOIN {to_tbl} ON {from_tbl}.{from_col} = {to_tbl}.{to_col}{comment}")

    return {
        "tables": tables_to_join,
        "full_path": found_path_tables,
        "status": "connected",
        "sql_snippet": "\n".join(sql_lines) + ";"
    }


def validate_query_against_schema(schema: DatabaseSchemaModel, sql: str) -> Dict[str, Any]:
    """
    Validates a SQL query string against known database tables, columns, PII policies, and query guardrails.
    Returns structured analysis with errors, warnings, tables referenced, and guardrails triggered.
    """
    import re
    errors: list[str] = []
    warnings: list[str] = []
    guardrails_triggered: list[str] = []
    
    sql_clean = sql.strip()
    sql_lower = sql_clean.lower()
    
    # 1. Identify referenced tables
    table_map = {t.name.lower(): t for t in schema.tables}
    tables_found = []
    for t_name, t_model in table_map.items():
        # Match table name as a whole word in SQL
        pattern = rf"\b{re.escape(t_name)}\b"
        if re.search(pattern, sql_lower):
            tables_found.append(t_model.name)

    # 2. Check for common hallucinated tables if FROM/JOIN used
    from_join_matches = re.findall(r"(?:from|join)\s+([a-zA-Z0-9_]+)", sql_lower)
    for candidate in from_join_matches:
        if candidate not in table_map and candidate not in ("select", "where", "group", "order", "limit"):
            errors.append(f"Unknown table `{candidate}` referenced in query. Table does not exist in schema.")

    # 3. Check for PII & sensitive columns
    for t_name in tables_found:
        t_model = table_map[t_name.lower()]
        for col in t_model.columns:
            col_lower = col.name.lower()
            if col_lower in sql_lower:
                is_pii = "pii" in [tag.lower() for tag in col.tags] or any(
                    k in col_lower for k in ["password", "secret", "token", "ssn", "cvv", "card_number"]
                )
                if is_pii:
                    warnings.append(f"Query references sensitive/PII column `{t_model.name}.{col.name}`.")

    # 4. Check Table Guardrails
    for t_name in tables_found:
        t_model = table_map[t_name.lower()]
        if t_model.guardrails:
            for g in t_model.guardrails:
                guardrails_triggered.append(f"[{t_model.name}] {g}")

        # Check soft-delete warning
        col_names = {c.name.lower() for c in t_model.columns}
        if "deleted_at" in col_names and "deleted_at" not in sql_lower:
            warnings.append(f"Table `{t_model.name}` has `deleted_at` soft-delete column but query does not filter `deleted_at IS NULL`.")

        if "is_deleted" in col_names and "is_deleted" not in sql_lower:
            warnings.append(f"Table `{t_model.name}` has `is_deleted` flag but query does not filter active records.")

    # 5. Check Global Guardrails
    if schema.global_guardrails:
        for gr in schema.global_guardrails:
            guardrails_triggered.append(f"[Global Policy] {gr}")

    valid = len(errors) == 0

    return {
        "valid": valid,
        "sql": sql_clean,
        "tables_referenced": tables_found,
        "errors": errors,
        "warnings": warnings,
        "guardrails_triggered": guardrails_triggered
    }

