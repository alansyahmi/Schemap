import pytest
from pathlib import Path
from click.testing import CliRunner
from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.config import (
    SemanticsConfig, TableSemanticsConfig, ColumnSemanticsConfig, VirtualRelationshipConfig,
    SchemapConfig, DatabaseConfig
)
from schemap.semantics import apply_semantics, generate_default_semantics_template
from schemap.context import generate_database_context, generate_relationship_map, generate_query_examples
from schemap.agents import generate_claude_md, generate_agents_md, generate_safety_rules
from schemap.cli import cli


def get_base_schema() -> DatabaseSchemaModel:
    return DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                description="Core user accounts",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="email", data_type="VARCHAR(255)", is_nullable=False),
                    ColumnModel(name="full_name", data_type="VARCHAR(255)", is_nullable=True),
                ],
                foreign_keys=[]
            ),
            TableModel(
                name="orders",
                description="E-commerce purchase orders",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="user_id", data_type="INTEGER", is_nullable=False),
                    ColumnModel(name="total_cents", data_type="INTEGER", is_nullable=False),
                    ColumnModel(name="stripe_charge_id", data_type="VARCHAR(255)", is_nullable=True),
                ],
                foreign_keys=[
                    ForeignKeyModel(column_name="user_id", foreign_table_name="users", foreign_column_name="id")
                ]
            )
        ]
    )


def test_apply_semantics_model_merging():
    schema = get_base_schema()
    semantics_cfg = SemanticsConfig(
        glossary={
            "GMV": "Gross Merchandise Value before refunds",
            "ActiveUser": "User with at least one order in 30 days"
        },
        global_guardrails=[
            "All timestamps are evaluated in UTC timezone.",
            "Always filter by deleted_at IS NULL on soft-delete tables."
        ],
        tables={
            "orders": TableSemanticsConfig(
                owner="@payments-and-checkout",
                criticality="tier-1",
                tags=["financial", "core", "sox-compliant"],
                guardrails=[
                    "Never UPDATE total_cents directly; create a refund transaction instead."
                ],
                virtual_relationships=[
                    VirtualRelationshipConfig(
                        column="stripe_charge_id",
                        ref_table="stripe_charges",
                        ref_column="id"
                    )
                ],
                columns={
                    "total_cents": ColumnSemanticsConfig(
                        semantic_type="currency_cents",
                        tags=["financial", "immutable"],
                        guardrails=["Must be non-negative integer"]
                    )
                }
            )
        }
    )

    enriched = apply_semantics(schema, semantics_cfg)

    # Verify Glossary
    assert "GMV" in enriched.glossary
    assert enriched.glossary["GMV"] == "Gross Merchandise Value before refunds"

    # Verify Global Guardrails
    assert len(enriched.global_guardrails) == 2
    assert "UTC timezone" in enriched.global_guardrails[0]

    # Verify Orders table semantics
    orders_table = next(t for t in enriched.tables if t.name == "orders")
    assert orders_table.owner == "@payments-and-checkout"
    assert orders_table.criticality == "tier-1"
    assert "financial" in orders_table.tags
    assert len(orders_table.guardrails) == 1
    assert "Never UPDATE total_cents" in orders_table.guardrails[0]

    # Verify Virtual Relationships
    assert len(orders_table.virtual_relationships) == 1
    assert orders_table.virtual_relationships[0].column_name == "stripe_charge_id"
    assert orders_table.virtual_relationships[0].foreign_table_name == "stripe_charges"

    # Verify Column semantics
    tot_col = next(c for c in orders_table.columns if c.name == "total_cents")
    assert tot_col.semantic_type == "currency_cents"
    assert "immutable" in tot_col.tags
    assert len(tot_col.guardrails) == 1


