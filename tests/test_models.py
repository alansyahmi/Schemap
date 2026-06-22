import pytest
from pydantic import ValidationError
from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel

def test_models_parse_valid_payload():
    """Verify that models.py successfully parses a valid raw dictionary payload."""
    payload = {
        "tables": [
            {
                "name": "users",
                "description": "User accounts",
                "columns": [
                    {
                        "name": "id",
                        "data_type": "integer",
                        "is_nullable": False,
                        "primary_key": True,
                        "description": "Primary key"
                    },
                    {
                        "name": "email",
                        "data_type": "character varying",
                        "is_nullable": False,
                        "primary_key": False,
                        "description": None
                    }
                ],
                "foreign_keys": []
            }
        ]
    }
    
    model = DatabaseSchemaModel(**payload)
    assert len(model.tables) == 1
    assert model.tables[0].name == "users"
    assert len(model.tables[0].columns) == 2
    assert model.tables[0].columns[0].name == "id"
    assert model.tables[0].columns[0].primary_key is True

def test_models_invalid_type_error():
    """Verify that models.py throws a validation error if data is malformed."""
    payload = {
        "tables": [
            {
                "name": "users",
                "columns": [
                    {
                        "name": "id",
                        # Missing data_type which is required
                        "is_nullable": False
                    }
                ]
            }
        ]
    }
    
    with pytest.raises(ValidationError):
        DatabaseSchemaModel(**payload)
