from typing import List, Set, Any
import sqlglot
from sqlglot import exp
from .models import SemanticPolicyGraph, ValidationResult


DESTRUCTIVE_EXPRESSIONS = (
    exp.Drop,
    exp.TruncateTable,
    exp.Alter,
    exp.Create,
    exp.Command,
    exp.Grant,
    exp.Insert,
)


def verify_sql(
    sql: str,
    graph: SemanticPolicyGraph,
    tenant_id: str | int | None = None,
    auto_patch: bool = False,
    allow_mutations: bool = False,
) -> ValidationResult:
    """
    Rigorously validates a SQL query against the SemanticPolicyGraph using sqlglot AST parsing.
    Enforces tenant boundaries, soft-delete compliance, and structural/mutation guardrails.
    """
    violations: List[str] = []
    patched_sql: str | None = None

    # 1. Parse SQL (Detect multi-statement payloads)
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
        if not statements:
            return ValidationResult(
                passed=False,
                violations=["SQL Parse Failure: Empty SQL string."],
                tables_analyzed=[],
            )
        if len(statements) > 1:
            return ValidationResult(
                passed=False,
                violations=[f"Security Policy Violation: Multi-statement execution ({len(statements)} statements) is forbidden."],
                tables_analyzed=[],
            )
        parsed = statements[0]
    except Exception as e:
        return ValidationResult(
            passed=False,
            violations=[f"SQL Parse Failure: {str(e)}"],
            tables_analyzed=[],
        )

    # 2. Check for destructive expressions (including nested in CTEs or subqueries)
    if not allow_mutations:
        destructive_node = parsed if isinstance(parsed, DESTRUCTIVE_EXPRESSIONS) else parsed.find(DESTRUCTIVE_EXPRESSIONS)
        if destructive_node:
            return ValidationResult(
                passed=False,
                violations=[f"Policy Violation: Statement contains forbidden destructive expression '{type(destructive_node).__name__}'."],
                tables_analyzed=[],
            )

        mutation_node = parsed if isinstance(parsed, (exp.Delete, exp.Update)) else parsed.find((exp.Delete, exp.Update))
        if mutation_node:
            return ValidationResult(
                passed=False,
                violations=[f"Policy Violation: Mutation '{type(mutation_node).__name__}' is forbidden in read/analytics scope."],
                tables_analyzed=[],
            )
    else:
        # If mutations are allowed, verify that DELETE/UPDATE has a WHERE clause
        mutation_node = parsed if isinstance(parsed, (exp.Delete, exp.Update)) else parsed.find((exp.Delete, exp.Update))
        if mutation_node:
            where_clause = mutation_node.find(exp.Where)
            if not where_clause:
                return ValidationResult(
                    passed=False,
                    violations=[f"Critical Safety Violation: '{type(mutation_node).__name__}' statement without WHERE clause is prohibited."],
                    tables_analyzed=[],
                )

    # 3. Extract queried tables
    tables_found: Set[str] = set()
    for t_node in parsed.find_all(exp.Table):
        t_name = t_node.name.lower()
        # Exclude subquery aliases or CTEs
        if t_name in graph.tables:
            tables_found.add(t_name)

    tables_analyzed = sorted(list(tables_found))

    # 4. Check for Cartesian joins (multiple tables in FROM without JOIN ON)
    joins = parsed.find_all(exp.Join)
    for j in joins:
        # If join is CROSS or has no ON condition
        if j.args.get("kind") == "CROSS" or (not j.args.get("on") and not j.args.get("using")):
            violations.append(
                f"Performance Risk: Unconstrained Cartesian join detected on table '{j.this.name}'."
            )

    # 5. Extract all WHERE and ON predicates as text for fast containment check
    all_predicates: List[str] = []
    for w in parsed.find_all(exp.Where):
        all_predicates.append(w.sql(dialect="postgres").lower())
    for j in parsed.find_all(exp.Join):
        if j.args.get("on"):
            all_predicates.append(j.args.get("on").sql(dialect="postgres").lower())

    combined_predicates_text = " ".join(all_predicates)

    missing_tenant_filters: List[str] = []
    missing_soft_deletes: List[str] = []

    # 6. Tenant Isolation Check
    if tenant_id is not None:
        tenant_str = str(tenant_id).lower()
        for tbl in tables_analyzed:
            t_key = graph.tenant_keys.get(tbl)
            if t_key:
                t_key_lower = t_key.lower()
                # Check if tenant key condition exists in predicates
                has_tenant_filter = (
                    (t_key_lower in combined_predicates_text and tenant_str in combined_predicates_text)
                    or f"{tbl}.{t_key_lower}" in combined_predicates_text
                    or f":{t_key_lower}" in combined_predicates_text
                    or f":tenant_id" in combined_predicates_text
                    or f":org_id" in combined_predicates_text
                )
                if not has_tenant_filter:
                    val_repr = f"'{tenant_id}'" if isinstance(tenant_id, str) else str(tenant_id)
                    req_filter = f"{tbl}.{t_key} = {val_repr}"
                    violations.append(
                        f"Tenant Isolation Failure: Query accesses table '{tbl}' without mandatory tenant predicate '{req_filter}'."
                    )
                    missing_tenant_filters.append(req_filter)

    # 7. Soft-Delete Check
    for tbl in tables_analyzed:
        sd_col = graph.soft_deletes.get(tbl)
        if sd_col:
            sd_col_lower = sd_col.lower()
            has_sd_filter = (
                f"{sd_col_lower} is null" in combined_predicates_text
                or f"{tbl}.{sd_col_lower} is null" in combined_predicates_text
            )
            if not has_sd_filter:
                req_sd = f"{tbl}.{sd_col} IS NULL"
                violations.append(
                    f"Soft-Delete Violation: Table '{tbl}' has soft-deletes enabled, but query is missing '{req_sd}'."
                )
                missing_soft_deletes.append(req_sd)

    # 8. Auto-Patch Logic
    if auto_patch and (missing_tenant_filters or missing_soft_deletes):
        # We can append missing filters to the main WHERE clause
        filters_to_add = missing_tenant_filters + missing_soft_deletes
        for f in filters_to_add:
            try:
                cond_exp = sqlglot.parse_one(f, read="postgres")
                where_clause = parsed.find(exp.Where)
                if where_clause:
                    where_clause.set("this", exp.and_(where_clause.this, cond_exp))
                else:
                    parsed.where(cond_exp, copy=False)
            except Exception:
                pass
        patched_sql = parsed.sql(dialect="postgres", pretty=True)

    passed = len(violations) == 0

    return ValidationResult(
        passed=passed,
        violations=violations,
        patched_sql=patched_sql,
        tables_analyzed=tables_analyzed,
    )
