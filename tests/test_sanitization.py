import pytest
from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.context import sanitize_schema_for_llm, generate_database_context
from schemap.agents import write_agent_files


def get_schema_with_pii() -> DatabaseSchemaModel:
    return DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                description="Core user records",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True),
                    ColumnModel(name="email", data_type="VARCHAR(255)"),
                    ColumnModel(name="password_hash", data_type="VARCHAR(255)"),
                    ColumnModel(name="ssn", data_type="VARCHAR(11)"),
                    ColumnModel(name="api_token", data_type="TEXT"),
                    ColumnModel(name="created_at", data_type="TIMESTAMP"),
                ],
                foreign_keys=[]
            )
        ]
    )


def test_sanitize_schema_masks_sensitive_columns():
    schema = get_schema_with_pii()
    sanitized_model, count = sanitize_schema_for_llm(schema)

    assert count == 3  # password_hash, ssn, api_token
    cols = {c.name: c for c in sanitized_model.tables[0].columns}

    # Verify normal columns remain untouched
    assert cols["email"].description is None
    assert cols["id"].primary_key is True

    # Verify sensitive columns are redacted
    assert "[REDACTED_PII" in cols["password_hash"].description
    assert "[REDACTED_PII" in cols["ssn"].description
    assert "[REDACTED_PII" in cols["api_token"].description


def test_generate_database_context_with_sanitize():
    schema = get_schema_with_pii()
    
    # 1. Without sanitize
    ctx_raw = generate_database_context(schema, sanitize=False)
    assert "Security Guardrail Active" not in ctx_raw

    # 2. With sanitize
    ctx_sanitized = generate_database_context(schema, sanitize=True)
    assert "Security Guardrail Active" in ctx_sanitized
    assert "`3` sensitive/PII columns automatically redacted" in ctx_sanitized


def test_write_agent_files_with_sanitize(tmp_path):
    schema = get_schema_with_pii()
    files = write_agent_files(schema, target_dir=str(tmp_path), targets="claude,codex", sanitize=True)
    
    claude_content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "users" in claude_content
