import pytest
from schemap.models import (
    DatabaseSchemaModel,
    TableModel,
    ColumnModel,
    ForeignKeyModel,
    Provenance,
    SemanticRole,
)
from schemap.semantic import compile_semantic_graph, find_deterministic_join
from schemap.ground import ground
from schemap.validator import verify_sql


@pytest.fixture
def mock_saas_schema() -> DatabaseSchemaModel:
    """Fixture providing a realistic multi-tenant SaaS schema."""
    orgs = TableModel(
        name="organizations",
        columns=[
            ColumnModel(name="id", data_type="integer", primary_key=True),
            ColumnModel(name="name", data_type="text"),
            ColumnModel(name="created_at", data_type="timestamp"),
        ]
    )

    users = TableModel(
        name="users",
        columns=[
            ColumnModel(name="id", data_type="integer", primary_key=True),
            ColumnModel(name="org_id", data_type="integer"),
            ColumnModel(name="email", data_type="text"),
            ColumnModel(name="role", data_type="text"),
            ColumnModel(name="deleted_at", data_type="timestamp", is_nullable=True),
            ColumnModel(name="created_at", data_type="timestamp"),
        ],
        foreign_keys=[
            ForeignKeyModel(column_name="org_id", foreign_table_name="organizations", foreign_column_name="id")
        ]
    )

    subscriptions = TableModel(
        name="subscriptions",
        columns=[
            ColumnModel(name="id", data_type="integer", primary_key=True),
            ColumnModel(name="org_id", data_type="integer"),
            ColumnModel(name="status", data_type="text"),
            ColumnModel(name="plan_tier", data_type="text"),
            ColumnModel(name="created_at", data_type="timestamp"),
        ],
        foreign_keys=[
            ForeignKeyModel(column_name="org_id", foreign_table_name="organizations", foreign_column_name="id")
        ]
    )

    invoices = TableModel(
        name="invoices",
        columns=[
            ColumnModel(name="id", data_type="integer", primary_key=True),
            ColumnModel(name="org_id", data_type="integer"),
            ColumnModel(name="subscription_id", data_type="integer"),
            ColumnModel(name="amount_cents", data_type="integer"),
            ColumnModel(name="status", data_type="text"),
            ColumnModel(name="created_at", data_type="timestamp"),
        ],
        foreign_keys=[
            ForeignKeyModel(column_name="org_id", foreign_table_name="organizations", foreign_column_name="id"),
            ForeignKeyModel(column_name="subscription_id", foreign_table_name="subscriptions", foreign_column_name="id"),
        ]
    )

    payments = TableModel(
        name="payments",
        columns=[
            ColumnModel(name="id", data_type="integer", primary_key=True),
            ColumnModel(name="invoice_id", data_type="integer"),
            ColumnModel(name="amount_cents", data_type="integer"),
            ColumnModel(name="status", data_type="text"),
            ColumnModel(name="deleted_at", data_type="timestamp", is_nullable=True),
            ColumnModel(name="created_at", data_type="timestamp"),
        ],
        foreign_keys=[
            ForeignKeyModel(column_name="invoice_id", foreign_table_name="invoices", foreign_column_name="id"),
        ]
    )

    return DatabaseSchemaModel(tables=[orgs, users, subscriptions, invoices, payments])


def test_semantic_compiler_classification(mock_saas_schema):
    graph = compile_semantic_graph(mock_saas_schema)

    # 1. Tenant key detection
    assert graph.tenant_keys["organizations"] == "id"
    assert graph.tenant_keys["users"] == "org_id"
    assert graph.tenant_keys["subscriptions"] == "org_id"
    assert graph.tenant_keys["invoices"] == "org_id"

    # 2. Soft delete detection
    assert graph.soft_deletes["users"] == "deleted_at"
    assert graph.soft_deletes["payments"] == "deleted_at"
    assert "organizations" not in graph.soft_deletes

    # 3. Measures detection
    measure_names = [m.column for m in graph.measures]
    assert "amount_cents" in measure_names

    cents_measure = next(m for m in graph.measures if m.column == "amount_cents" and m.table == "invoices")
    assert cents_measure.provenance == Provenance.INFERRED
    assert "/ 100.0" in cents_measure.expression


