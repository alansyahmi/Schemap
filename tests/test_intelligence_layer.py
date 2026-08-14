import os
import tempfile
from pathlib import Path
from click.testing import CliRunner

from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.agents import generate_safety_rules, generate_claude_md, generate_agents_md
from schemap.context import generate_database_context, filter_schema_by_scope
from schemap.benchmark import calculate_benchmark
from schemap.cli import cli


def get_mock_schema():
    users_tbl = TableModel(
        name="users",
        description="Core user accounts",
        columns=[
            ColumnModel(name="id", data_type="INTEGER", primary_key=True),
            ColumnModel(name="email", data_type="VARCHAR"),
            ColumnModel(name="password_hash", data_type="VARCHAR"),
        ],
        foreign_keys=[]
    )
    orders_tbl = TableModel(
        name="orders",
        description="Customer transactions",
        columns=[
            ColumnModel(name="id", data_type="INTEGER", primary_key=True),
            ColumnModel(name="user_id", data_type="INTEGER"),
            ColumnModel(name="total_cents", data_type="INTEGER"),
        ],
        foreign_keys=[
            ForeignKeyModel(column_name="user_id", foreign_table_name="users", foreign_column_name="id")
        ]
    )
    fact_sales_tbl = TableModel(
        name="fact_sales",
        description="Analytics sales aggregation",
        columns=[
            ColumnModel(name="id", data_type="INTEGER", primary_key=True),
            ColumnModel(name="revenue", data_type="DECIMAL"),
        ],
        foreign_keys=[]
    )
    return DatabaseSchemaModel(tables=[users_tbl, orders_tbl, fact_sales_tbl])


def test_generate_safety_rules():
    schema = get_mock_schema()
    rules = generate_safety_rules(schema)
    assert any("Sensitive Data Protection" in r for r in rules)
    assert any("password_hash" in r for r in rules)


def test_scoped_context_filtering():
    schema = get_mock_schema()
    
    # Analytics scope
    analytics_model = filter_schema_by_scope(schema, scope="analytics")
    table_names = [t.name for t in analytics_model.tables]
    assert "fact_sales" in table_names
    
    # Backend scope
    backend_model = filter_schema_by_scope(schema, scope="backend")
    backend_names = [t.name for t in backend_model.tables]
    assert "users" in backend_names or "orders" in backend_names
    
    # Context generation with scope
    context_output = generate_database_context(schema, scope="analytics")
    assert "Context Scope" in context_output
    assert "analytics" in context_output


def test_benchmark_cost_calculation():
    schema = get_mock_schema()
    raw_tables = [
        {"name": "users", "columns": [{"name": "id", "data_type": "INT"}]},
        {"name": "orders", "columns": [{"name": "id", "data_type": "INT"}]}
    ]
    bench = calculate_benchmark(schema, raw_tables)
    assert "estimated_savings_per_prompt_usd" in bench
    assert "estimated_monthly_savings_per_dev_usd" in bench


def test_cli_examples_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create lightweight schemap.yaml with SQLite test DB
        with open("schemap.yaml", "w", encoding="utf-8") as f:
            f.write("database:\n  connection_url: 'sqlite:///:memory:'\n")
        result = runner.invoke(cli, ["examples"])
        assert result.exit_code == 0
        assert "Canonical Reference SQL Examples" in result.output


def test_cli_hook_install_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs(".git", exist_ok=True)
        result = runner.invoke(cli, ["hook", "install"])
        assert result.exit_code == 0
        assert "Installed Git pre-commit hook" in result.output
        hook_path = Path(".git/hooks/pre-commit")
        assert hook_path.exists()
        with open(hook_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "schemap sync" in content
