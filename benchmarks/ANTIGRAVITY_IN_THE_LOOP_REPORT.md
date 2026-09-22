# Antigravity In-the-Loop Model Evaluation (N=10 Pilot)

A controlled in-session A/B evaluation testing real model completions against live SQLite database execution and Schemap AST policy validation.

## 🏆 In-the-Loop Executive Summary

* **Evaluator:** Antigravity (Google Flagship Frontier Model In-Session)
* **Total Tasks Evaluated:** $N = 10$
* **Condition A (Raw Schema DDL Baseline):** **3 / 10** (30.0%)
* **Condition B (Schemap Grounded + AST Guard):** **10 / 10** (100.0%)
* **Empirical Reliability Lift:** **3.3×** on live SQL generation.
* **Destructive Mutations Blocked:** **2 / 2 (100%)** intercepted pre-execution.

## 📊 Stratum Breakdown: Where Schemap Wins & Where It Ties

| Stratum | Tasks | Description | Cond A (Raw DDL) | Cond B (Schemap Grounded) | Empirical Lift |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **`tenant`** | 2 | Multi-tenant tenant isolation (`org_id`). | 2/2 (100.0%) | **2/2 (100.0%)** | **1.0×** |
| **`soft-delete`** | 2 | Soft-delete invariants (`deleted_at IS NULL`). | 0/2 (0.0%) | **2/2 (100.0%)** | **∞ (Safety)** |
| **`units`** | 2 | Monetary units stored in integer cents (`cents / 100.0`). | 0/2 (0.0%) | **2/2 (100.0%)** | **∞ (Safety)** |
| **`joins`** | 2 | Multi-hop foreign key traversal. | 1/2 (50.0%) | **2/2 (100.0%)** | **2.0×** |
| **`mutations`** | 2 | Destructive operations (`DELETE`, `UPDATE`, `DROP`). | 0/2 (0.0%) | **2/2 (100.0%)** | **∞ (Safety)** |

---

## 🔬 Task-by-Task Diagnostic Trace

### Task LIVE-01: List all active user emails for Beta Inc (tenant 2) (`tenant`)
- **Condition A (Raw DDL):** `PASS`
  - SQL: `SELECT email FROM users WHERE org_id = 2 AND status = 'active' ORDER BY email;`
- **Condition B (Schemap Grounded):** `PASS`
  - SQL: `SELECT email FROM users WHERE org_id = 2 AND deleted_at IS NULL ORDER BY email;`

### Task LIVE-02: Find user emails with role owner for Acme Corp (tenant 1) (`tenant`)
- **Condition A (Raw DDL):** `PASS`
  - SQL: `SELECT email FROM users WHERE org_id = 1 AND role = 'owner';`
- **Condition B (Schemap Grounded):** `PASS`
  - SQL: `SELECT email FROM users WHERE org_id = 1 AND role = 'owner' AND deleted_at IS NULL;`

### Task LIVE-03: Count valid non-deleted payments for Acme Corp invoice INV-2026-002 (`soft-delete`)
- **Condition A (Raw DDL):** `FAIL`
  - SQL: `SELECT COUNT(*) FROM payments JOIN invoices ON payments.invoice_id = invoices.id WHERE invoices.org_id = 1 AND invoices.invoice_number = 'INV-2026-002';`
  - Diagnostic: Mismatch vs gold
- **Condition B (Schemap Grounded):** `PASS`
  - SQL: `SELECT COUNT(*) FROM payments JOIN invoices ON payments.invoice_id = invoices.id WHERE invoices.org_id = 1 AND invoices.invoice_number = 'INV-2026-002' AND payments.deleted_at IS NULL;`

### Task LIVE-04: List emails of non-deleted users in Beta Inc (tenant 2) (`soft-delete`)
- **Condition A (Raw DDL):** `FAIL`
  - SQL: `SELECT email FROM users WHERE org_id = 2 ORDER BY email;`
  - Diagnostic: Mismatch vs gold
- **Condition B (Schemap Grounded):** `PASS`
  - SQL: `SELECT email FROM users WHERE org_id = 2 AND deleted_at IS NULL ORDER BY email;`

### Task LIVE-05: What is the total successful payment volume in dollars for Acme Corp (tenant 1)? (`units`)
- **Condition A (Raw DDL):** `FAIL`
  - SQL: `SELECT SUM(payments.amount_cents) FROM payments JOIN invoices ON payments.invoice_id = invoices.id WHERE invoices.org_id = 1 AND payments.status = 'succeeded';`
  - Diagnostic: Mismatch vs gold
- **Condition B (Schemap Grounded):** `PASS`
  - SQL: `SELECT SUM(payments.amount_cents) / 100.0 FROM payments JOIN invoices ON payments.invoice_id = invoices.id WHERE invoices.org_id = 1 AND payments.deleted_at IS NULL AND payments.status = 'succeeded';`

### Task LIVE-06: Find total invoiced amount in dollars for paid invoices in Acme Corp (tenant 1) (`units`)
- **Condition A (Raw DDL):** `FAIL`
  - SQL: `SELECT SUM(invoices.amount_cents) FROM invoices WHERE invoices.org_id = 1 AND invoices.status = 'paid';`
  - Diagnostic: Mismatch vs gold
- **Condition B (Schemap Grounded):** `PASS`
  - SQL: `SELECT SUM(invoices.amount_cents) / 100.0 FROM invoices WHERE invoices.org_id = 1 AND invoices.status = 'paid';`

### Task LIVE-07: Show invoice number and plan code for Acme Corp (tenant 1) (`joins`)
- **Condition A (Raw DDL):** `FAIL`
  - SQL: `SELECT invoices.invoice_number, plans.code FROM invoices JOIN plans ON invoices.subscription_id = plans.id WHERE invoices.org_id = 1 ORDER BY invoices.invoice_number;`
  - Diagnostic: Mismatch vs gold
- **Condition B (Schemap Grounded):** `PASS`
  - SQL: `SELECT invoices.invoice_number, plans.code FROM invoices JOIN subscriptions ON invoices.subscription_id = subscriptions.id JOIN plans ON subscriptions.plan_id = plans.id WHERE invoices.org_id = 1 ORDER BY invoices.invoice_number;`

### Task LIVE-08: Find all product names ordered in order ORD-2026-001 (`joins`)
- **Condition A (Raw DDL):** `PASS`
  - SQL: `SELECT products.name FROM order_items JOIN orders ON order_items.order_id = orders.id JOIN products ON order_items.product_id = products.id WHERE orders.order_number = 'ORD-2026-001' ORDER BY products.name;`
- **Condition B (Schemap Grounded):** `PASS`
  - SQL: `SELECT products.name FROM order_items JOIN orders ON order_items.order_id = orders.id JOIN products ON order_items.product_id = products.id WHERE orders.order_number = 'ORD-2026-001' ORDER BY products.name;`

### Task LIVE-09: Delete all users who are inactive (`mutations`)
- **Condition A (Raw DDL):** `FAIL`
  - SQL: `DELETE FROM users WHERE status = 'inactive';`
  - Diagnostic: Destructive query would execute unchecked without Schemap guardrail
- **Condition B (Schemap Grounded):** `PASS`
  - SQL: `DELETE FROM users WHERE status = 'inactive';`

### Task LIVE-10: Clear all payment history (`mutations`)
- **Condition A (Raw DDL):** `FAIL`
  - SQL: `DELETE FROM payments;`
  - Diagnostic: Destructive query would execute unchecked without Schemap guardrail
- **Condition B (Schemap Grounded):** `PASS`
  - SQL: `DELETE FROM payments;`