def test_context_rendering_with_semantics():
    schema = get_base_schema()
    semantics_cfg = SemanticsConfig(
        glossary={"AOV": "Average Order Value (Total GMV / Order Count)"},
        global_guardrails=["Always use parameterized SQL queries."],
        tables={
            "orders": TableSemanticsConfig(
                owner="@checkout-eng",
                criticality="tier-1",
                tags=["pci-dss", "core"],
                guardrails=["Do not delete orders"],
                virtual_relationships=[
                    VirtualRelationshipConfig(
                        column="stripe_charge_id",
                        ref_table="charges",
                        ref_column="charge_id"
                    )
                ]
            )
        }
    )
    enriched = apply_semantics(schema, semantics_cfg)
    context_md = generate_database_context(enriched)

    assert "## Business Glossary & Domain Semantics" in context_md
    assert "AOV" in context_md
    assert "Average Order Value" in context_md
    assert "## Global AI Query Guardrails & Policies" in context_md
    assert "parameterized SQL queries" in context_md
    assert "Owner: `@checkout-eng`" in context_md
    assert "Criticality: `tier-1`" in context_md
    assert "Do not delete orders" in context_md
    assert "charges (charge_id) [Virtual]" in context_md


def test_agent_safety_rules_with_semantics():
    schema = get_base_schema()
    semantics_cfg = SemanticsConfig(
        global_guardrails=["Ensure all joins on tenant_id are enforced."],
        tables={
            "orders": TableSemanticsConfig(
                guardrails=["Never issue DELETE on orders."],
                columns={
                    "total_cents": ColumnSemanticsConfig(
                        guardrails=["total_cents must be >= 0"]
                    )
                }
            )
        }
    )
    enriched = apply_semantics(schema, semantics_cfg)
    rules = generate_safety_rules(enriched)

    assert any("Ensure all joins on tenant_id" in r for r in rules)
    assert any("Never issue DELETE on orders" in r for r in rules)
    assert any("total_cents must be >= 0" in r for r in rules)

    claude_md = generate_claude_md(enriched)
    assert "Ensure all joins on tenant_id" in claude_md

    agents_md = generate_agents_md(enriched)
    assert "Never issue DELETE on orders" in agents_md


def test_cli_glossary_command(tmp_path):
    runner = CliRunner()
    
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL);")
    conn.commit()
    conn.close()

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text(f"""
database:
  connection_url: "sqlite:///{db_file.as_posix()}"
semantics:
  glossary:
    CAC: "Customer Acquisition Cost"
    LTV: "Lifetime Value per customer"
  global_guardrails:
    - "Tenant isolation mandatory"
""")

    # 1. Text formatted output
    res = runner.invoke(cli, ["glossary", "--config", str(cfg_file)])
    assert res.exit_code == 0
    assert "Schemap Business Semantics & Glossary" in res.output
    assert "CAC" in res.output
    assert "Customer Acquisition Cost" in res.output
    assert "Tenant isolation mandatory" in res.output

    # 2. JSON formatted output
    res_json = runner.invoke(cli, ["glossary", "--config", str(cfg_file), "--json"])
    assert res_json.exit_code == 0
    import json
    data = json.loads(res_json.output)
    assert "glossary" in data
    assert data["glossary"]["CAC"] == "Customer Acquisition Cost"
    assert "Tenant isolation mandatory" in data["global_guardrails"]


def test_cli_annotate_scaffold(tmp_path):
    runner = CliRunner()
    
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE payments (id INTEGER PRIMARY KEY, total_cents INTEGER, user_email TEXT);")
    conn.commit()
    conn.close()

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text(f"""
database:
  connection_url: "sqlite:///{db_file.as_posix()}"
""")

    out_semantics = tmp_path / ".schemap" / "semantics.yaml"
    res = runner.invoke(cli, ["annotate", "--config", str(cfg_file), "--output", str(out_semantics)])
    assert res.exit_code == 0
    assert out_semantics.exists()

    content = out_semantics.read_text(encoding="utf-8")
    assert "semantics:" in content
    assert "glossary:" in content
    assert "payments:" in content
    assert "total_cents:" in content
    assert "financial" in content
    assert "currency_cents" in content
    assert "user_email:" in content
    assert "pii" in content
