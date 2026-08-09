# AGENTS.md — Database Context

This file provides automated database context for AI agents working in this repository.

## Database Summary
- Total Tables: 8
- Key Central Tables: products, orders, users, order_items, reviews

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
