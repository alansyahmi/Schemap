import re
from typing import List, Dict, Any, Tuple
from collections import deque
from .models import (
    DatabaseSchemaModel,
    TableModel,
    ColumnModel,
    Provenance,
    SemanticRole,
    SemanticEntity,
    JoinStep,
    JoinPath,
    SemanticPolicyGraph,
)

TENANT_COLUMN_PATTERNS = [
    r"^org_id$",
    r"^organization_id$",
    r"^tenant_id$",
    r"^company_id$",
    r"^account_id$",
    r"^workspace_id$",
]

TENANT_TABLE_NAMES = ["organizations", "tenants", "companies", "accounts", "workspaces"]

SOFT_DELETE_PATTERNS = [
    r"^deleted_at$",
    r"^is_deleted$",
    r"^archived_at$",
    r"^is_archived$",
]

MEASURE_PATTERNS = [
    r".*_cents$",
    r"^amount.*",
    r".*_amount.*",
    r"^price.*",
    r".*_price.*",
    r"^total.*",
    r".*_total.*",
    r"^cost.*",
    r"^fee.*",
    r"^quantity$",
    r"^qty$",
    r"^count$",
    r"^balance.*",
    r"^score$",
    r"^rating$",
    r"^usage$",
    r"^volume$",
]

NUMERIC_TYPES = {
    "int", "integer", "bigint", "smallint", "tinyint",
    "float", "double", "real", "decimal", "numeric", "number"
}

TIME_GRAIN_PATTERNS = [
    r".*_at$",
    r"^timestamp$",
    r"^date$",
    r".*_date$",
    r"^event_time$",
    r"^occurred_at$",
]

DIMENSION_PATTERNS = [
    r"^status$",
    r"^type$",
    r"^role$",
    r"^tier$",
    r"^plan.*",
    r"^category.*",
    r"^currency$",
    r"^country$",
    r"^code$",
    r"^name$",
]


