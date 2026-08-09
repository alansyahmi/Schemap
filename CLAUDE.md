# Database Architecture & Context for Claude

This project relies on the database schema outlined below. Refer to this context when writing queries, migrations, or database-related business logic.

## Core Statistics
- **Active Tables**: 8
- **Key Hub Entities**: products, orders, users, order_items, reviews

## Central Tables Overview
- **`products`**: No description
  Columns: `id` (INTEGER), `category_id` (INTEGER), `sku` (TEXT), `name` (TEXT), `description` (TEXT), `price_cents` (INTEGER) ...+2 more
- **`orders`**: No description
  Columns: `id` (INTEGER), `user_id` (INTEGER), `order_number` (TEXT), `status` (TEXT), `total_cents` (INTEGER), `shipping_address` (TEXT) ...+1 more
- **`users`**: No description
  Columns: `id` (INTEGER), `email` (TEXT), `full_name` (TEXT), `role` (TEXT), `created_at` (DATETIME)
- **`order_items`**: No description
  Columns: `id` (INTEGER), `order_id` (INTEGER), `product_id` (INTEGER), `quantity` (INTEGER), `unit_price_cents` (INTEGER)
- **`reviews`**: No description
  Columns: `id` (INTEGER), `user_id` (INTEGER), `product_id` (INTEGER), `rating` (INTEGER), `review_text` (TEXT), `created_at` (DATETIME)

## Schema Relationships
```
products (category_id) ──> categories (id)
orders (user_id) ──> users (id)
order_items (product_id) ──> products (id)
order_items (order_id) ──> orders (id)
payments (order_id) ──> orders (id)
reviews (product_id) ──> products (id)
reviews (user_id) ──> users (id)
```

## Query Guidelines
- Always verify foreign key constraints before building multi-table joins.
- Use standard indexed columns (`id`, `*_id`) for joins.
