import pytest
from pathlib import Path
import sqlite3
from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.context import calculate_central_tables, generate_relationship_map, generate_query_examples, generate_database_context
from schemap.agents import generate_claude_md, generate_agents_md, write_agent_files
from schemap.linter import calculate_score

@pytest.fixture
def sample_schema():
    users = TableModel(
        name="users",
        description="Application users account details",
        columns=[
            ColumnModel(name="id", data_type="INTEGER", primary_key=True),
            ColumnModel(name="email", data_type="VARCHAR"),
            ColumnModel(name="created_at", data_type="TIMESTAMP")
        ],
        foreign_keys=[]
    )
    orders = TableModel(
        name="orders",
        description="Customer order purchases",
        columns=[
            ColumnModel(name="id", data_type="INTEGER", primary_key=True),
            ColumnModel(name="user_id", data_type="INTEGER"),
            ColumnModel(name="total_price", data_type="DECIMAL")
        ],
        foreign_keys=[
            ForeignKeyModel(column_name="user_id", foreign_table_name="users", foreign_column_name="id")
        ]
    )
    audit_logs = TableModel(
        name="audit_logs",
        description="System activity audit logs",
        columns=[
            ColumnModel(name="id", data_type="INTEGER", primary_key=True),
            ColumnModel(name="user_id", data_type="INTEGER"),
            ColumnModel(name="order_id", data_type="INTEGER"),
            ColumnModel(name="action", data_type="VARCHAR")
        ],
        foreign_keys=[
            ForeignKeyModel(column_name="user_id", foreign_table_name="users", foreign_column_name="id"),
            ForeignKeyModel(column_name="order_id", foreign_table_name="orders", foreign_column_name="id")
        ]
    )
    return DatabaseSchemaModel(tables=[users, orders, audit_logs])

def test_central_tables_ranking(sample_schema):
    central = calculate_central_tables(sample_schema)
    names = [c[0] for c in central]
    # users & orders should outrank audit_logs despite audit_logs having connections due to utility table penalty
    assert names.index("users") < names.index("audit_logs")
    assert names.index("orders") < names.index("audit_logs")

def test_generate_relationship_map(sample_schema):
    rel_map = generate_relationship_map(sample_schema)
    assert any("orders (user_id) ──> users (id)" in r for r in rel_map)
    assert any("audit_logs (user_id) ──> users (id)" in r for r in rel_map)

def test_generate_query_examples(sample_schema):
    queries = generate_query_examples(sample_schema)
    assert len(queries) >= 1
    assert "JOIN users ON orders.user_id = users.id" in queries[0] or "JOIN" in queries[0]

def test_generate_database_context(sample_schema):
    ctx_md = generate_database_context(sample_schema)
    assert "# Database Context Engine Output" in ctx_md
    assert "## Schema Relationship Map" in ctx_md
    assert "## Central Tables" in ctx_md
    assert "## Query Examples" in ctx_md

def test_agents_generation(sample_schema, tmp_path):
    claude_md = generate_claude_md(sample_schema)
    agents_md = generate_agents_md(sample_schema)
    
    assert "CLAUDE" in claude_md or "Claude" in claude_md
    assert "AGENTS.md" in agents_md
    
    files = write_agent_files(sample_schema, str(tmp_path))
    assert Path(files["CLAUDE.md"]).exists()
    assert Path(files["AGENTS.md"]).exists()

def test_ai_readiness_score(sample_schema):
    score, issues = calculate_score(sample_schema, unresolved_abbrs=[])
    assert score >= 80
    assert isinstance(issues, list)
