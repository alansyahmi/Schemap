<!-- schemap:start -->
# Database Architecture & Context for Claude

This project relies on the database schema outlined below. Refer to this context when writing queries, migrations, or database-related business logic.

## Core Statistics
- **Active Tables**: 8
- **Key Hub Entities**: products, orders, users, order_items, reviews

## AI Safety & Anti-Hallucination Guardrails
- [SAFETY] Never join `products.id` directly to `categories.id`. Correct JOIN path: `products.category_id -> categories.id`.
- [SAFETY] Never join `orders.id` directly to `users.id`. Correct JOIN path: `orders.user_id -> users.id`.
- [SAFETY] Never join `order_items.id` directly to `products.id`. Correct JOIN path: `order_items.product_id -> products.id`.
- [SAFETY] Never join `order_items.id` directly to `orders.id`. Correct JOIN path: `order_items.order_id -> orders.id`.
- [SAFETY] Never join `payments.id` directly to `orders.id`. Correct JOIN path: `payments.order_id -> orders.id`.
- [SAFETY] Never join `reviews.id` directly to `products.id`. Correct JOIN path: `reviews.product_id -> products.id`.
- [SAFETY] Never join `reviews.id` directly to `users.id`. Correct JOIN path: `reviews.user_id -> users.id`.
- [SAFETY] Immutability Guardrail: Do not generate DELETE or UPDATE queries for audit/financial records: `payments`

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
<!-- schemap:end -->
