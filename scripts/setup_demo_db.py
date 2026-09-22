import sqlite3
import os

from pathlib import Path

# Target examples/demo_ecommerce.db relative to repository root
repo_root = Path(__file__).parent.parent
examples_dir = repo_root / "examples"
examples_dir.mkdir(exist_ok=True)
db_path = examples_dir / "demo_ecommerce.db"

if db_path.exists():
    os.remove(db_path)

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

schema_sql = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT DEFAULT 'customer',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    order_number TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'pending',
    total_cents INTEGER NOT NULL,
    shipping_address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price_cents INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    stripe_charge_id TEXT UNIQUE,
    amount_cents INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    review_text TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE coupon_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    discount_percent INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1
);
"""

cur.executescript(schema_sql)

seed_sql = """
INSERT INTO categories (id, name, slug, description) VALUES
(1, 'Electronics', 'electronics', 'Gadgets, audio, and computer peripherals'),
(2, 'Apparel', 'apparel', 'Clothing, footwear, and accessories'),
(3, 'Books', 'books', 'Technical books and literature'),
(4, 'Kitchen', 'kitchen', 'Cookware and coffee accessories');

INSERT INTO products (id, category_id, sku, name, description, price_cents, stock_quantity) VALUES
(1, 1, 'ELEC-001', 'Wireless Noise-Canceling Headphones', 'Premium over-ear ANC headphones', 19999, 45),
(2, 1, 'ELEC-002', 'Mechanical Keyboard RGB', 'Hot-swappable mechanical keyboard', 8999, 120),
(3, 2, 'APP-001', 'Merino Wool Hoodie', '100% natural thermal wool hoodie', 7500, 80),
(4, 2, 'APP-002', 'Running Sneakers', 'Lightweight marathon running shoes', 12000, 60),
(5, 3, 'BOOK-001', 'Designing Data-Intensive Applications', 'O Reilly distributed systems reference', 4500, 200),
(6, 3, 'BOOK-002', 'Clean Code', 'Software craftsmanship handbook', 3500, 150),
(7, 4, 'KITCH-001', 'Cast Iron Skillet 12-inch', 'Pre-seasoned heavy cast iron skillet', 3999, 90),
(8, 4, 'KITCH-002', 'Pour-Over Coffee Maker', 'Borosilicate glass drip coffee dripper', 2999, 110);

INSERT INTO users (id, email, full_name, role) VALUES
(1, 'alice@example.com', 'Alice Johnson', 'customer'),
(2, 'bob@example.com', 'Bob Martinez', 'customer'),
(3, 'carol@example.com', 'Carol White', 'customer'),
(4, 'dan@example.com', 'Dan Brown', 'customer'),
(5, 'admin@example.com', 'Eve Admin', 'admin');

INSERT INTO orders (id, user_id, order_number, status, total_cents, shipping_address) VALUES
(1, 1, 'ORD-2026-001', 'completed', 28998, '123 Main St, New York, NY'),
(2, 2, 'ORD-2026-002', 'completed', 7500, '456 Oak Ave, Austin, TX'),
(3, 1, 'ORD-2026-003', 'completed', 4500, '123 Main St, New York, NY'),
(4, 3, 'ORD-2026-004', 'pending', 12000, '789 Pine Rd, Seattle, WA'),
(5, 4, 'ORD-2026-005', 'cancelled', 3999, '321 Elm St, Chicago, IL');

INSERT INTO order_items (id, order_id, product_id, quantity, unit_price_cents) VALUES
(1, 1, 1, 1, 19999),
(2, 1, 2, 1, 8999),
(3, 2, 3, 1, 7500),
(4, 3, 5, 1, 4500),
(5, 4, 4, 1, 12000),
(6, 5, 7, 1, 3999);

INSERT INTO payments (id, order_id, stripe_charge_id, amount_cents, status) VALUES
(1, 1, 'ch_ord_001', 28998, 'succeeded'),
(2, 2, 'ch_ord_002', 7500, 'succeeded'),
(3, 3, 'ch_ord_003', 4500, 'succeeded'),
(4, 4, 'ch_ord_004', 12000, 'pending'),
(5, 5, 'ch_ord_005', 3999, 'failed');

INSERT INTO reviews (id, user_id, product_id, rating, review_text) VALUES
(1, 1, 1, 5, 'Best headphones I have ever owned!'),
(2, 2, 3, 4, 'Very comfortable and warm.'),
(3, 1, 5, 5, 'Essential reading for any backend engineer.');

INSERT INTO coupon_codes (id, code, discount_percent, is_active) VALUES
(1, 'WELCOME10', 10, 1),
(2, 'SUMMER20', 20, 1),
(3, 'BLACKFRIDAY50', 50, 0);
"""
cur.executescript(seed_sql)
conn.commit()
conn.close()
print(f"Database {db_path} created successfully with 8 tables and realistic seed data.")


