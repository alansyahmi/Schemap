import pytest
from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel
from schemap.enrichment import apply_heuristics, apply_description_overrides
from schemap.config import TableOverride, ColumnOverride

def test_ignore_abbreviations():
    # Setup database model with short column name 'abc' and 'xyz'
    schema = DatabaseSchemaModel(
        tables=[
            TableModel(
                name="dictionary",
                columns=[
                    ColumnModel(name="abc", data_type="text"),
                    ColumnModel(name="xyz", data_type="text"),
                    ColumnModel(name="qwe", data_type="text") # should trigger warning
                ]
            )
        ]
    )
    
    # Run heuristics without whitelist
    _, unresolved_before = apply_heuristics(schema.model_copy(deep=True), ignore_abbreviations=[])
    assert "abc" in unresolved_before
    assert "xyz" in unresolved_before
    assert "qwe" in unresolved_before

    # Run heuristics with whitelist ignoring 'abc' and 'xyz'
    _, unresolved_after = apply_heuristics(
        schema.model_copy(deep=True), 
        ignore_abbreviations=["abc", "xyz"]
    )
    assert "abc" not in unresolved_after
    assert "xyz" not in unresolved_after
    assert "qwe" in unresolved_after # qwe should still be flagged

def test_apply_description_overrides():
    schema = DatabaseSchemaModel(
        tables=[
            TableModel(
                name="users",
                description="Original description",
                business_name="Original Name",
                columns=[
                    ColumnModel(
                        name="pos", 
                        data_type="integer", 
                        description="Original col description",
                        business_name="Original Col Name"
                    )
                ]
            )
        ]
    )
    
    overrides = {
        "users": TableOverride(
            description="Custom overridden description",
            business_name="User Profile",
            columns={
                "pos": ColumnOverride(
                    description="Position override details",
                    business_name="Grid Position"
                )
            }
        )
    }
    
    result = apply_description_overrides(schema, overrides)
    
    # Assert overrides are correctly applied
    assert result.tables[0].description == "Custom overridden description"
    assert result.tables[0].business_name == "User Profile"
    assert result.tables[0].columns[0].description == "Position override details"
    assert result.tables[0].columns[0].business_name == "Grid Position"
