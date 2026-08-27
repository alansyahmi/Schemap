import pytest
from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from schemap.gate import evaluate_gate


def get_clean_schema() -> DatabaseSchemaModel:
    return DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                description="Core registered users of the platform",
                columns=[
                    ColumnModel(name="id", data_type="INTEGER", primary_key=True, is_nullable=False),
                    ColumnModel(name="email", data_type="VARCHAR(255)", is_nullable=False),
                    ColumnModel(name="full_name", data_type="VARCHAR(255)", is_nullable=True),
                ],
                foreign_keys=[]
            ),
            TableModel(
                name="orders",
                description="Customer purchases and transactions",
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


def get_degraded_schema() -> DatabaseSchemaModel:
    # No descriptions, no primary keys, no foreign keys
    return DatabaseSchemaModel(
        tables=[
            TableModel(
                name="tbl1",
                description=None,
                columns=[
                    ColumnModel(name="c1", data_type="TEXT", primary_key=False),
                    ColumnModel(name="c2", data_type="TEXT", primary_key=False),
                ],
                foreign_keys=[]
            ),
            TableModel(
                name="tbl2",
                description=None,
                columns=[
                    ColumnModel(name="d1", data_type="TEXT", primary_key=False),
                ],
                foreign_keys=[]
            )
        ]
    )


def test_gate_pass_on_clean_schema():
    schema = get_clean_schema()
    result = evaluate_gate(current_schema=schema, min_score=80)
    assert result.passed is True
    assert result.score >= 80
    assert len(result.failure_reasons) == 0


def test_gate_fail_on_degraded_schema():
    schema = get_degraded_schema()
    result = evaluate_gate(current_schema=schema, min_score=80)
    assert result.passed is False
    assert result.score < 80
    assert len(result.failure_reasons) > 0
    assert "below the required threshold" in result.failure_reasons[0]


def test_gate_detects_breaking_changes():
    old_schema = get_clean_schema()
    
    # New schema drops the "orders" table
    new_schema = DatabaseSchemaModel(
        tables=[old_schema.tables[0]]
    )

    # 1. Without fail_on_breaking flag
    res_lenient = evaluate_gate(current_schema=new_schema, previous_schema=old_schema, fail_on_breaking=False)
    assert len(res_lenient.breaking_changes) > 0

    # 2. With fail_on_breaking flag
    res_strict = evaluate_gate(current_schema=new_schema, previous_schema=old_schema, fail_on_breaking=True)
    assert res_strict.passed is False
    assert any("breaking schema changes" in reason for reason in res_strict.failure_reasons)
