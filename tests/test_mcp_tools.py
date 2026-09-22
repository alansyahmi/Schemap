import pytest
from schemap.models import (
    DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
)
from schemap.mcp import (
    dispatch_mcp_request, execute_tool, MCP_TOOLS
)


def get_contract_test_schema() -> DatabaseSchemaModel:
    """Fixture schema representing a multi-tenant SaaS operational database."""
    return DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                description="User accounts",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="email", data_type="VARCHAR(255)", is_nullable=False),
                    ColumnModel(name="org_id", data_type="INTEGER", is_nullable=False),
                    ColumnModel(name="deleted_at", data_type="TIMESTAMP", is_nullable=True),
                ],
                foreign_keys=[]
            ),
            TableModel(
                name="orders",
                description="Orders and invoices",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="user_id", data_type="INTEGER", is_nullable=False),
                    ColumnModel(name="org_id", data_type="INTEGER", is_nullable=False),
                    ColumnModel(name="total_cents", data_type="INTEGER", is_nullable=False),
                    ColumnModel(name="deleted_at", data_type="TIMESTAMP", is_nullable=True),
                ],
                foreign_keys=[
                    ForeignKeyModel(column_name="user_id", foreign_table_name="users", foreign_column_name="id")
                ]
            )
        ],
        glossary={
            "ARR": "Annual Recurring Revenue",
        },
        global_guardrails=[
            "Never perform destructive mutations in analytical workflows."
        ]
    )


def test_mcp_server_initialize_version_4():
    """Verify serverInfo reports version 4.0.0."""
    schema = get_contract_test_schema()
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    resp = dispatch_mcp_request(req, schema)
    assert resp is not None
    assert resp["jsonrpc"] == "2.0"
    server_info = resp["result"]["serverInfo"]
    assert server_info["name"] == "schemap-mcp"
    assert server_info["version"] == "4.0.0"


def test_mcp_tools_list_contract():
    """Verify tools/list exposes ground, verify, patch with outputSchema and agent copy."""
    schema = get_contract_test_schema()
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    resp = dispatch_mcp_request(req, schema)
    tools = {t["name"]: t for t in resp["result"]["tools"]}

    # 1. Check tool presence
    assert "schemap_ground" in tools
    assert "schemap_verify" in tools
    assert "schemap_patch" in tools

    # 2. Check agent-facing guidance copy
    assert "before writing SQL" in tools["schemap_ground"]["description"]
    assert "before executing" in tools["schemap_verify"]["description"]
    assert "explicitly" in tools["schemap_patch"]["description"]

    # 3. Check outputSchema declaration on all three tools
    for tool_name in ["schemap_ground", "schemap_verify", "schemap_patch"]:
        tool = tools[tool_name]
        assert "outputSchema" in tool, f"{tool_name} must declare outputSchema"
        assert tool["outputSchema"]["type"] == "object"
        assert "properties" in tool["outputSchema"]


