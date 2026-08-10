from typing import List, Dict, Any, Tuple
from .models import DatabaseSchemaModel

def _is_utility_table(name: str) -> bool:
    """Detect common audit/log/session utility tables to exclude from high central ranking."""
    lname = name.lower()
    utility_keywords = ['audit', 'log', 'session', 'token', 'cache', 'history', 'migration', 'alembic', 'schema_version']
    return any(kw in lname for kw in utility_keywords)

def calculate_central_tables(schema_model: DatabaseSchemaModel) -> List[Tuple[str, float, int]]:
    """
    Calculate table centrality rank.
    centrality_score = degree_connections * name_factor
    Returns list of tuples: (table_name, centrality_score, total_connections)
    """
    connections: Dict[str, int] = {t.name: 0 for t in schema_model.tables}
    
    for t in schema_model.tables:
        for fk in t.foreign_keys:
            ref_table = fk.get("ref_table") if isinstance(fk, dict) else (fk.ref_table if hasattr(fk, 'ref_table') else fk.foreign_table_name)
            connections[t.name] += 1
            if ref_table and ref_table in connections:
                connections[ref_table] += 1

    results = []
    for t in schema_model.tables:
        degree = connections[t.name]
        factor = 0.3 if _is_utility_table(t.name) else 1.0
        score = round(degree * factor, 2)
        results.append((t.name, score, degree))
        
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def generate_relationship_map(schema_model: DatabaseSchemaModel) -> List[str]:
    """Generate deterministic topological / flow lines showing table relationships."""
    lines = []
    seen = set()
    
    for t in schema_model.tables:
        for fk in t.foreign_keys:
            if isinstance(fk, dict):
                ref_table = fk.get("ref_table")
                col = fk.get("column")
                ref_col = fk.get("ref_column")
            else:
                ref_table = getattr(fk, "foreign_table_name", getattr(fk, "ref_table", None))
                col = getattr(fk, "column_name", getattr(fk, "column", None))
                ref_col = getattr(fk, "foreign_column_name", getattr(fk, "ref_column", None))
                
            if ref_table:
                rel_str = f"{t.name} ({col}) ──> {ref_table} ({ref_col})"
                if rel_str not in seen:
                    seen.add(rel_str)
                    lines.append(rel_str)
                    
    if not lines:
        lines.append("No explicit foreign key relationships detected.")
        
    return lines

def generate_query_examples(schema_model: DatabaseSchemaModel) -> List[str]:
    """Generate deterministic standard SQL JOIN snippets based on foreign keys."""
    queries = []
    seen_pairs = set()
    
    for t in schema_model.tables:
        for fk in t.foreign_keys:
            if isinstance(fk, dict):
                ref_table = fk.get("ref_table")
                col = fk.get("column")
                ref_col = fk.get("ref_column")
            else:
                ref_table = getattr(fk, "foreign_table_name", getattr(fk, "ref_table", None))
                col = getattr(fk, "column_name", getattr(fk, "column", None))
                ref_col = getattr(fk, "foreign_column_name", getattr(fk, "ref_column", None))
                
            if ref_table:
                pair = tuple(sorted([t.name, ref_table]))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    sql = (
                        f"-- Join {t.name} with {ref_table}\n"
                        f"SELECT *\n"
                        f"FROM {t.name}\n"
                        f"JOIN {ref_table} ON {t.name}.{col} = {ref_table}.{ref_col};"
                    )
                    queries.append(sql)
                    
    return queries

def generate_database_context(schema_model: DatabaseSchemaModel) -> str:
    """Generate the full schemap_database_context.md content."""
    total_tables = len(schema_model.tables)
    total_cols = sum(len(t.columns) for t in schema_model.tables)
    total_fks = sum(len(t.foreign_keys) for t in schema_model.tables)
    
    out = []
    out.append("# Database Context Engine Output\n")
    out.append("## Database Overview\n")
    out.append(f"- **Total Tables**: {total_tables}")
    out.append(f"- **Total Columns**: {total_cols}")
    out.append(f"- **Total Foreign Key Relationships**: {total_fks}\n")
    
    # Schema Relationship Map
    out.append("## Schema Relationship Map\n")
    out.append("```")
    rel_map = generate_relationship_map(schema_model)
    out.extend(rel_map)
    out.append("```\n")
    
    # Central Tables
    out.append("## Central Tables\n")
    central_tables = calculate_central_tables(schema_model)
    top_central = [ct for ct in central_tables if ct[2] > 0][:5]
    if not top_central:
        top_central = central_tables[:5]
        
    for name, score, degree in top_central:
        t_model = next((t for t in schema_model.tables if t.name == name), None)
        desc = t_model.description if t_model and t_model.description else "No description available."
        out.append(f"### `{name}`")
        out.append(f"- **Connectivity Score**: {score} ({degree} connections)")
        out.append(f"- **Description**: {desc}")
        if t_model:
            pk_cols = [c.name for c in t_model.columns if c.primary_key]
            out.append(f"- **Primary Key(s)**: {', '.join(pk_cols) if pk_cols else 'None'}\n")
            
    # Query Examples
    out.append("## Query Examples\n")
    query_examples = generate_query_examples(schema_model)
    if query_examples:
        for q in query_examples[:5]:
            out.append("```sql")
            out.append(q)
            out.append("```\n")
    else:
        out.append("_No foreign key relationships found to auto-generate standard JOIN queries._\n")
        
    return "\n".join(out)
