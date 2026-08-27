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
    """Generate deterministic topological / flow lines showing table relationships including physical and virtual FKs."""
    lines = []
    seen = set()
    
    # 1. Physical Foreign Keys
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

    # 2. Virtual / Logical Foreign Keys
    for t in schema_model.tables:
        for vfk in getattr(t, "virtual_relationships", []):
            if isinstance(vfk, dict):
                ref_table = vfk.get("ref_table")
                col = vfk.get("column")
                ref_col = vfk.get("ref_column")
            else:
                ref_table = getattr(vfk, "foreign_table_name", getattr(vfk, "ref_table", None))
                col = getattr(vfk, "column_name", getattr(vfk, "column", None))
                ref_col = getattr(vfk, "foreign_column_name", getattr(vfk, "ref_column", None))
                
            if ref_table:
                rel_str = f"{t.name} ({col}) ──┄> {ref_table} ({ref_col}) [Virtual]"
                if rel_str not in seen:
                    seen.add(rel_str)
                    lines.append(rel_str)
                    
    if not lines:
        lines.append("No foreign key or virtual relationships detected.")
        
    return lines

def generate_query_examples(schema_model: DatabaseSchemaModel) -> List[str]:
    """Generate deterministic standard SQL JOIN snippets based on foreign keys and virtual relations."""
    queries = []
    seen_pairs = set()
    
    for t in schema_model.tables:
        all_rels = list(t.foreign_keys) + list(getattr(t, "virtual_relationships", []))
        for fk in all_rels:
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
                    is_virtual = fk in getattr(t, "virtual_relationships", [])
                    label = "Virtual/Logical " if is_virtual else ""
                    sql = (
                        f"-- {label}Join {t.name} with {ref_table}\n"
                        f"SELECT *\n"
                        f"FROM {t.name}\n"
                        f"JOIN {ref_table} ON {t.name}.{col} = {ref_table}.{ref_col};"
                    )
                    queries.append(sql)
                    
    return queries

def sanitize_schema_for_llm(schema_model: DatabaseSchemaModel) -> Tuple[DatabaseSchemaModel, int]:
    """
    Sanitize sensitive columns (PII, secrets, credentials, tokens) before LLM emission.
    Returns (sanitized_model, sanitized_column_count).
    """
    sensitive_keywords = {
        'password', 'passwd', 'secret', 'token', 'ssn', 'credit_card', 'card_number',
        'cvv', 'cvc', 'auth_key', 'private_key', 'api_key', 'dob', 'date_of_birth',
        'jwt', 'session_id', 'access_token', 'refresh_token', 'pin', 'salt'
    }
    
    sanitized_tables = []
    total_sanitized = 0
    
    for t in schema_model.tables:
        sanitized_cols = []
        for c in t.columns:
            col_lower = c.name.lower()
            is_sensitive = any(kw in col_lower for kw in sensitive_keywords) or ("pii" in [tag.lower() for tag in getattr(c, "tags", [])])
            if is_sensitive:
                total_sanitized += 1
                # Redact sensitive column details
                sanitized_cols.append(c.model_copy(update={
                    "description": "[REDACTED_PII: Sensitive field masked for AI safety]",
                    "business_name": "[CONFIDENTIAL]"
                }))
            else:
                sanitized_cols.append(c)
        sanitized_tables.append(t.model_copy(update={"columns": sanitized_cols}))
        
    return DatabaseSchemaModel(
        tables=sanitized_tables,
        common_journeys=schema_model.common_journeys,
        glossary=schema_model.glossary,
        global_guardrails=schema_model.global_guardrails
    ), total_sanitized

def filter_schema_by_scope(schema_model: DatabaseSchemaModel, scope: str = "all") -> DatabaseSchemaModel:
    """Filter tables in schema model based on role-scoped profile (analytics, backend, core, or custom keyword)."""
    if not scope or scope.lower() == "all":
        return schema_model
    
    scope_lower = scope.lower()
    filtered_tables = []
    
    if scope_lower == "analytics":
        analytics_keywords = {'fact', 'dim', 'analytics', 'stats', 'metrics', 'summary', 'report', 'history', 'snapshot', 'sales', 'revenue', 'aggregates'}
        for t in schema_model.tables:
            name_lower = t.name.lower()
            tags_lower = [tag.lower() for tag in getattr(t, "tags", [])]
            if any(kw in name_lower for kw in analytics_keywords) or "analytics" in tags_lower:
                filtered_tables.append(t)
    elif scope_lower == "backend":
        backend_keywords = {'user', 'users', 'auth', 'session', 'account', 'order', 'payment', 'transaction', 'role', 'permission', 'profile'}
        for t in schema_model.tables:
            name_lower = t.name.lower()
            tags_lower = [tag.lower() for tag in getattr(t, "tags", [])]
            if any(kw in name_lower for kw in backend_keywords) or "backend" in tags_lower or "core" in tags_lower:
                filtered_tables.append(t)
    elif scope_lower == "core":
        central = calculate_central_tables(schema_model)
        top_names = {c[0] for c in central if c[2] > 0}
        if not top_names:
            top_names = {c[0] for c in central[:5]}
        for t in schema_model.tables:
            if t.name in top_names or "core" in [tag.lower() for tag in getattr(t, "tags", [])]:
                filtered_tables.append(t)
    else:
        for t in schema_model.tables:
            if scope_lower in t.name.lower() or scope_lower in [tag.lower() for tag in getattr(t, "tags", [])]:
                filtered_tables.append(t)
                
    if not filtered_tables:
        filtered_tables = schema_model.tables

    return DatabaseSchemaModel(
        tables=filtered_tables,
        common_journeys=schema_model.common_journeys,
        glossary=schema_model.glossary,
        global_guardrails=schema_model.global_guardrails
    )

