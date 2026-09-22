import re
from typing import List, Dict, Any, Set
from .models import (
    SemanticPolicyGraph,
    GroundedPlan,
    SemanticEntity,
    JoinPath,
)
from .semantic import find_deterministic_join

# Common English word stem / synonym matching
SYNONYM_MAP = {
    "revenue": ["payments", "transactions", "charges", "settlements", "amount_cents", "amount", "total"],
    "sales": ["payments", "transactions", "charges", "invoices", "orders", "billing_records"],
    "spend": ["payments", "transactions", "charges", "amount_cents", "fee"],
    "money": ["amount_cents", "payments", "transactions", "charges"],
    "billing": ["invoices", "invoice_items", "subscriptions", "billing_records"],
    "customer": ["organizations", "tenants", "accounts", "customers", "users"],
    "client": ["organizations", "tenants", "accounts", "customers", "users"],
    "tenant": ["organizations", "tenants", "accounts"],
    "org": ["organizations", "tenants", "accounts"],
    "organization": ["organizations", "tenants", "accounts"],
    "account": ["accounts", "organizations", "tenants"],
    "user": ["users", "members", "customers"],
    "member": ["members", "users"],
    "sub": ["subscriptions"],
    "subscription": ["subscriptions"],
    "plan": ["plans", "tiers"],
    "tier": ["plans", "tiers"],
    "bill": ["invoices", "billing_records"],
    "invoice": ["invoices", "billing_records"],
    "record": ["billing_records"],
    "pay": ["payments", "transactions", "charges", "settlements"],
    "payment": ["payments", "transactions", "charges", "settlements"],
    "charge": ["charges", "payments", "transactions"],
    "settlement": ["settlements", "payments", "transactions"],
    "transaction": ["transactions", "payments", "charges"],
    "event": ["usage_events"],
    "usage": ["usage_events"],
}


def _tokenize(text: str) -> Set[str]:
    """Tokenize and normalize text into clean words."""
    words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    tokens = set(words)
    # Also add singular/plural variations
    for w in words:
        if w.endswith("s") and len(w) > 3:
            tokens.add(w[:-1])
        else:
            tokens.add(w + "s")
    return tokens


def ground(
    question: str,
    graph: SemanticPolicyGraph,
    tenant_id: str | int | None = None,
) -> GroundedPlan:
    """
    Rigorously grounds a natural language question against a SemanticPolicyGraph.
    Resolves relevant tables, deterministic join paths, and mandatory tenant/soft-delete invariants.
    """
    tokens = _tokenize(question)

    matched_tables: Set[str] = set()
    matched_measures: List[SemanticEntity] = []
    matched_dimensions: List[SemanticEntity] = []
    ambiguities: List[str] = []

    # 1. Match tables directly or via synonyms
    for t_name in graph.tables:
        t_tokens = _tokenize(t_name)
        if t_tokens.intersection(tokens):
            matched_tables.add(t_name)

    for word, target_entities in SYNONYM_MAP.items():
        if word in tokens:
            for entity in target_entities:
                if entity in graph.tables:
                    matched_tables.add(entity)

    # 2. Match measures
    for m in graph.measures:
        m_tokens = _tokenize(m.column)
        if m_tokens.intersection(tokens) or m.column.lower() in tokens:
            matched_measures.append(m)
            matched_tables.add(m.table)
        elif any(syn in tokens for syn in ["revenue", "sales", "spend", "total", "amount"]) and "amount" in m.column.lower():
            matched_measures.append(m)
            matched_tables.add(m.table)

    # 3. Match dimensions
    for d in graph.dimensions:
        d_tokens = _tokenize(d.column)
        if d_tokens.intersection(tokens):
            matched_dimensions.append(d)

    # Default to first table if none detected
    if not matched_tables and graph.tables:
        first_table = list(graph.tables.keys())[0]
        matched_tables.add(first_table)
        ambiguities.append(f"No explicit tables mentioned in query; defaulted to '{first_table}'")

    target_table_list = sorted(list(matched_tables))

    # 4. Resolve join path
    join_path: JoinPath | None = None
    if len(target_table_list) > 1:
        join_path = find_deterministic_join(graph, target_table_list)
        if not join_path:
            ambiguities.append(
                f"No direct or multi-hop foreign key path found connecting tables: {', '.join(target_table_list)}"
            )

    # All active tables involved in the query (base + join hops)
    active_tables = join_path.tables if join_path else target_table_list

    # 5. Mandatory Filters (Tenant Isolation & Soft Deletes)
    mandatory_filters: List[str] = []

    for t in active_tables:
        # Tenant filter
        if tenant_id is not None:
            t_key = graph.tenant_keys.get(t)
            if t_key:
                val_str = f"'{tenant_id}'" if isinstance(tenant_id, str) else str(tenant_id)
                mandatory_filters.append(f"{t}.{t_key} = {val_str}")

        # Soft delete filter
        sd_col = graph.soft_deletes.get(t)
        if sd_col:
            mandatory_filters.append(f"{t}.{sd_col} IS NULL")

    # 6. Build structured prompt instructions
    instructions_lines = [
        "### Schemap Deterministic Grounding Context",
        f"- User Intent: \"{question}\"",
        f"- Target Tables: {', '.join(active_tables)}",
    ]

    if join_path:
        join_prov = "DECLARED (Virtual Relations)" if any(s.is_virtual for s in join_path.steps) else "INFERRED (Physical Foreign Keys)"
        instructions_lines.append(f"- Deterministic Join Path [{join_prov}]:\n```sql\n{join_path.sql_join_clause}\n```")

    if mandatory_filters:
        instructions_lines.append("- Mandatory Filters (MUST be included in WHERE clause):")
        for f in mandatory_filters:
            tbl = f.split(".")[0]
            if "IS NULL" in f:
                prov = graph.provenance_map.get(f"{tbl}:soft_delete", "INFERRED")
            else:
                prov = graph.provenance_map.get(f"{tbl}:tenant_key", "INFERRED")
            prov_str = prov.value if hasattr(prov, "value") else str(prov)
            instructions_lines.append(f"  * {f} [{prov_str}]")

    if matched_measures:
        instructions_lines.append("- Recommended Measure Expressions:")
        for m in matched_measures:
            expr = m.expression or f"SUM({m.table}.{m.column})"
            instructions_lines.append(f"  * {m.column} [{m.provenance.value}]: {expr}")

    if ambiguities:
        instructions_lines.append("- Semantic Ambiguities / Warnings:")
        for a in ambiguities:
            instructions_lines.append(f"  * [UNKNOWN]: {a}")

    prompt_instructions = "\n".join(instructions_lines)

    return GroundedPlan(
        question=question,
        target_tables=active_tables,
        join_path=join_path,
        mandatory_filters=mandatory_filters,
        measures=matched_measures,
        dimensions=matched_dimensions,
        ambiguities=ambiguities,
        prompt_instructions=prompt_instructions,
    )
