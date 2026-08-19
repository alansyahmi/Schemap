"""Canonical database schema definitions for Schemap benchmark evaluation.

Includes:
1. Chinook (11 tables - Digital Media Store)
2. Northwind (13 tables - ERP & Inventory)
3. Pagila (15 tables - Video Rental with Many-to-Many & cyclic relationships)
4. SaaS Platform (30 tables - Multi-tenant, RBAC, Subscriptions, Audit Logs)
5. Enterprise Scale (100 tables - Synthetic large enterprise schema)
"""

from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel, ForeignKeyModel
from tests.stress_generator import generate_synthetic_schema_models


def get_chinook_schema() -> tuple[DatabaseSchemaModel, str]:
    """Chinook 11-table digital media store schema and full DDL."""
    tables = [
        TableModel(
            name="artists",
            columns=[
                ColumnModel(name="artist_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="name", data_type="VARCHAR(120)", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="albums",
            columns=[
                ColumnModel(name="album_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="title", data_type="VARCHAR(160)", primary_key=False, is_nullable=False),
                ColumnModel(name="artist_id", data_type="INTEGER", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="artist_id", foreign_table_name="artists", foreign_column_name="artist_id"),
            ],
        ),
        TableModel(
            name="media_types",
            columns=[
                ColumnModel(name="media_type_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="name", data_type="VARCHAR(120)", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="genres",
            columns=[
                ColumnModel(name="genre_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="name", data_type="VARCHAR(120)", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="tracks",
            columns=[
                ColumnModel(name="track_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="name", data_type="VARCHAR(200)", primary_key=False, is_nullable=False),
                ColumnModel(name="album_id", data_type="INTEGER", primary_key=False, is_nullable=True),
                ColumnModel(name="media_type_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="genre_id", data_type="INTEGER", primary_key=False, is_nullable=True),
                ColumnModel(name="composer", data_type="VARCHAR(220)", primary_key=False, is_nullable=True),
                ColumnModel(name="milliseconds", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="bytes", data_type="INTEGER", primary_key=False, is_nullable=True),
                ColumnModel(name="unit_price", data_type="NUMERIC(10,2)", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="album_id", foreign_table_name="albums", foreign_column_name="album_id"),
                ForeignKeyModel(column_name="media_type_id", foreign_table_name="media_types", foreign_column_name="media_type_id"),
                ForeignKeyModel(column_name="genre_id", foreign_table_name="genres", foreign_column_name="genre_id"),
            ],
        ),
        TableModel(
            name="employees",
            columns=[
                ColumnModel(name="employee_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="last_name", data_type="VARCHAR(20)", primary_key=False, is_nullable=False),
                ColumnModel(name="first_name", data_type="VARCHAR(20)", primary_key=False, is_nullable=False),
                ColumnModel(name="title", data_type="VARCHAR(30)", primary_key=False, is_nullable=True),
                ColumnModel(name="reports_to", data_type="INTEGER", primary_key=False, is_nullable=True),
                ColumnModel(name="birth_date", data_type="TIMESTAMP", primary_key=False, is_nullable=True),
                ColumnModel(name="hire_date", data_type="TIMESTAMP", primary_key=False, is_nullable=True),
                ColumnModel(name="address", data_type="VARCHAR(70)", primary_key=False, is_nullable=True),
                ColumnModel(name="city", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="state", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="country", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="postal_code", data_type="VARCHAR(10)", primary_key=False, is_nullable=True),
                ColumnModel(name="phone", data_type="VARCHAR(24)", primary_key=False, is_nullable=True),
                ColumnModel(name="fax", data_type="VARCHAR(24)", primary_key=False, is_nullable=True),
                ColumnModel(name="email", data_type="VARCHAR(60)", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="reports_to", foreign_table_name="employees", foreign_column_name="employee_id"),
            ],
        ),
        TableModel(
            name="customers",
            columns=[
                ColumnModel(name="customer_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="first_name", data_type="VARCHAR(40)", primary_key=False, is_nullable=False),
                ColumnModel(name="last_name", data_type="VARCHAR(20)", primary_key=False, is_nullable=False),
                ColumnModel(name="company", data_type="VARCHAR(80)", primary_key=False, is_nullable=True),
                ColumnModel(name="address", data_type="VARCHAR(70)", primary_key=False, is_nullable=True),
                ColumnModel(name="city", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="state", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="country", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="postal_code", data_type="VARCHAR(10)", primary_key=False, is_nullable=True),
                ColumnModel(name="phone", data_type="VARCHAR(24)", primary_key=False, is_nullable=True),
                ColumnModel(name="fax", data_type="VARCHAR(24)", primary_key=False, is_nullable=True),
                ColumnModel(name="email", data_type="VARCHAR(60)", primary_key=False, is_nullable=False),
                ColumnModel(name="support_rep_id", data_type="INTEGER", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="support_rep_id", foreign_table_name="employees", foreign_column_name="employee_id"),
            ],
        ),
        TableModel(
            name="invoices",
            columns=[
                ColumnModel(name="invoice_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="customer_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="invoice_date", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
                ColumnModel(name="billing_address", data_type="VARCHAR(70)", primary_key=False, is_nullable=True),
                ColumnModel(name="billing_city", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="billing_state", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="billing_country", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="billing_postal_code", data_type="VARCHAR(10)", primary_key=False, is_nullable=True),
                ColumnModel(name="total", data_type="NUMERIC(10,2)", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="customer_id", foreign_table_name="customers", foreign_column_name="customer_id"),
            ],
        ),
        TableModel(
            name="invoice_items",
            columns=[
                ColumnModel(name="invoice_line_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="invoice_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="track_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="unit_price", data_type="NUMERIC(10,2)", primary_key=False, is_nullable=False),
                ColumnModel(name="quantity", data_type="INTEGER", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="invoice_id", foreign_table_name="invoices", foreign_column_name="invoice_id"),
                ForeignKeyModel(column_name="track_id", foreign_table_name="tracks", foreign_column_name="track_id"),
            ],
        ),
        TableModel(
            name="playlists",
            columns=[
                ColumnModel(name="playlist_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="name", data_type="VARCHAR(120)", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="playlist_track",
            columns=[
                ColumnModel(name="playlist_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="track_id", data_type="INTEGER", primary_key=True, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="playlist_id", foreign_table_name="playlists", foreign_column_name="playlist_id"),
                ForeignKeyModel(column_name="track_id", foreign_table_name="tracks", foreign_column_name="track_id"),
            ],
        ),
    ]

    raw_ddl = """
CREATE TABLE artists (
    artist_id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(120)
);

CREATE TABLE albums (
    album_id INTEGER NOT NULL PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    artist_id INTEGER NOT NULL,
    CONSTRAINT fk_albums_artist_id FOREIGN KEY (artist_id) REFERENCES artists (artist_id) ON DELETE NO ACTION ON UPDATE NO ACTION
);
CREATE INDEX ifk_album_artist_id ON albums (artist_id);

CREATE TABLE media_types (
    media_type_id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(120)
);

CREATE TABLE genres (
    genre_id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(120)
);

CREATE TABLE tracks (
    track_id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    album_id INTEGER,
    media_type_id INTEGER NOT NULL,
    genre_id INTEGER,
    composer VARCHAR(220),
    milliseconds INTEGER NOT NULL,
    bytes INTEGER,
    unit_price NUMERIC(10,2) NOT NULL,
    CONSTRAINT fk_tracks_album_id FOREIGN KEY (album_id) REFERENCES albums (album_id) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT fk_tracks_genre_id FOREIGN KEY (genre_id) REFERENCES genres (genre_id) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT fk_tracks_media_type_id FOREIGN KEY (media_type_id) REFERENCES media_types (media_type_id) ON DELETE NO ACTION ON UPDATE NO ACTION
);
CREATE INDEX ifk_track_album_id ON tracks (album_id);
CREATE INDEX ifk_track_genre_id ON tracks (genre_id);
CREATE INDEX ifk_track_media_type_id ON tracks (media_type_id);

CREATE TABLE employees (
    employee_id INTEGER NOT NULL PRIMARY KEY,
    last_name VARCHAR(20) NOT NULL,
    first_name VARCHAR(20) NOT NULL,
    title VARCHAR(30),
    reports_to INTEGER,
    birth_date TIMESTAMP,
    hire_date TIMESTAMP,
    address VARCHAR(70),
    city VARCHAR(40),
    state VARCHAR(40),
    country VARCHAR(40),
    postal_code VARCHAR(10),
    phone VARCHAR(24),
    fax VARCHAR(24),
    email VARCHAR(60),
    CONSTRAINT fk_employees_reports_to FOREIGN KEY (reports_to) REFERENCES employees (employee_id) ON DELETE NO ACTION ON UPDATE NO ACTION
);
CREATE INDEX ifk_employee_reports_to ON employees (reports_to);

CREATE TABLE customers (
    customer_id INTEGER NOT NULL PRIMARY KEY,
    first_name VARCHAR(40) NOT NULL,
    last_name VARCHAR(20) NOT NULL,
    company VARCHAR(80),
    address VARCHAR(70),
    city VARCHAR(40),
    state VARCHAR(40),
    country VARCHAR(40),
    postal_code VARCHAR(10),
    phone VARCHAR(24),
    fax VARCHAR(24),
    email VARCHAR(60) NOT NULL,
    support_rep_id INTEGER,
    CONSTRAINT fk_customers_support_rep_id FOREIGN KEY (support_rep_id) REFERENCES employees (employee_id) ON DELETE NO ACTION ON UPDATE NO ACTION
);
CREATE INDEX ifk_customer_support_rep_id ON customers (support_rep_id);

CREATE TABLE invoices (
    invoice_id INTEGER NOT NULL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    invoice_date TIMESTAMP NOT NULL,
    billing_address VARCHAR(70),
    billing_city VARCHAR(40),
    billing_state VARCHAR(40),
    billing_country VARCHAR(40),
    billing_postal_code VARCHAR(10),
    total NUMERIC(10,2) NOT NULL,
    CONSTRAINT fk_invoices_customer_id FOREIGN KEY (customer_id) REFERENCES customers (customer_id) ON DELETE NO ACTION ON UPDATE NO ACTION
);
CREATE INDEX ifk_invoice_customer_id ON invoices (customer_id);

CREATE TABLE invoice_items (
    invoice_line_id INTEGER NOT NULL PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    CONSTRAINT fk_invoice_items_invoice_id FOREIGN KEY (invoice_id) REFERENCES invoices (invoice_id) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT fk_invoice_items_track_id FOREIGN KEY (track_id) REFERENCES tracks (track_id) ON DELETE NO ACTION ON UPDATE NO ACTION
);
CREATE INDEX ifk_invoice_line_invoice_id ON invoice_items (invoice_id);
CREATE INDEX ifk_invoice_line_track_id ON invoice_items (track_id);

CREATE TABLE playlists (
    playlist_id INTEGER NOT NULL PRIMARY KEY,
    name VARCHAR(120)
);

CREATE TABLE playlist_track (
    playlist_id INTEGER NOT NULL,
    track_id INTEGER NOT NULL,
    CONSTRAINT pk_playlist_track PRIMARY KEY (playlist_id, track_id),
    CONSTRAINT fk_playlist_track_playlist_id FOREIGN KEY (playlist_id) REFERENCES playlists (playlist_id) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT fk_playlist_track_track_id FOREIGN KEY (track_id) REFERENCES tracks (track_id) ON DELETE NO ACTION ON UPDATE NO ACTION
);
CREATE INDEX ifk_playlist_track_track_id ON playlist_track (track_id);
"""
    return DatabaseSchemaModel(tables=tables), raw_ddl.strip()


def get_northwind_schema() -> tuple[DatabaseSchemaModel, str]:
    """Northwind 13-table ERP & Inventory schema and full DDL."""
    tables = [
        TableModel(
            name="categories",
            columns=[
                ColumnModel(name="category_id", data_type="SMALLINT", primary_key=True, is_nullable=False),
                ColumnModel(name="category_name", data_type="VARCHAR(15)", primary_key=False, is_nullable=False),
                ColumnModel(name="description", data_type="TEXT", primary_key=False, is_nullable=True),
                ColumnModel(name="picture", data_type="BYTEA", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="suppliers",
            columns=[
                ColumnModel(name="supplier_id", data_type="SMALLINT", primary_key=True, is_nullable=False),
                ColumnModel(name="company_name", data_type="VARCHAR(40)", primary_key=False, is_nullable=False),
                ColumnModel(name="contact_name", data_type="VARCHAR(30)", primary_key=False, is_nullable=True),
                ColumnModel(name="contact_title", data_type="VARCHAR(30)", primary_key=False, is_nullable=True),
                ColumnModel(name="address", data_type="VARCHAR(60)", primary_key=False, is_nullable=True),
                ColumnModel(name="city", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="region", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="postal_code", data_type="VARCHAR(10)", primary_key=False, is_nullable=True),
                ColumnModel(name="country", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="phone", data_type="VARCHAR(24)", primary_key=False, is_nullable=True),
                ColumnModel(name="fax", data_type="VARCHAR(24)", primary_key=False, is_nullable=True),
                ColumnModel(name="homepage", data_type="TEXT", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="products",
            columns=[
                ColumnModel(name="product_id", data_type="SMALLINT", primary_key=True, is_nullable=False),
                ColumnModel(name="product_name", data_type="VARCHAR(40)", primary_key=False, is_nullable=False),
                ColumnModel(name="supplier_id", data_type="SMALLINT", primary_key=False, is_nullable=True),
                ColumnModel(name="category_id", data_type="SMALLINT", primary_key=False, is_nullable=True),
                ColumnModel(name="quantity_per_unit", data_type="VARCHAR(20)", primary_key=False, is_nullable=True),
                ColumnModel(name="unit_price", data_type="REAL", primary_key=False, is_nullable=True),
                ColumnModel(name="units_in_stock", data_type="SMALLINT", primary_key=False, is_nullable=True),
                ColumnModel(name="units_on_order", data_type="SMALLINT", primary_key=False, is_nullable=True),
                ColumnModel(name="reorder_level", data_type="SMALLINT", primary_key=False, is_nullable=True),
                ColumnModel(name="discontinued", data_type="INTEGER", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="category_id", foreign_table_name="categories", foreign_column_name="category_id"),
                ForeignKeyModel(column_name="supplier_id", foreign_table_name="suppliers", foreign_column_name="supplier_id"),
            ],
        ),
        TableModel(
            name="region",
            columns=[
                ColumnModel(name="region_id", data_type="SMALLINT", primary_key=True, is_nullable=False),
                ColumnModel(name="region_description", data_type="VARCHAR(50)", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="territories",
            columns=[
                ColumnModel(name="territory_id", data_type="VARCHAR(20)", primary_key=True, is_nullable=False),
                ColumnModel(name="territory_description", data_type="VARCHAR(50)", primary_key=False, is_nullable=False),
                ColumnModel(name="region_id", data_type="SMALLINT", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="region_id", foreign_table_name="region", foreign_column_name="region_id"),
            ],
        ),
        TableModel(
            name="employees",
            columns=[
                ColumnModel(name="employee_id", data_type="SMALLINT", primary_key=True, is_nullable=False),
                ColumnModel(name="last_name", data_type="VARCHAR(20)", primary_key=False, is_nullable=False),
                ColumnModel(name="first_name", data_type="VARCHAR(10)", primary_key=False, is_nullable=False),
                ColumnModel(name="title", data_type="VARCHAR(30)", primary_key=False, is_nullable=True),
                ColumnModel(name="title_of_courtesy", data_type="VARCHAR(25)", primary_key=False, is_nullable=True),
                ColumnModel(name="birth_date", data_type="DATE", primary_key=False, is_nullable=True),
                ColumnModel(name="hire_date", data_type="DATE", primary_key=False, is_nullable=True),
                ColumnModel(name="address", data_type="VARCHAR(60)", primary_key=False, is_nullable=True),
                ColumnModel(name="city", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="region", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="postal_code", data_type="VARCHAR(10)", primary_key=False, is_nullable=True),
                ColumnModel(name="country", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="home_phone", data_type="VARCHAR(24)", primary_key=False, is_nullable=True),
                ColumnModel(name="extension", data_type="VARCHAR(4)", primary_key=False, is_nullable=True),
                ColumnModel(name="notes", data_type="TEXT", primary_key=False, is_nullable=True),
                ColumnModel(name="reports_to", data_type="SMALLINT", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="reports_to", foreign_table_name="employees", foreign_column_name="employee_id"),
            ],
        ),
        TableModel(
            name="employee_territories",
            columns=[
                ColumnModel(name="employee_id", data_type="SMALLINT", primary_key=True, is_nullable=False),
                ColumnModel(name="territory_id", data_type="VARCHAR(20)", primary_key=True, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="employee_id", foreign_table_name="employees", foreign_column_name="employee_id"),
                ForeignKeyModel(column_name="territory_id", foreign_table_name="territories", foreign_column_name="territory_id"),
            ],
        ),
        TableModel(
            name="shippers",
            columns=[
                ColumnModel(name="shipper_id", data_type="SMALLINT", primary_key=True, is_nullable=False),
                ColumnModel(name="company_name", data_type="VARCHAR(40)", primary_key=False, is_nullable=False),
                ColumnModel(name="phone", data_type="VARCHAR(24)", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="customers",
            columns=[
                ColumnModel(name="customer_id", data_type="VARCHAR(5)", primary_key=True, is_nullable=False),
                ColumnModel(name="company_name", data_type="VARCHAR(40)", primary_key=False, is_nullable=False),
                ColumnModel(name="contact_name", data_type="VARCHAR(30)", primary_key=False, is_nullable=True),
                ColumnModel(name="contact_title", data_type="VARCHAR(30)", primary_key=False, is_nullable=True),
                ColumnModel(name="address", data_type="VARCHAR(60)", primary_key=False, is_nullable=True),
                ColumnModel(name="city", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="region", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="postal_code", data_type="VARCHAR(10)", primary_key=False, is_nullable=True),
                ColumnModel(name="country", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="phone", data_type="VARCHAR(24)", primary_key=False, is_nullable=True),
                ColumnModel(name="fax", data_type="VARCHAR(24)", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="orders",
            columns=[
                ColumnModel(name="order_id", data_type="SMALLINT", primary_key=True, is_nullable=False),
                ColumnModel(name="customer_id", data_type="VARCHAR(5)", primary_key=False, is_nullable=True),
                ColumnModel(name="employee_id", data_type="SMALLINT", primary_key=False, is_nullable=True),
                ColumnModel(name="order_date", data_type="DATE", primary_key=False, is_nullable=True),
                ColumnModel(name="required_date", data_type="DATE", primary_key=False, is_nullable=True),
                ColumnModel(name="shipped_date", data_type="DATE", primary_key=False, is_nullable=True),
                ColumnModel(name="ship_via", data_type="SMALLINT", primary_key=False, is_nullable=True),
                ColumnModel(name="freight", data_type="REAL", primary_key=False, is_nullable=True),
                ColumnModel(name="ship_name", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="ship_address", data_type="VARCHAR(60)", primary_key=False, is_nullable=True),
                ColumnModel(name="ship_city", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="ship_region", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
                ColumnModel(name="ship_postal_code", data_type="VARCHAR(10)", primary_key=False, is_nullable=True),
                ColumnModel(name="ship_country", data_type="VARCHAR(15)", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="customer_id", foreign_table_name="customers", foreign_column_name="customer_id"),
                ForeignKeyModel(column_name="employee_id", foreign_table_name="employees", foreign_column_name="employee_id"),
                ForeignKeyModel(column_name="ship_via", foreign_table_name="shippers", foreign_column_name="shipper_id"),
            ],
        ),
        TableModel(
            name="order_details",
            columns=[
                ColumnModel(name="order_id", data_type="SMALLINT", primary_key=True, is_nullable=False),
                ColumnModel(name="product_id", data_type="SMALLINT", primary_key=True, is_nullable=False),
                ColumnModel(name="unit_price", data_type="REAL", primary_key=False, is_nullable=False),
                ColumnModel(name="quantity", data_type="SMALLINT", primary_key=False, is_nullable=False),
                ColumnModel(name="discount", data_type="REAL", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="order_id", foreign_table_name="orders", foreign_column_name="order_id"),
                ForeignKeyModel(column_name="product_id", foreign_table_name="products", foreign_column_name="product_id"),
            ],
        ),
        TableModel(
            name="customer_demographics",
            columns=[
                ColumnModel(name="customer_type_id", data_type="VARCHAR(10)", primary_key=True, is_nullable=False),
                ColumnModel(name="customer_desc", data_type="TEXT", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="customer_customer_demo",
            columns=[
                ColumnModel(name="customer_id", data_type="VARCHAR(5)", primary_key=True, is_nullable=False),
                ColumnModel(name="customer_type_id", data_type="VARCHAR(10)", primary_key=True, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="customer_id", foreign_table_name="customers", foreign_column_name="customer_id"),
                ForeignKeyModel(column_name="customer_type_id", foreign_table_name="customer_demographics", foreign_column_name="customer_type_id"),
            ],
        ),
    ]

    raw_ddl = """
CREATE TABLE categories (
    category_id SMALLINT NOT NULL PRIMARY KEY,
    category_name VARCHAR(15) NOT NULL,
    description TEXT,
    picture BYTEA
);

CREATE TABLE suppliers (
    supplier_id SMALLINT NOT NULL PRIMARY KEY,
    company_name VARCHAR(40) NOT NULL,
    contact_name VARCHAR(30),
    contact_title VARCHAR(30),
    address VARCHAR(60),
    city VARCHAR(15),
    region VARCHAR(15),
    postal_code VARCHAR(10),
    country VARCHAR(15),
    phone VARCHAR(24),
    fax VARCHAR(24),
    homepage TEXT
);

CREATE TABLE products (
    product_id SMALLINT NOT NULL PRIMARY KEY,
    product_name VARCHAR(40) NOT NULL,
    supplier_id SMALLINT,
    category_id SMALLINT,
    quantity_per_unit VARCHAR(20),
    unit_price REAL,
    units_in_stock SMALLINT,
    units_on_order SMALLINT,
    reorder_level SMALLINT,
    discontinued INTEGER NOT NULL,
    CONSTRAINT fk_products_categories FOREIGN KEY (category_id) REFERENCES categories (category_id),
    CONSTRAINT fk_products_suppliers FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id)
);
CREATE INDEX idx_products_category ON products (category_id);
CREATE INDEX idx_products_supplier ON products (supplier_id);

CREATE TABLE region (
    region_id SMALLINT NOT NULL PRIMARY KEY,
    region_description VARCHAR(50) NOT NULL
);

CREATE TABLE territories (
    territory_id VARCHAR(20) NOT NULL PRIMARY KEY,
    territory_description VARCHAR(50) NOT NULL,
    region_id SMALLINT NOT NULL,
    CONSTRAINT fk_territories_region FOREIGN KEY (region_id) REFERENCES region (region_id)
);

CREATE TABLE employees (
    employee_id SMALLINT NOT NULL PRIMARY KEY,
    last_name VARCHAR(20) NOT NULL,
    first_name VARCHAR(10) NOT NULL,
    title VARCHAR(30),
    title_of_courtesy VARCHAR(25),
    birth_date DATE,
    hire_date DATE,
    address VARCHAR(60),
    city VARCHAR(15),
    region VARCHAR(15),
    postal_code VARCHAR(10),
    country VARCHAR(15),
    home_phone VARCHAR(24),
    extension VARCHAR(4),
    notes TEXT,
    reports_to SMALLINT,
    CONSTRAINT fk_employees_employees FOREIGN KEY (reports_to) REFERENCES employees (employee_id)
);

CREATE TABLE employee_territories (
    employee_id SMALLINT NOT NULL,
    territory_id VARCHAR(20) NOT NULL,
    PRIMARY KEY (employee_id, territory_id),
    CONSTRAINT fk_employee_territories_employees FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
    CONSTRAINT fk_employee_territories_territories FOREIGN KEY (territory_id) REFERENCES territories (territory_id)
);

CREATE TABLE shippers (
    shipper_id SMALLINT NOT NULL PRIMARY KEY,
    company_name VARCHAR(40) NOT NULL,
    phone VARCHAR(24)
);

CREATE TABLE customers (
    customer_id VARCHAR(5) NOT NULL PRIMARY KEY,
    company_name VARCHAR(40) NOT NULL,
    contact_name VARCHAR(30),
    contact_title VARCHAR(30),
    address VARCHAR(60),
    city VARCHAR(15),
    region VARCHAR(15),
    postal_code VARCHAR(10),
    country VARCHAR(15),
    phone VARCHAR(24),
    fax VARCHAR(24)
);

CREATE TABLE orders (
    order_id SMALLINT NOT NULL PRIMARY KEY,
    customer_id VARCHAR(5),
    employee_id SMALLINT,
    order_date DATE,
    required_date DATE,
    shipped_date DATE,
    ship_via SMALLINT,
    freight REAL,
    ship_name VARCHAR(40),
    ship_address VARCHAR(60),
    ship_city VARCHAR(15),
    ship_region VARCHAR(15),
    ship_postal_code VARCHAR(10),
    ship_country VARCHAR(15),
    CONSTRAINT fk_orders_customers FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    CONSTRAINT fk_orders_employees FOREIGN KEY (employee_id) REFERENCES employees (employee_id),
    CONSTRAINT fk_orders_shippers FOREIGN KEY (ship_via) REFERENCES shippers (shipper_id)
);
CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_employee ON orders (employee_id);

CREATE TABLE order_details (
    order_id SMALLINT NOT NULL,
    product_id SMALLINT NOT NULL,
    unit_price REAL NOT NULL,
    quantity SMALLINT NOT NULL,
    discount REAL NOT NULL,
    PRIMARY KEY (order_id, product_id),
    CONSTRAINT fk_order_details_orders FOREIGN KEY (order_id) REFERENCES orders (order_id),
    CONSTRAINT fk_order_details_products FOREIGN KEY (product_id) REFERENCES products (product_id)
);
CREATE INDEX idx_order_details_product ON order_details (product_id);

CREATE TABLE customer_demographics (
    customer_type_id VARCHAR(10) NOT NULL PRIMARY KEY,
    customer_desc TEXT
);

CREATE TABLE customer_customer_demo (
    customer_id VARCHAR(5) NOT NULL,
    customer_type_id VARCHAR(10) NOT NULL,
    PRIMARY KEY (customer_id, customer_type_id),
    CONSTRAINT fk_customer_demo_customers FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    CONSTRAINT fk_customer_demo_types FOREIGN KEY (customer_type_id) REFERENCES customer_demographics (customer_type_id)
);
"""
    return DatabaseSchemaModel(tables=tables), raw_ddl.strip()


def get_pagila_schema() -> tuple[DatabaseSchemaModel, str]:
    """Pagila 15-table DVD Rental schema with cyclic & complex relations."""
    tables = [
        TableModel(
            name="actor",
            columns=[
                ColumnModel(name="actor_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="first_name", data_type="VARCHAR(45)", primary_key=False, is_nullable=False),
                ColumnModel(name="last_name", data_type="VARCHAR(45)", primary_key=False, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="category",
            columns=[
                ColumnModel(name="category_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="name", data_type="VARCHAR(25)", primary_key=False, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="language",
            columns=[
                ColumnModel(name="language_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="name", data_type="CHAR(20)", primary_key=False, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="film",
            columns=[
                ColumnModel(name="film_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="title", data_type="VARCHAR(255)", primary_key=False, is_nullable=False),
                ColumnModel(name="description", data_type="TEXT", primary_key=False, is_nullable=True),
                ColumnModel(name="release_year", data_type="INTEGER", primary_key=False, is_nullable=True),
                ColumnModel(name="language_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="rental_duration", data_type="SMALLINT", primary_key=False, is_nullable=False),
                ColumnModel(name="rental_rate", data_type="NUMERIC(4,2)", primary_key=False, is_nullable=False),
                ColumnModel(name="length", data_type="SMALLINT", primary_key=False, is_nullable=True),
                ColumnModel(name="replacement_cost", data_type="NUMERIC(5,2)", primary_key=False, is_nullable=False),
                ColumnModel(name="rating", data_type="VARCHAR(10)", primary_key=False, is_nullable=True),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="language_id", foreign_table_name="language", foreign_column_name="language_id"),
            ],
        ),
        TableModel(
            name="film_actor",
            columns=[
                ColumnModel(name="actor_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="film_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="actor_id", foreign_table_name="actor", foreign_column_name="actor_id"),
                ForeignKeyModel(column_name="film_id", foreign_table_name="film", foreign_column_name="film_id"),
            ],
        ),
        TableModel(
            name="film_category",
            columns=[
                ColumnModel(name="film_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="category_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="film_id", foreign_table_name="film", foreign_column_name="film_id"),
                ForeignKeyModel(column_name="category_id", foreign_table_name="category", foreign_column_name="category_id"),
            ],
        ),
        TableModel(
            name="country",
            columns=[
                ColumnModel(name="country_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="country", data_type="VARCHAR(50)", primary_key=False, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[],
        ),
        TableModel(
            name="city",
            columns=[
                ColumnModel(name="city_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="city", data_type="VARCHAR(50)", primary_key=False, is_nullable=False),
                ColumnModel(name="country_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="country_id", foreign_table_name="country", foreign_column_name="country_id"),
            ],
        ),
        TableModel(
            name="address",
            columns=[
                ColumnModel(name="address_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="address", data_type="VARCHAR(50)", primary_key=False, is_nullable=False),
                ColumnModel(name="address2", data_type="VARCHAR(50)", primary_key=False, is_nullable=True),
                ColumnModel(name="district", data_type="VARCHAR(20)", primary_key=False, is_nullable=False),
                ColumnModel(name="city_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="postal_code", data_type="VARCHAR(10)", primary_key=False, is_nullable=True),
                ColumnModel(name="phone", data_type="VARCHAR(20)", primary_key=False, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="city_id", foreign_table_name="city", foreign_column_name="city_id"),
            ],
        ),
        TableModel(
            name="store",
            columns=[
                ColumnModel(name="store_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="manager_staff_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="address_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="address_id", foreign_table_name="address", foreign_column_name="address_id"),
            ],
        ),
        TableModel(
            name="staff",
            columns=[
                ColumnModel(name="staff_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="first_name", data_type="VARCHAR(45)", primary_key=False, is_nullable=False),
                ColumnModel(name="last_name", data_type="VARCHAR(45)", primary_key=False, is_nullable=False),
                ColumnModel(name="address_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="email", data_type="VARCHAR(50)", primary_key=False, is_nullable=True),
                ColumnModel(name="store_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="active", data_type="BOOLEAN", primary_key=False, is_nullable=False),
                ColumnModel(name="username", data_type="VARCHAR(16)", primary_key=False, is_nullable=False),
                ColumnModel(name="password", data_type="VARCHAR(40)", primary_key=False, is_nullable=True),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="address_id", foreign_table_name="address", foreign_column_name="address_id"),
                ForeignKeyModel(column_name="store_id", foreign_table_name="store", foreign_column_name="store_id"),
            ],
        ),
        TableModel(
            name="customer",
            columns=[
                ColumnModel(name="customer_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="store_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="first_name", data_type="VARCHAR(45)", primary_key=False, is_nullable=False),
                ColumnModel(name="last_name", data_type="VARCHAR(45)", primary_key=False, is_nullable=False),
                ColumnModel(name="email", data_type="VARCHAR(50)", primary_key=False, is_nullable=True),
                ColumnModel(name="address_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="activebool", data_type="BOOLEAN", primary_key=False, is_nullable=False),
                ColumnModel(name="create_date", data_type="DATE", primary_key=False, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=True),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="store_id", foreign_table_name="store", foreign_column_name="store_id"),
                ForeignKeyModel(column_name="address_id", foreign_table_name="address", foreign_column_name="address_id"),
            ],
        ),
        TableModel(
            name="inventory",
            columns=[
                ColumnModel(name="inventory_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="film_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="store_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="film_id", foreign_table_name="film", foreign_column_name="film_id"),
                ForeignKeyModel(column_name="store_id", foreign_table_name="store", foreign_column_name="store_id"),
            ],
        ),
        TableModel(
            name="rental",
            columns=[
                ColumnModel(name="rental_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="rental_date", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
                ColumnModel(name="inventory_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="customer_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="return_date", data_type="TIMESTAMP", primary_key=False, is_nullable=True),
                ColumnModel(name="staff_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="last_update", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="inventory_id", foreign_table_name="inventory", foreign_column_name="inventory_id"),
                ForeignKeyModel(column_name="customer_id", foreign_table_name="customer", foreign_column_name="customer_id"),
                ForeignKeyModel(column_name="staff_id", foreign_table_name="staff", foreign_column_name="staff_id"),
            ],
        ),
        TableModel(
            name="payment",
            columns=[
                ColumnModel(name="payment_id", data_type="INTEGER", primary_key=True, is_nullable=False),
                ColumnModel(name="customer_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="staff_id", data_type="INTEGER", primary_key=False, is_nullable=False),
                ColumnModel(name="rental_id", data_type="INTEGER", primary_key=False, is_nullable=True),
                ColumnModel(name="amount", data_type="NUMERIC(5,2)", primary_key=False, is_nullable=False),
                ColumnModel(name="payment_date", data_type="TIMESTAMP", primary_key=False, is_nullable=False),
            ],
            foreign_keys=[
                ForeignKeyModel(column_name="customer_id", foreign_table_name="customer", foreign_column_name="customer_id"),
                ForeignKeyModel(column_name="staff_id", foreign_table_name="staff", foreign_column_name="staff_id"),
                ForeignKeyModel(column_name="rental_id", foreign_table_name="rental", foreign_column_name="rental_id"),
            ],
        ),
    ]

    raw_ddl = """
CREATE TABLE actor (
    actor_id SERIAL PRIMARY KEY,
    first_name VARCHAR(45) NOT NULL,
    last_name VARCHAR(45) NOT NULL,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_actor_last_name ON actor (last_name);

CREATE TABLE category (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(25) NOT NULL,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE language (
    language_id SERIAL PRIMARY KEY,
    name CHAR(20) NOT NULL,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE film (
    film_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    release_year INTEGER,
    language_id INTEGER NOT NULL REFERENCES language (language_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    rental_duration SMALLINT NOT NULL DEFAULT 3,
    rental_rate NUMERIC(4,2) NOT NULL DEFAULT 4.99,
    length SMALLINT,
    replacement_cost NUMERIC(5,2) NOT NULL DEFAULT 19.99,
    rating VARCHAR(10) DEFAULT 'G',
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_film_title ON film (title);
CREATE INDEX idx_fk_language_id ON film (language_id);

CREATE TABLE film_actor (
    actor_id INTEGER NOT NULL REFERENCES actor (actor_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    film_id INTEGER NOT NULL REFERENCES film (film_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (actor_id, film_id)
);
CREATE INDEX idx_fk_film_id ON film_actor (film_id);

CREATE TABLE film_category (
    film_id INTEGER NOT NULL REFERENCES film (film_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    category_id INTEGER NOT NULL REFERENCES category (category_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (film_id, category_id)
);

CREATE TABLE country (
    country_id SERIAL PRIMARY KEY,
    country VARCHAR(50) NOT NULL,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE city (
    city_id SERIAL PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    country_id INTEGER NOT NULL REFERENCES country (country_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_country_id ON city (country_id);

CREATE TABLE address (
    address_id SERIAL PRIMARY KEY,
    address VARCHAR(50) NOT NULL,
    address2 VARCHAR(50),
    district VARCHAR(20) NOT NULL,
    city_id INTEGER NOT NULL REFERENCES city (city_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    postal_code VARCHAR(10),
    phone VARCHAR(20) NOT NULL,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_city_id ON address (city_id);

CREATE TABLE store (
    store_id SERIAL PRIMARY KEY,
    manager_staff_id INTEGER NOT NULL,
    address_id INTEGER NOT NULL REFERENCES address (address_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE staff (
    staff_id SERIAL PRIMARY KEY,
    first_name VARCHAR(45) NOT NULL,
    last_name VARCHAR(45) NOT NULL,
    address_id INTEGER NOT NULL REFERENCES address (address_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    email VARCHAR(50),
    store_id INTEGER NOT NULL REFERENCES store (store_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    username VARCHAR(16) NOT NULL,
    password VARCHAR(40),
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer (
    customer_id SERIAL PRIMARY KEY,
    store_id INTEGER NOT NULL REFERENCES store (store_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    first_name VARCHAR(45) NOT NULL,
    last_name VARCHAR(45) NOT NULL,
    email VARCHAR(50),
    address_id INTEGER NOT NULL REFERENCES address (address_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    activebool BOOLEAN NOT NULL DEFAULT TRUE,
    create_date DATE NOT NULL DEFAULT CURRENT_DATE,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_store_id ON customer (store_id);
CREATE INDEX idx_fk_address_id ON customer (address_id);
CREATE INDEX idx_last_name ON customer (last_name);

CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    film_id INTEGER NOT NULL REFERENCES film (film_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    store_id INTEGER NOT NULL REFERENCES store (store_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_store_id_film_id ON inventory (store_id, film_id);

CREATE TABLE rental (
    rental_id SERIAL PRIMARY KEY,
    rental_date TIMESTAMP NOT NULL,
    inventory_id INTEGER NOT NULL REFERENCES inventory (inventory_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    customer_id INTEGER NOT NULL REFERENCES customer (customer_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    return_date TIMESTAMP,
    staff_id INTEGER NOT NULL REFERENCES staff (staff_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fk_inventory_id ON rental (inventory_id);
CREATE INDEX idx_fk_customer_id ON rental (customer_id);
CREATE INDEX idx_fk_staff_id ON rental (staff_id);

CREATE TABLE payment (
    payment_id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customer (customer_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    staff_id INTEGER NOT NULL REFERENCES staff (staff_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    rental_id INTEGER REFERENCES rental (rental_id) ON DELETE SET NULL ON UPDATE CASCADE,
    amount NUMERIC(5,2) NOT NULL,
    payment_date TIMESTAMP NOT NULL
);
CREATE INDEX idx_fk_customer_id_payment ON payment (customer_id);
CREATE INDEX idx_fk_staff_id_payment ON payment (staff_id);
"""
    return DatabaseSchemaModel(tables=tables), raw_ddl.strip()


def get_saas_ecommerce_schema() -> tuple[DatabaseSchemaModel, str]:
    """30-table modern SaaS e-commerce platform schema."""
    schema = generate_synthetic_schema_models(30)
    ddl_lines = []
    for t in schema.tables:
        ddl_lines.append(f"CREATE TABLE {t.name} (")
        for col in t.columns:
            pk = " PRIMARY KEY" if col.primary_key else ""
            nullable = " NOT NULL" if not col.is_nullable else ""
            ddl_lines.append(f"    {col.name} {col.data_type}{pk}{nullable},")
        for fk in t.foreign_keys:
            ddl_lines.append(f"    CONSTRAINT fk_{t.name}_{fk.column_name} FOREIGN KEY ({fk.column_name}) REFERENCES {fk.foreign_table_name} ({fk.foreign_column_name}),")
        ddl_lines.append(");")
    return schema, "\n".join(ddl_lines)


def get_enterprise_100_schema() -> tuple[DatabaseSchemaModel, str]:
    """100-table enterprise production schema."""
    schema = generate_synthetic_schema_models(100)
    ddl_lines = []
    for t in schema.tables:
        ddl_lines.append(f"CREATE TABLE {t.name} (")
        for col in t.columns:
            pk = " PRIMARY KEY" if col.primary_key else ""
            nullable = " NOT NULL" if not col.is_nullable else ""
            ddl_lines.append(f"    {col.name} {col.data_type}{pk}{nullable},")
        for fk in t.foreign_keys:
            ddl_lines.append(f"    CONSTRAINT fk_{t.name}_{fk.column_name} FOREIGN KEY ({fk.column_name}) REFERENCES {fk.foreign_table_name} ({fk.foreign_column_name}),")
        ddl_lines.append(");")
    return schema, "\n".join(ddl_lines)