def compile_semantic_graph(
    schema: DatabaseSchemaModel,
    declared_config: Dict[str, Any] | None = None,
) -> SemanticPolicyGraph:
    """
    Compiles a raw database schema model into an active, provenance-aware
    SemanticPolicyGraph targeting PostgreSQL operational patterns.
    """
    declared = declared_config or {}
    declared_metrics = declared.get("metrics", {})
    declared_invariants = declared.get("invariants", [])
    declared_tenants = declared.get("tenants", {})
    declared_soft_deletes = declared.get("soft_deletes", {})

    graph = SemanticPolicyGraph(
        database_name="postgres",
        declared_invariants=declared_invariants,
    )

    # 1. Process tables and columns
    for table in schema.tables:
        t_copy = table.model_copy(deep=True)
        graph.tables[t_copy.name] = t_copy

        # Check tenant key
        tenant_key = None
        if t_copy.name in declared_tenants:
            tenant_key = declared_tenants[t_copy.name]
            graph.provenance_map[f"{t_copy.name}:tenant_key"] = Provenance.DECLARED
        else:
            # If this table is the organization/tenant root table, its PK is the tenant key
            if t_copy.name.lower() in TENANT_TABLE_NAMES:
                for col in t_copy.columns:
                    if col.primary_key:
                        tenant_key = col.name
                        graph.provenance_map[f"{t_copy.name}:tenant_key"] = Provenance.INFERRED
                        break
            else:
                # Search columns for tenant pattern
                tenant_candidates = [
                    col for col in t_copy.columns
                    if any(re.match(pat, col.name.lower()) for pat in TENANT_COLUMN_PATTERNS)
                ]
                if len(tenant_candidates) == 1:
                    col = tenant_candidates[0]
                    tenant_key = col.name
                    col.semantic_role = SemanticRole.TENANT_KEY
                    col.provenance = Provenance.INFERRED
                    graph.provenance_map[f"{t_copy.name}:tenant_key"] = Provenance.INFERRED
                elif len(tenant_candidates) > 1:
                    # Deceptive / Ambiguous schema detected! Do not pick arbitrarily
                    candidate_names = [c.name for c in tenant_candidates]
                    graph.provenance_map[f"{t_copy.name}:tenant_key"] = Provenance.UNKNOWN
                    graph.declared_invariants.append(
                        f"AMBIGUITY: Multiple tenant keys detected on '{t_copy.name}': {candidate_names}. Human declaration required."
                    )

        if tenant_key:
            t_copy.tenant_key = tenant_key
            graph.tenant_keys[t_copy.name] = tenant_key

        # Check soft delete column
        soft_del_col = None
        if t_copy.name in declared_soft_deletes:
            soft_del_col = declared_soft_deletes[t_copy.name]
            graph.provenance_map[f"{t_copy.name}:soft_delete"] = Provenance.DECLARED
        else:
            sd_candidates = [
                col for col in t_copy.columns
                if any(re.match(pat, col.name.lower()) for pat in SOFT_DELETE_PATTERNS)
            ]
            if len(sd_candidates) == 1:
                col = sd_candidates[0]
                soft_del_col = col.name
                col.semantic_role = SemanticRole.SOFT_DELETE
                col.provenance = Provenance.INFERRED
                graph.provenance_map[f"{t_copy.name}:soft_delete"] = Provenance.INFERRED
            elif len(sd_candidates) > 1:
                # Ambiguity detected
                candidate_names = [c.name for c in sd_candidates]
                graph.provenance_map[f"{t_copy.name}:soft_delete"] = Provenance.UNKNOWN
                graph.declared_invariants.append(
                    f"AMBIGUITY: Multiple soft-delete columns detected on '{t_copy.name}': {candidate_names}. Human declaration required."
                )

        if soft_del_col:
            t_copy.soft_delete_column = soft_del_col
            graph.soft_deletes[t_copy.name] = soft_del_col

        # Classify all columns into semantic roles
        for col in t_copy.columns:
            # Skip if already identified as tenant_key or soft_delete
            if col.semantic_role in (SemanticRole.TENANT_KEY, SemanticRole.SOFT_DELETE):
                continue

            if col.primary_key:
                col.semantic_role = SemanticRole.PRIMARY_KEY
                col.provenance = Provenance.INFERRED
                continue

            # Check if foreign key
            is_fk = any(
                fk.column_name == col.name for fk in t_copy.foreign_keys
            ) or any(
                vfk.column_name == col.name for vfk in t_copy.virtual_relationships
            )
            if is_fk:
                col.semantic_role = SemanticRole.FOREIGN_KEY
                col.provenance = Provenance.INFERRED
                continue

            # Check measures (numeric + pattern match)
            is_numeric = any(num_t in col.data_type.lower() for num_t in NUMERIC_TYPES)
            is_measure_name = any(re.match(pat, col.name.lower()) for pat in MEASURE_PATTERNS)

            if is_numeric and is_measure_name:
                col.semantic_role = SemanticRole.MEASURE
                col.provenance = Provenance.INFERRED
                
                # Check for currency cents pattern
                expr = f"SUM({t_copy.name}.{col.name})"
                if col.name.endswith("_cents"):
                    expr = f"SUM({t_copy.name}.{col.name}) / 100.0"

                graph.measures.append(
                    SemanticEntity(
                        table=t_copy.name,
                        column=col.name,
                        role=SemanticRole.MEASURE,
                        provenance=Provenance.INFERRED,
                        data_type=col.data_type,
                        expression=expr,
                        description=f"Measure {col.name} in {t_copy.name}"
                    )
                )
                continue

            # Check time grain
            if any(re.match(pat, col.name.lower()) for pat in TIME_GRAIN_PATTERNS):
                col.semantic_role = SemanticRole.TIME_GRAIN
                col.provenance = Provenance.INFERRED
                continue

            # Check dimension
            if any(re.match(pat, col.name.lower()) for pat in DIMENSION_PATTERNS) or not is_numeric:
                col.semantic_role = SemanticRole.DIMENSION
                col.provenance = Provenance.INFERRED
                graph.dimensions.append(
                    SemanticEntity(
                        table=t_copy.name,
                        column=col.name,
                        role=SemanticRole.DIMENSION,
                        provenance=Provenance.INFERRED,
                        data_type=col.data_type,
                        description=f"Dimension {col.name} in {t_copy.name}"
                    )
                )

    # 2. Add declared metrics from config
    for metric_name, m_spec in declared_metrics.items():
        table_name = m_spec.get("table", "")
        col_name = m_spec.get("column", "")
        expr = m_spec.get("expression", f"SUM({table_name}.{col_name})")
        graph.measures.append(
            SemanticEntity(
                table=table_name,
                column=col_name or metric_name,
                role=SemanticRole.MEASURE,
                provenance=Provenance.DECLARED,
                data_type="numeric",
                expression=expr,
                description=m_spec.get("description", f"Declared metric {metric_name}")
            )
        )
        graph.provenance_map[f"metric:{metric_name}"] = Provenance.DECLARED

    return graph


