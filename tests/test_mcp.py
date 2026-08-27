import pytest
import json
from pathlib import Path
from click.testing import CliRunner

from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.mcp import (
    dispatch_mcp_request, execute_tool, generate_mcp_config_snippet, MCP_TOOLS
)
from schemap.cli import cli


def get_test_schema() -> DatabaseSchemaModel:
    return DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                description="User accounts and credentials",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="email", data_type="VARCHAR(255)", is_nullable=False, tags=["pii"]),
                    ColumnModel(name="password_hash", data_type="TEXT", is_nullable=False, tags=["secret"]),
                ],
                foreign_keys=[]
            ),
            TableModel(
                name="orders",
                description="Order transactions",
                owner="@checkout-team",
                criticality="tier-1",
                guardrails=["Never issue DELETE queries against orders."],
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="user_id", data_type="INTEGER", is_nullable=False),
                    ColumnModel(name="total_cents", data_type="INTEGER", is_nullable=False, semantic_type="currency_cents"),
                    ColumnModel(name="stripe_charge_id", data_type="VARCHAR(255)", is_nullable=True),
                    ColumnModel(name="deleted_at", data_type="TIMESTAMP", is_nullable=True),
                ],
                foreign_keys=[
                    ForeignKeyModel(column_name="user_id", foreign_table_name="users", foreign_column_name="id")
                ],
                virtual_relationships=[
                    ForeignKeyModel(column_name="stripe_charge_id", foreign_table_name="stripe_charges", foreign_column_name="id")
                ]
            ),
            TableModel(
                name="stripe_charges",
                description="Third-party payment ledger",
                columns=[
                    ColumnModel(name="id", data_type="VARCHAR(255)", primary_key=True, is_nullable=False),
                    ColumnModel(name="amount", data_type="INTEGER", is_nullable=False)
                ],
                foreign_keys=[]
            )
        ],
        glossary={
            "GMV": "Gross Merchandise Value",
            "AOV": "Average Order Value"
        },
        global_guardrails=[
            "All timestamps are in UTC."
        ]
    )


def test_mcp_initialize():
    schema = get_test_schema()
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    resp = dispatch_mcp_request(req, schema)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert "protocolVersion" in resp["result"]
    assert resp["result"]["serverInfo"]["name"] == "schemap-mcp"


def test_mcp_tools_list():
    schema = get_test_schema()
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    resp = dispatch_mcp_request(req, schema)
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "schemap_get_schema" in tool_names
    assert "schemap_get_join_path" in tool_names
    assert "schemap_validate_query" in tool_names
    assert "schemap_get_glossary" in tool_names
    assert "schemap_check_blast_radius" in tool_names


def test_mcp_tool_get_schema():
    schema = get_test_schema()
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "schemap_get_schema",
            "arguments": {
                "tables": ["orders"],
                "sanitize": True
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    text = resp["result"]["content"][0]["text"]
    assert "orders" in text
    assert "Database Context Engine Output" in text


def test_mcp_tool_get_join_path_virtual_relation():
    schema = get_test_schema()
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "schemap_get_join_path",
            "arguments": {
                "from_table": "orders",
                "to_table": "stripe_charges"
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    text = resp["result"]["content"][0]["text"]
    assert "JOIN stripe_charges ON orders.stripe_charge_id = stripe_charges.id" in text


def test_mcp_tool_validate_query():
    schema = get_test_schema()

    # Query with missing table & soft-delete omission
    bad_sql = "SELECT * FROM orders JOIN missing_table ON orders.id = missing_table.order_id WHERE email = 'test';"
    req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "schemap_validate_query",
            "arguments": {
                "sql": bad_sql
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    text = resp["result"]["content"][0]["text"]
    assert "Unknown table `missing_table`" in text
    assert "soft-delete" in text
    assert "Never issue DELETE queries against orders" in text


def test_mcp_tool_get_glossary():
    schema = get_test_schema()
    req = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "schemap_get_glossary",
            "arguments": {
                "term": "GMV"
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    text = resp["result"]["content"][0]["text"]
    assert "GMV" in text
    assert "Gross Merchandise Value" in text


def test_mcp_tool_blast_radius():
    schema = get_test_schema()
    req = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "schemap_check_blast_radius",
            "arguments": {
                "target_table": "users"
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    text = resp["result"]["content"][0]["text"]
    assert "Blast Radius Report for Table: `users`" in text
    assert "`orders.user_id` references this table" in text


def test_cli_mcp_snippet():
    runner = CliRunner()
    res = runner.invoke(cli, ["mcp", "--snippet", "cursor"])
    assert res.exit_code == 0
    assert "mcpServers" in res.output
    assert "schemap" in res.output

    res_claude = runner.invoke(cli, ["mcp", "--snippet", "claude"])
    assert res_claude.exit_code == 0
    assert "schemap.yaml" in res_claude.output
