import pytest
from pathlib import Path
from click.testing import CliRunner
from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.gate import evaluate_gate, generate_gate_markdown_report
from schemap.cli import cli


def get_ecom_schema() -> DatabaseSchemaModel:
    return DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                description="Core customer accounts and auth details",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="email", data_type="VARCHAR(255)", is_nullable=False),
                    ColumnModel(name="full_name", data_type="VARCHAR(255)", is_nullable=True),
                ],
                foreign_keys=[]
            ),
            TableModel(
                name="orders",
                description="Customer checkout orders and purchase ledger",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="user_id", data_type="INTEGER", is_nullable=False),
                    ColumnModel(name="total_cents", data_type="INTEGER", is_nullable=False),
                ],
                foreign_keys=[
                    ForeignKeyModel(column_name="user_id", foreign_table_name="users", foreign_column_name="id")
                ]
            )
        ]
    )


def test_markdown_report_generation_passed():
    schema = get_ecom_schema()
    res = evaluate_gate(current_schema=schema, min_score=80)
    assert res.passed is True
    
    report = generate_gate_markdown_report(res, project_name="ECommerce Core")
    assert "### 🟢 Schemap AI Quality Gate: PASSED" in report
    assert "ECommerce Core" in report
    assert "Quality Gate Passed" in report
    assert "AI Readiness & Schema Governance Scorecard" in report
    assert f"`{res.score}/100`" in report
    assert "Documentation Coverage" in report
    assert "Primary Key Integrity" in report
    assert "Explicit Foreign Keys" in report


def test_markdown_report_generation_failed_with_blast_radius():
    old_schema = get_ecom_schema()
    # Degrade: remove orders table and modify users.email to integer
    new_schema = DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                description=None,
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=False, is_nullable=False),
                    ColumnModel(name="email", data_type="INTEGER", is_nullable=False),
                ],
                foreign_keys=[]
            )
        ]
    )

    res = evaluate_gate(
        current_schema=new_schema,
        previous_schema=old_schema,
        min_score=85,
        fail_on_breaking=True
    )
    assert res.passed is False
    assert len(res.failure_reasons) > 0

    report = generate_gate_markdown_report(res, project_name="ECommerce Core")
    assert "### 🔴 Schemap AI Quality Gate: BLOCKED" in report
    assert "Pull Request Gate Violations" in report
    assert "Blast Radius & Agent Impact Analysis" in report
    assert "HIGH" in report
    assert "Dropped table `orders`" in report
    assert "Type mutation on `users.email`" in report
    assert "Recommended Actions to Raise AI Readiness Score" in report


def test_cli_gate_command_with_output_report(tmp_path):
    runner = CliRunner()
    from schemap.license import _write_cache
    _write_cache("TEST-TEAM-KEY", plan_tier="team")
    
    # Create sample sqlite database
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL);")
    conn.commit()
    conn.close()

    # Create schemap.yaml
    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text(f"""
database:
  connection_url: "sqlite:///{db_file.as_posix()}"
domain:
  project_name: "Test CLI App"
gate:
  min_score: 50
  fail_on_breaking: false
license_key: "TEST-TEAM-KEY"
""")

    report_file = tmp_path / "pr_report.md"
    result = runner.invoke(cli, [
        "gate",
        "--config", str(cfg_file),
        "--output-report", str(report_file),
        "--no-step-summary"
    ])

    if result.exit_code != 0:
        print("Output:", result.output)
    assert result.exit_code == 0
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "Schemap AI Quality Gate" in content
    assert "Test CLI App" in content


def test_cli_gate_command_json_output(tmp_path):
    runner = CliRunner()
    from schemap.license import _write_cache
    _write_cache("TEST-TEAM-KEY", plan_tier="team")
    
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT);")
    conn.commit()
    conn.close()

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text(f"""
database:
  connection_url: "sqlite:///{db_file.as_posix()}"
gate:
  min_score: 10
license_key: "TEST-TEAM-KEY"
""")

    result = runner.invoke(cli, [
        "gate",
        "--config", str(cfg_file),
        "--json",
        "--no-step-summary"
    ])

    if result.exit_code != 0:
        print("Output:", result.output)
    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert "passed" in data
    assert "score" in data
    assert "metrics" in data
    assert "blast_radius" in data

