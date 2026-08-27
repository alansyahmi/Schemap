import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.roi import calculate_team_roi, generate_roi_report
from schemap.cli import cli


def get_sample_schema() -> DatabaseSchemaModel:
    return DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                description="User accounts",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="email", data_type="VARCHAR(255)", is_nullable=False),
                ],
                foreign_keys=[]
            ),
            TableModel(
                name="orders",
                description="Orders placed by users",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="user_id", data_type="INTEGER", is_nullable=False),
                    ColumnModel(name="total_cents", data_type="INTEGER", is_nullable=False),
                ],
                foreign_keys=[
                    ForeignKeyModel(column_name="user_id", foreign_table_name="users", foreign_column_name="id")
                ]
            )
        ],
        glossary={"GMV": "Gross Merchandise Value"}
    )


def test_calculate_team_roi():
    schema = get_sample_schema()
    roi = calculate_team_roi(
        schema_model=schema,
        team_size=10,
        prompts_per_dev_day=50,
        dev_hourly_rate=85.0
    )

    assert "team_parameters" in roi
    assert roi["team_parameters"]["team_size"] == 10
    assert roi["team_parameters"]["total_annual_prompts"] == 10 * 50 * 250

    te = roi["token_economics"]
    assert te["raw_schema_tokens"] > te["schemap_compressed_tokens"]
    assert te["annual_token_savings_usd"] > 0

    pe = roi["productivity_economics"]
    assert pe["total_annual_hours_saved"] == 10 * 4.0 * 12
    assert pe["annual_productivity_value_usd"] > 0

    rs = roi["roi_summary"]
    assert rs["total_annual_value_usd"] > rs["schemap_annual_cost_usd"]
    assert rs["net_economic_benefit_usd"] > 0
    assert "x" in rs["roi_multiple"]


def test_generate_roi_report_markdown():
    schema = get_sample_schema()
    roi = calculate_team_roi(schema, team_size=12)
    report = generate_roi_report(roi, project_name="ECommerce Platform")

    assert "Schemap Enterprise ROI & Business Impact Report" in report
    assert "ECommerce Platform" in report
    assert "Executive Value Summary" in report
    assert "Direct LLM Token Savings" in report
    assert "Engineering Velocity Gain" in report
    assert "Schemap Team Investment" in report


def test_cli_roi_command(tmp_path):
    runner = CliRunner()
    from schemap.license import _write_cache
    _write_cache("TEST-TEAM-KEY", plan_tier="team")
    
    import sqlite3
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL);")
    cur.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, amount INTEGER);")
    conn.commit()
    conn.close()

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text(f"""
database:
  connection_url: "sqlite:///{db_file.as_posix()}"
domain:
  project_name: "FinTech Platform"
license_key: "TEST-TEAM-KEY"
""")

    report_out = tmp_path / "roi_summary.md"
    res = runner.invoke(cli, [
        "roi",
        "--config", str(cfg_file),
        "--team-size", "15",
        "--output-report", str(report_out)
    ])

    assert res.exit_code == 0
    assert "Schemap Enterprise ROI Dashboard (15 Developers)" in res.output
    assert "Annual Economic ROI" in res.output
    assert report_out.exists()

    # JSON output test
    res_json = runner.invoke(cli, [
        "roi",
        "--config", str(cfg_file),
        "--json"
    ])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert "roi_summary" in data
    assert "token_economics" in data

