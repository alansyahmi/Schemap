import pytest
import json
from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.doctor import get_doctor_report, render_ascii_bar
from schemap.benchmark import calculate_benchmark

@pytest.fixture
def sample_schema():
    users = TableModel(
        name="users",
        description="User accounts table",
        columns=[
            ColumnModel(name="id", data_type="INTEGER", primary_key=True),
            ColumnModel(name="email", data_type="VARCHAR")
        ],
        foreign_keys=[]
    )
    orders = TableModel(
        name="orders",
        description="Orders table",
        columns=[
            ColumnModel(name="id", data_type="INTEGER", primary_key=True),
            ColumnModel(name="user_id", data_type="INTEGER")
        ],
        foreign_keys=[
            ForeignKeyModel(column_name="user_id", foreign_table_name="users", foreign_column_name="id")
        ]
    )
    return DatabaseSchemaModel(tables=[users, orders])

def test_ascii_bar_rendering():
    bar_50 = render_ascii_bar(50)
    assert "50/100" in bar_50
    assert "#" in bar_50 and "-" in bar_50

def test_doctor_report(sample_schema):
    raw_tables = [
        {"name": "users", "columns": [{"name": "id", "data_type": "INT"}]},
        {"name": "orders", "columns": [{"name": "id", "data_type": "INT"}], "foreign_keys": [{"column": "user_id", "ref_table": "users", "ref_column": "id"}]}
    ]
    report = get_doctor_report(sample_schema, raw_tables, unresolved_abbrs=[])
    assert report["status"] == "ok"
    assert report["tables_count"] == 2
    assert report["relationships_count"] == 1
    assert "progress_bar" in report

def test_benchmark_calculation(sample_schema):
    raw_tables = [
        {"name": "users", "columns": [{"name": "id", "data_type": "INT"}]},
        {"name": "orders", "columns": [{"name": "id", "data_type": "INT"}]}
    ]
    bench = calculate_benchmark(sample_schema, raw_tables)
    assert "context_efficiency" in bench
    assert "raw_sql_tokens" in bench["context_efficiency"]
    assert "reduction_percentage" in bench["context_efficiency"]
