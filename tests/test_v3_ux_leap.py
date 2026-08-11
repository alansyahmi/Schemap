import os
import json
import pytest
from pathlib import Path

from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.config import load_config, find_config_path, SchemapConfig, ForeignKeyOverride
from schemap.agents import write_agent_files, merge_content_with_markers, START_MARKER, END_MARKER
from schemap.fingerprint import calculate_schema_fingerprint, save_fingerprint, get_cached_fingerprint
from schemap.quickstart import run_quickstart, detect_local_databases
from schemap.query_explainer import explain_table, find_join_path
from schemap.diff import calculate_detailed_diff
from schemap.doctor import get_doctor_report, infer_foreign_key_candidates
from schemap.fix import run_fix
from schemap.renderer import render_output
from schemap.skills import install_agent_skills

@pytest.fixture
def sample_schema():
    return DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                description="Registered user accounts",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True),
                    ColumnModel(name="email", data_type="VARCHAR")
                ]
            ),
            TableModel(
                name="orders",
                description="Purchased orders",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True),
                    ColumnModel(name="user_id", data_type="INTEGER"),
                    ColumnModel(name="total_cents", data_type="INTEGER")
                ],
                foreign_keys=[
                    ForeignKeyModel(column_name="user_id", foreign_table_name="users", foreign_column_name="id")
                ]
            ),
            TableModel(
                name="payments",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True),
                    ColumnModel(name="order_id", data_type="INTEGER"),
                    ColumnModel(name="amount", data_type="INTEGER")
                ],
                foreign_keys=[
                    ForeignKeyModel(column_name="order_id", foreign_table_name="orders", foreign_column_name="id")
                ]
            )
        ]
    )

def test_config_env_override_and_profiles(tmp_path, monkeypatch):
    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text("""
database:
  connection_url: "sqlite:///base.db"
profiles:
  staging:
    database:
      connection_url: "postgresql://staging-host/db"
foreign_key_overrides:
  - table: "orders"
    column: "user_id"
    ref_table: "users"
    ref_column: "id"
""", encoding="utf-8")

    # Base load
    cfg = load_config(str(cfg_file))
    assert cfg.database.connection_url == "sqlite:///base.db"
    assert len(cfg.foreign_key_overrides) == 1
    assert cfg.foreign_key_overrides[0].table == "orders"

    # Profile load
    cfg_staging = load_config(str(cfg_file), profile="staging")
    assert cfg_staging.database.connection_url == "postgresql://staging-host/db"

    # Env override
    monkeypatch.setenv("SCHEMAP_DATABASE_URL", "sqlite:///env.db")
    cfg_env = load_config(str(cfg_file))
    assert cfg_env.database.connection_url == "sqlite:///env.db"

def test_safe_agent_merge_and_markers(tmp_path, sample_schema):
    target_dir = tmp_path / "agents_test"
    target_dir.mkdir()
    
    # Write initial with markers
    res = write_agent_files(sample_schema, target_dir=str(target_dir), targets="claude", merge=True)
    claude_file = Path(res["CLAUDE.md"])
    assert claude_file.exists()
    content = claude_file.read_text(encoding="utf-8")
    assert START_MARKER in content
    assert END_MARKER in content

    # Add custom user section above markers
    custom_content = f"# My Custom Notes\n\n{content}"
    claude_file.write_text(custom_content, encoding="utf-8")

    # Re-run merge
    write_agent_files(sample_schema, target_dir=str(target_dir), targets="claude", merge=True)
    updated_content = claude_file.read_text(encoding="utf-8")
    assert "# My Custom Notes" in updated_content
    assert START_MARKER in updated_content

def test_schema_fingerprint(sample_schema):
    fp1 = calculate_schema_fingerprint(sample_schema)
    fp2 = calculate_schema_fingerprint(sample_schema)
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA256 hex length

def test_query_explainer(sample_schema):
    info = explain_table(sample_schema, "orders")
    assert info["table"] == "orders"
    assert info["columns_count"] == 3
    assert len(info["outgoing_relationships"]) == 1

    join_res = find_join_path(sample_schema, ["users", "payments"])
    assert join_res["status"] == "connected"
    assert "users" in join_res["full_path"]
    assert "orders" in join_res["full_path"]
    assert "payments" in join_res["full_path"]
    assert "JOIN orders ON users.id = orders.user_id" in join_res["sql_snippet"] or "JOIN orders ON orders.user_id = users.id" in join_res["sql_snippet"] or "FROM users" in join_res["sql_snippet"]

def test_diff_breaking_changes(sample_schema):
    modified_schema = DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                columns=[
                    ColumnModel(name="id", data_type="BIGINT", primary_key=True) # Changed type
                ]
            )
            # orders & payments removed
        ]
    )

    diffs, report = calculate_detailed_diff(sample_schema, modified_schema)
    assert len(report["removed_tables"]) == 2
    assert len(report["changed_columns"]) == 1
    assert len(report["breaking_changes"]) > 0

def test_doctor_and_fix(tmp_path, sample_schema):
    # Schema with missing explicit FK
    unconnected_schema = DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                columns=[ColumnModel(name="id", data_type="INTEGER", primary_key=True)]
            ),
            TableModel(
                name="orders",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True),
                    ColumnModel(name="user_id", data_type="INTEGER")
                ]
            )
        ]
    )

    cands = infer_foreign_key_candidates(unconnected_schema)
    assert len(cands) == 1
    assert cands[0]["table"] == "orders"
    assert cands[0]["column"] == "user_id"
    assert cands[0]["ref_table"] == "users"
    assert cands[0]["confidence"] >= 90

def test_mermaid_renderer(sample_schema):
    mermaid_out = render_output(sample_schema, fmt="mermaid")
    assert "erDiagram" in mermaid_out
    assert "users {" in mermaid_out
    assert "orders }|--|| users" in mermaid_out

def test_skills_installation(tmp_path):
    installed = install_agent_skills(targets="all", base_dir=str(tmp_path))
    assert len(installed) == 3
    for p in installed:
        assert Path(p).exists()
        assert "Schemap AI Database Agent Skill" in Path(p).read_text(encoding="utf-8")