def generate_database_context(schema_model: DatabaseSchemaModel, scope: str = "all", sanitize: bool = False) -> str:
    """Generate the full schemap_database_context.md content supporting semantics, glossary, guardrails, and PII sanitization."""
    sanitized_count = 0
    if sanitize:
        schema_model, sanitized_count = sanitize_schema_for_llm(schema_model)

    model_to_use = filter_schema_by_scope(schema_model, scope=scope)
    total_tables = len(model_to_use.tables)
    total_cols = sum(len(t.columns) for t in model_to_use.tables)
    total_fks = sum(len(t.foreign_keys) for t in model_to_use.tables)
    total_vfks = sum(len(getattr(t, "virtual_relationships", [])) for t in model_to_use.tables)
    
    out = []
    out.append("# Database Context Engine Output\n")
    if sanitize and sanitized_count > 0:
        out.append(f"> 🛡️ **Security Guardrail Active**: `{sanitized_count}` sensitive/PII columns automatically redacted.\n")
    if scope and scope.lower() != "all":
        out.append(f"> **Context Scope**: `{scope.lower()}` profile ({total_tables} focused tables)\n")
        
    out.append("## Database Overview\n")
    out.append(f"- **Total Tables**: {total_tables}")
    out.append(f"- **Total Columns**: {total_cols}")
    out.append(f"- **Physical Foreign Key Relationships**: {total_fks}")
    if total_vfks > 0:
        out.append(f"- **Virtual / Logical Relationships**: {total_vfks}")
    out.append("")

    # Business Glossary
    if model_to_use.glossary:
        out.append("## Business Glossary & Domain Semantics\n")
        out.append("| Business Term | Canonical Definition / Calculation Formula |")
        out.append("| :--- | :--- |")
        for term, definition in model_to_use.glossary.items():
            out.append(f"| **`{term}`** | {definition} |")
        out.append("")

    # Global Query Guardrails
    if model_to_use.global_guardrails:
        out.append("## Global AI Query Guardrails & Policies\n")
        for rule in model_to_use.global_guardrails:
            out.append(f"- 🛡️ {rule}")
        out.append("")
    
    # Schema Relationship Map
    out.append("## Schema Relationship Map\n")
    out.append("```")
    rel_map = generate_relationship_map(model_to_use)
    out.extend(rel_map)
    out.append("```\n")
    
    # Central Tables
    out.append("## Central Tables\n")
    central_tables = calculate_central_tables(model_to_use)
    top_central = [ct for ct in central_tables if ct[2] > 0][:5]
    if not top_central:
        top_central = central_tables[:5]
        
    table_map = {t.name: t for t in model_to_use.tables}
    for name, score, degree in top_central:
        t_model = table_map.get(name)
        desc = t_model.description if t_model and t_model.description else "No description available."
        out.append(f"### `{name}`")
        out.append(f"- **Connectivity Score**: {score} ({degree} connections)")
        out.append(f"- **Description**: {desc}")

        if t_model:
            meta_items = []
            if t_model.owner:
                meta_items.append(f"Owner: `{t_model.owner}`")
            if t_model.criticality:
                meta_items.append(f"Criticality: `{t_model.criticality}`")
            if t_model.tags:
                meta_items.append(f"Tags: `{', '.join(t_model.tags)}`")
            if meta_items:
                out.append(f"- **Governance**: {' | '.join(meta_items)}")

            if t_model.guardrails:
                out.append("- **Table Guardrails**:")
                for g in t_model.guardrails:
                    out.append(f"  - ⚠️ {g}")

            pk_cols = [c.name for c in t_model.columns if c.primary_key]
            out.append(f"- **Primary Key(s)**: {', '.join(pk_cols) if pk_cols else 'None'}\n")
            
    # Query Examples
    out.append("## Query Examples\n")
    query_examples = generate_query_examples(model_to_use)
    if query_examples:
        for q in query_examples[:5]:
            out.append("```sql")
            out.append(q)
            out.append("```\n")
    else:
        out.append("_No foreign key relationships found to auto-generate standard JOIN queries._\n")
        
    return "\n".join(out)


