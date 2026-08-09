# Database Context Engine Output

## Database Overview

- **Total Tables**: 8
- **Total Columns**: 45
- **Total Foreign Key Relationships**: 7

## Schema Relationship Map

```
products (category_id) ──> categories (id)
orders (user_id) ──> users (id)
order_items (product_id) ──> products (id)
order_items (order_id) ──> orders (id)
payments (order_id) ──> orders (id)
reviews (product_id) ──> products (id)
reviews (user_id) ──> users (id)
```

## Central Tables

### `products`
- **Connectivity Score**: 3.0 (3 connections)
- **Description**: No description available.
- **Primary Key(s)**: id

### `orders`
- **Connectivity Score**: 3.0 (3 connections)
- **Description**: No description available.
- **Primary Key(s)**: id

### `users`
- **Connectivity Score**: 2.0 (2 connections)
- **Description**: No description available.
- **Primary Key(s)**: id

### `order_items`
- **Connectivity Score**: 2.0 (2 connections)
- **Description**: No description available.
- **Primary Key(s)**: id

### `reviews`
- **Connectivity Score**: 2.0 (2 connections)
- **Description**: No description available.
- **Primary Key(s)**: id

## Query Examples

```sql
-- Join products with categories
SELECT *
FROM products
JOIN categories ON products.category_id = categories.id;
```

```sql
-- Join orders with users
SELECT *
FROM orders
JOIN users ON orders.user_id = users.id;
```

```sql
-- Join order_items with products
SELECT *
FROM order_items
JOIN products ON order_items.product_id = products.id;
```

```sql
-- Join order_items with orders
SELECT *
FROM order_items
JOIN orders ON order_items.order_id = orders.id;
```

```sql
-- Join payments with orders
SELECT *
FROM payments
JOIN orders ON payments.order_id = orders.id;
```