def find_deterministic_join(
    graph: SemanticPolicyGraph,
    tables: List[str],
) -> JoinPath | None:
    """
    Computes the shortest deterministic join path across a list of target tables
    using the foreign key relationships in the SemanticPolicyGraph.
    """
    if len(tables) < 2:
        return None

    # Build adjacency graph
    adj: Dict[str, List[Tuple[str, str, str, bool]]] = {t: [] for t in graph.tables}
    
    for t_name, table in graph.tables.items():
        # Physical FKs
        for fk in table.foreign_keys:
            ref_tbl = getattr(fk, "foreign_table_name", None) or getattr(fk, "ref_table", None)
            col = getattr(fk, "column_name", None) or getattr(fk, "column", None)
            ref_col = getattr(fk, "foreign_column_name", None) or getattr(fk, "ref_column", None)

            if ref_tbl and ref_tbl in adj:
                adj[t_name].append((ref_tbl, col, ref_col, False))
                adj[ref_tbl].append((t_name, ref_col, col, False))

        # Virtual FKs
        for vfk in getattr(table, "virtual_relationships", []):
            ref_tbl = getattr(vfk, "foreign_table_name", None) or getattr(vfk, "ref_table", None)
            col = getattr(vfk, "column_name", None) or getattr(vfk, "column", None)
            ref_col = getattr(vfk, "foreign_column_name", None) or getattr(vfk, "ref_column", None)

            if ref_tbl and ref_tbl in adj:
                adj[t_name].append((ref_tbl, col, ref_col, True))
                adj[ref_tbl].append((t_name, ref_col, col, True))

    target_set = set(tables)
    found_tables = None
    found_steps = None

    for start_table in tables:
        if start_table not in adj:
            continue

        queue = deque([([start_table], [])])
        visited = set()

        while queue:
            path_nodes, steps = queue.popleft()

            if target_set.issubset(set(path_nodes)):
                if found_tables is None or len(path_nodes) < len(found_tables):
                    found_tables = path_nodes
                    found_steps = steps
                break

            key = tuple(sorted(path_nodes))
            if key in visited:
                continue
            visited.add(key)

            # Expand from any node currently joined to form join trees
            for curr in path_nodes:
                for neighbor, from_col, to_col, is_virt in adj.get(curr, []):
                    if neighbor not in path_nodes:
                        next_nodes = path_nodes + [neighbor]
                        step = JoinStep(
                            from_table=curr,
                            from_column=from_col,
                            to_table=neighbor,
                            to_column=to_col,
                            is_virtual=is_virt
                        )
                        queue.append((next_nodes, steps + [step]))

    if not found_tables or not found_steps:
        return None

    # Construct clean SQL join clauses
    # E.g. FROM table1 JOIN table2 ON table1.col = table2.col
    base_table = found_tables[0]
    join_clauses = []
    joined_tables = {base_table}

    for step in found_steps:
        # Step: curr.from_col = neighbor.to_col
        # One is already joined, the other is being joined
        if step.to_table not in joined_tables:
            join_clauses.append(
                f"JOIN {step.to_table} ON {step.from_table}.{step.from_column} = {step.to_table}.{step.to_column}"
            )
            joined_tables.add(step.to_table)
        elif step.from_table not in joined_tables:
            join_clauses.append(
                f"JOIN {step.from_table} ON {step.to_table}.{step.to_column} = {step.from_table}.{step.from_column}"
            )
            joined_tables.add(step.from_table)

    full_sql = f"FROM {base_table}\n" + "\n".join(join_clauses)

    return JoinPath(
        tables=found_tables,
        steps=found_steps,
        sql_join_clause=full_sql
    )
