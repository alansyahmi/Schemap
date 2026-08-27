<!-- schemap:start -->
# AGENTS.md - Database Context

This file provides automated database context for AI agents working in this repository.

## Database Summary
- Total Tables: 8
- Key Central Tables: products, orders, users, order_items, reviews

## AI Safety & Anti-Hallucination Guardrails
- [SAFETY] Never join `products.id` directly to `categories.id`. Correct JOIN path: `products.category_id -> categories.id`.
- [SAFETY] Never join `orders.id` directly to `users.id`. Correct JOIN path: `orders.user_id -> users.id`.
- [SAFETY] Never join `order_items.id` directly to `products.id`. Correct JOIN path: `order_items.product_id -> products.id`.
- [SAFETY] Never join `order_items.id` directly to `orders.id`. Correct JOIN path: `order_items.order_id -> orders.id`.
- [SAFETY] Never join `payments.id` directly to `orders.id`. Correct JOIN path: `payments.order_id -> orders.id`.
- [SAFETY] Never join `reviews.id` directly to `products.id`. Correct JOIN path: `reviews.product_id -> products.id`.
- [SAFETY] Never join `reviews.id` directly to `users.id`. Correct JOIN path: `reviews.user_id -> users.id`.
- [SAFETY] Immutability Guardrail: Do not generate DELETE or UPDATE queries for audit/financial records: `payments`

## Table Map
### Table: `users`
Columns: id, email, full_name, role, created_at

### Table: `categories`
Columns: id, name, slug, description

### Table: `products`
Columns: id, category_id, sku, name, description, price_cents, stock_quantity, created_at
Foreign Keys: category_id -> categories.id

### Table: `orders`
Columns: id, user_id, order_number, status, total_cents, shipping_address, created_at
Foreign Keys: user_id -> users.id

### Table: `order_items`
Columns: id, order_id, product_id, quantity, unit_price_cents
Foreign Keys: product_id -> products.id, order_id -> orders.id

### Table: `payments`
Columns: id, order_id, stripe_charge_id, amount_cents, status, created_at
Foreign Keys: order_id -> orders.id

### Table: `reviews`
Columns: id, user_id, product_id, rating, review_text, created_at
Foreign Keys: product_id -> products.id, user_id -> users.id

### Table: `coupon_codes`
Columns: id, code, discount_percent, is_active
<!-- schemap:end -->