def test_mcp_ground_dual_payload_and_provenance():
    """Verify schemap_ground returns non-empty markdown and matching structuredContent."""
    schema = get_contract_test_schema()
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "schemap_ground",
            "arguments": {
                "question": "What was total revenue?",
                "tenant_id": "42"
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    result = resp["result"]

    # 1. Non-empty markdown enforcement
    assert "content" in result
    assert len(result["content"]) >= 1
    assert result["content"][0]["type"] == "text"
    assert len(result["content"][0]["text"].strip()) > 0
    assert "[INFERRED" in result["content"][0]["text"] or "[DECLARED" in result["content"][0]["text"]

    # 2. Machine-readable structuredContent
    assert "structuredContent" in result
    sc = result["structuredContent"]
    assert sc["question"] == "What was total revenue?"
    assert isinstance(sc["target_tables"], list)
    assert len(sc["target_tables"]) > 0
    assert isinstance(sc["mandatory_filters"], list)
    # Check that soft delete filter and tenant filter are present
    assert any("deleted_at IS NULL" in f for f in sc["mandatory_filters"])
    assert any("42" in f for f in sc["mandatory_filters"])
    assert isinstance(sc["measures"], list)
    assert isinstance(sc["provenance"], dict)
    assert "prompt_instructions" in sc


def test_mcp_verify_policy_complete_select():
    """Verify policy-complete SELECT query is allowed."""
    schema = get_contract_test_schema()
    safe_sql = "SELECT id, total_cents FROM orders WHERE org_id = 42 AND deleted_at IS NULL"
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "schemap_verify",
            "arguments": {
                "sql": safe_sql,
                "tenant_id": "42"
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    result = resp["result"]

    assert len(result["content"]) >= 1
    assert "ALLOWED" in result["content"][0]["text"]

    sc = result["structuredContent"]
    assert sc["status"] == "allow"
    assert sc["passed"] is True
    assert len(sc["violations"]) == 0
    assert sc["patched_sql"] is None
    assert sc["patch_requested"] is False


def test_mcp_verify_destructive_mutation_denied():
    """Verify DELETE is rejected by default."""
    schema = get_contract_test_schema()
    delete_sql = "DELETE FROM users WHERE id = 1"
    req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "schemap_verify",
            "arguments": {
                "sql": delete_sql
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    result = resp["result"]

    assert "REJECTED (Deny-by-Default)" in result["content"][0]["text"]
    sc = result["structuredContent"]
    assert sc["status"] == "reject"
    assert sc["passed"] is False
    assert any("Delete" in v or "forbidden" in v for v in sc["violations"])
    assert sc["patched_sql"] is None


def test_mcp_verify_destructive_mutation_unpatchable_even_with_patch_flag():
    """Verify destructive DELETE remains rejected and unpatchable even when patch=True."""
    schema = get_contract_test_schema()
    delete_sql = "DELETE FROM users WHERE id = 1"
    req = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "schemap_verify",
            "arguments": {
                "sql": delete_sql,
                "patch": True
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    result = resp["result"]
    sc = result["structuredContent"]

    # Destructive mutations can never be auto-patched into existence
    assert sc["status"] == "reject"
    assert sc["passed"] is False
    assert sc["patched_sql"] is None
    assert sc["patch_requested"] is True


def test_mcp_verify_soft_delete_violation_patch_false():
    """Verify SELECT missing soft-delete is rejected and not rewritten when patch=False."""
    schema = get_contract_test_schema()
    unfiltered_sql = "SELECT id FROM orders WHERE org_id = 42"
    req = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "schemap_verify",
            "arguments": {
                "sql": unfiltered_sql,
                "tenant_id": "42",
                "patch": False
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    result = resp["result"]
    sc = result["structuredContent"]

    assert sc["status"] == "reject"
    assert sc["passed"] is False
    assert any("Soft-Delete" in v or "deleted_at" in v for v in sc["violations"])
    assert sc["patched_sql"] is None
    assert sc["patch_requested"] is False


def test_mcp_verify_soft_delete_violation_patch_true():
    """Verify SELECT missing soft-delete returns patched_sql when patch=True."""
    schema = get_contract_test_schema()
    unfiltered_sql = "SELECT id FROM orders WHERE org_id = 42"
    req = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {
            "name": "schemap_verify",
            "arguments": {
                "sql": unfiltered_sql,
                "tenant_id": "42",
                "patch": True
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    result = resp["result"]
    sc = result["structuredContent"]

    assert sc["passed"] is False  # Original query had violations
    assert sc["patch_requested"] is True
    assert sc["patched_sql"] is not None
    assert "deleted_at IS NULL" in sc["patched_sql"]


def test_mcp_patch_tool_explicit():
    """Verify schemap_patch explicitly patches missing filters on SELECT."""
    schema = get_contract_test_schema()
    unfiltered_sql = "SELECT id FROM orders"
    req = {
        "jsonrpc": "2.0",
        "id": 9,
        "method": "tools/call",
        "params": {
            "name": "schemap_patch",
            "arguments": {
                "sql": unfiltered_sql,
                "tenant_id": "42"
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    result = resp["result"]
    sc = result["structuredContent"]

    assert sc["status"] == "allow"
    assert sc["passed"] is True
    assert sc["patch_applied"] is True
    assert sc["patched_sql"] is not None
    assert "deleted_at IS NULL" in sc["patched_sql"]
    assert "org_id = 42" in sc["patched_sql"] or "org_id = '42'" in sc["patched_sql"]


def test_mcp_patch_tool_rejects_destructive_mutation():
    """Verify schemap_patch rejects unpatchable DROP TABLE mutation."""
    schema = get_contract_test_schema()
    drop_sql = "DROP TABLE users"
    req = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "schemap_patch",
            "arguments": {
                "sql": drop_sql,
                "tenant_id": "42"
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    result = resp["result"]
    sc = result["structuredContent"]

    assert sc["status"] == "reject"
    assert sc["passed"] is False
    assert sc["patch_applied"] is False
    assert sc["patched_sql"] is None


def test_mcp_patch_tool_rejects_mixed_violation_with_remaining_cartesian_join():
    """
    P0 Regression Test: If a query has a patchable violation (missing tenant filter)
    AND an unpatchable violation (Cartesian join), schemap_patch must REJECT
    because the re-validated query still contains violations.
    """
    schema = get_contract_test_schema()
    mixed_sql = "SELECT * FROM orders, users"
    req = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {
            "name": "schemap_patch",
            "arguments": {
                "sql": mixed_sql,
                "tenant_id": "42"
            }
        }
    }
    resp = dispatch_mcp_request(req, schema)
    result = resp["result"]
    sc = result["structuredContent"]

    # Must reject because Cartesian join remains even after WHERE injection
    assert sc["status"] == "reject"
    assert sc["passed"] is False
    assert sc["patch_applied"] is False
    assert sc["patched_sql"] is None
    assert any("Cartesian" in v for v in sc["violations"])
