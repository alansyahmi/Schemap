"""Tests for PostgreSQL Multi-Schema Extraction and Cross-Schema Foreign Keys."""

from unittest.mock import patch, MagicMock
from schemap.extractor import _extract_postgres, extract_schema
from schemap.config import DatabaseConfig


def test_database_config_schemas_field():
    """Verify DatabaseConfig defaults to ['public'] and accepts custom schemas."""
    cfg = DatabaseConfig(connection_url="postgresql://localhost/db")
    assert cfg.schemas == ["public"]

    custom_cfg = DatabaseConfig(
        connection_url="postgresql://localhost/db",
        schemas=["public", "auth", "billing", "analytics"]
    )
    assert len(custom_cfg.schemas) == 4
    assert "billing" in custom_cfg.schemas

    # Verify comma-separated string input is parsed into a clean list
    csv_cfg = DatabaseConfig(
        connection_url="postgresql://localhost/db",
        schemas="public, auth, billing, analytics"
    )
    assert csv_cfg.schemas == ["public", "auth", "billing", "analytics"]

    # Verify edge cases like extra whitespace, empty entries
    edge_cfg = DatabaseConfig(
        connection_url="postgresql://localhost/db",
        schemas="  public,  auth,  "
    )
    assert edge_cfg.schemas == ["public", "auth"]


@patch("psycopg.connect")
def test_postgres_multi_schema_extraction(mock_connect):
    """Verify multi-schema extraction qualifies table names and resolves cross-schema FKs."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    # Mock tables across public, auth, and billing schemas
    tables_data = [
        ("auth", "users", "User authentication accounts"),
        ("billing", "subscriptions", "Customer billing plans"),
        ("billing", "invoices", "Billing invoices"),
        ("public", "products", "Store catalog products"),
    ]

    # Mock columns
    columns_data = [
        ("auth", "users", "id", "uuid", "NO", "Primary user ID", True),
        ("auth", "users", "email", "varchar", "NO", "User email", False),
        ("billing", "subscriptions", "id", "uuid", "NO", "Subscription ID", True),
        ("billing", "subscriptions", "user_id", "uuid", "NO", "FK to auth.users", False),
        ("billing", "invoices", "id", "uuid", "NO", "Invoice ID", True),
        ("billing", "invoices", "subscription_id", "uuid", "NO", "FK to billing.subscriptions", False),
        ("public", "products", "id", "uuid", "NO", "Product ID", True),
        ("public", "products", "title", "varchar", "NO", "Product title", False),
    ]

    # Mock cross-schema foreign keys
    # billing.subscriptions.user_id -> auth.users.id
    # billing.invoices.subscription_id -> billing.subscriptions.id
    fks_data = [
        ("billing", "subscriptions", "user_id", "auth", "users", "id"),
        ("billing", "invoices", "subscription_id", "billing", "subscriptions", "id"),
    ]

    mock_cur.fetchall.side_effect = [tables_data, columns_data, fks_data]

    tables = _extract_postgres(
        connection_url="postgresql://user:pass@localhost:5432/saas_db",
        exclude_tables=[],
        schemas=["public", "auth", "billing"]
    )

    assert len(tables) == 4
    table_names = [t["name"] for t in tables]
    assert "auth.users" in table_names
    assert "billing.subscriptions" in table_names
    assert "billing.invoices" in table_names
    assert "public.products" in table_names

    # Check cross-schema FK in billing.subscriptions
    sub_table = next(t for t in tables if t["name"] == "billing.subscriptions")
    assert len(sub_table["foreign_keys"]) == 1
    assert sub_table["foreign_keys"][0]["column_name"] == "user_id"
    assert sub_table["foreign_keys"][0]["foreign_table_name"] == "auth.users"
    assert sub_table["foreign_keys"][0]["foreign_column_name"] == "id"


@patch("psycopg.connect")
def test_postgres_single_public_schema_unqualified(mock_connect):
    """Verify single public schema preserves clean unqualified table names for backward compatibility."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur

    tables_data = [("public", "users", "User accounts")]
    columns_data = [("public", "users", "id", "integer", "NO", None, True)]
    fks_data = []

    mock_cur.fetchall.side_effect = [tables_data, columns_data, fks_data]

    tables = _extract_postgres(
        connection_url="postgresql://user:pass@localhost:5432/mydb",
        exclude_tables=[],
        schemas=["public"]
    )

    assert len(tables) == 1
    assert tables[0]["name"] == "users"  # Unqualified for single public schema
