import pytest
from schemap.extractor import extract_schema

def test_extract_schema_routing_postgres(mocker):
    """Verify that postgres URLs route to the postgres extractor."""
    mock_postgres = mocker.patch('schemap.extractor._extract_postgres')
    extract_schema("postgresql://user:pass@localhost/db", [])
    mock_postgres.assert_called_once()

def test_extract_schema_routing_libsql(mocker):
    """Verify that libsql URLs route to the libsql extractor."""
    mock_libsql = mocker.patch('schemap.extractor._extract_libsql')
    extract_schema("libsql://my-db.turso.io", [])
    mock_libsql.assert_called_once()
    
def test_extract_schema_routing_sqlite(mocker):
    """Verify that sqlite URLs route to the libsql extractor."""
    mock_libsql = mocker.patch('schemap.extractor._extract_libsql')
    extract_schema("sqlite:///local.db", [])
    mock_libsql.assert_called_once()

def test_extract_schema_invalid_scheme():
    """Verify that invalid schemes raise a ValueError."""
    with pytest.raises(ValueError):
        extract_schema("mssql://user:pass@localhost/db", [])

def test_extract_schema_routing_mysql(mocker):
    """Verify that mysql URLs route to the mysql extractor."""
    mock_mysql = mocker.patch('schemap.extractor._extract_mysql')
    extract_schema("mysql://user:pass@localhost/db", [])
    mock_mysql.assert_called_once()

def test_extract_schema_routing_oracle(mocker):
    """Verify that oracle URLs route to the oracle extractor."""
    mock_oracle = mocker.patch('schemap.extractor._extract_oracle')
    extract_schema("oracle://user:pass@localhost:1521/XEPDB1", [])
    mock_oracle.assert_called_once()