def test_semantic_compiler_declared_override(mock_saas_schema):
    config = {
        "metrics": {
            "mrr": {
                "table": "invoices",
                "column": "amount_cents",
                "expression": "SUM(invoices.amount_cents) / 100.0",
                "description": "Monthly recurring revenue"
            }
        },
        "tenants": {
            "users": "org_id"
        }
    }
    graph = compile_semantic_graph(mock_saas_schema, declared_config=config)
    assert graph.provenance_map["metric:mrr"] == Provenance.DECLARED
    assert graph.provenance_map["users:tenant_key"] == Provenance.DECLARED


def test_deterministic_join_multi_hop(mock_saas_schema):
    graph = compile_semantic_graph(mock_saas_schema)

    # Multi-hop: payments -> invoices -> subscriptions -> organizations
    join_path = find_deterministic_join(graph, ["payments", "organizations"])
    assert join_path is not None
    assert "payments" in join_path.tables
    assert "invoices" in join_path.tables
    assert "organizations" in join_path.tables
    assert "JOIN invoices ON" in join_path.sql_join_clause


def test_grounding_primitive(mock_saas_schema):
    graph = compile_semantic_graph(mock_saas_schema)

    # Ask for revenue from organizations
    plan = ground(
        question="What is the total revenue for organization 42?",
        graph=graph,
        tenant_id=42
    )

    assert "payments" in plan.target_tables or "invoices" in plan.target_tables
    # Mandatory filters should enforce tenant_id and soft-deletes
    assert any("42" in f for f in plan.mandatory_filters)
    assert any("deleted_at IS NULL" in f for f in plan.mandatory_filters)
    assert "### Schemap Deterministic Grounding Context" in plan.prompt_instructions


def test_validator_blocks_destructive_sql(mock_saas_schema):
    graph = compile_semantic_graph(mock_saas_schema)

    # DROP TABLE
    res1 = verify_sql("DROP TABLE users;", graph=graph)
    assert not res1.passed
    assert any("forbidden" in v.lower() for v in res1.violations)

    # DELETE without WHERE
    res2 = verify_sql("DELETE FROM users;", graph=graph)
    assert not res2.passed

    # TRUNCATE
    res3 = verify_sql("TRUNCATE TABLE payments;", graph=graph)
    assert not res3.passed


def test_validator_tenant_isolation(mock_saas_schema):
    graph = compile_semantic_graph(mock_saas_schema)

    # Query accessing users without tenant filter
    unsafe_sql = "SELECT email FROM users WHERE role = 'admin';"
    res = verify_sql(unsafe_sql, graph=graph, tenant_id=10)
    assert not res.passed
    assert any("Tenant Isolation Failure" in v for v in res.violations)

    # Query with correct tenant filter
    safe_sql = "SELECT email FROM users WHERE role = 'admin' AND users.org_id = 10 AND users.deleted_at IS NULL;"
    safe_res = verify_sql(safe_sql, graph=graph, tenant_id=10)
    assert safe_res.passed


def test_validator_soft_delete_enforcement(mock_saas_schema):
    graph = compile_semantic_graph(mock_saas_schema)

    # Missing deleted_at IS NULL
    sql = "SELECT email FROM users WHERE org_id = 5;"
    res = verify_sql(sql, graph=graph, tenant_id=5)
    assert not res.passed
    assert any("Soft-Delete Violation" in v for v in res.violations)

    # Auto-patch test
    patch_res = verify_sql(sql, graph=graph, tenant_id=5, auto_patch=True)
    assert patch_res.patched_sql is not None
    assert "DELETED_AT IS NULL" in patch_res.patched_sql.upper()


def test_validator_cartesian_join_hazard(mock_saas_schema):
    graph = compile_semantic_graph(mock_saas_schema)

    # Cartesian join: FROM users, organizations
    bad_join = "SELECT * FROM users, organizations WHERE users.org_id = 5 AND users.deleted_at IS NULL;"
    res = verify_sql(bad_join, graph=graph, tenant_id=5)
    assert not res.passed
    assert any("Cartesian join" in v for v in res.violations)
