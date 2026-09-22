# Schemap N=50 Policy & Gold-SQL Regression Suite Report

A deterministic regression suite evaluating **Schemap 4.0 policy guardrails and gold SQL execution** across **50 tasks** on two production-style schemas.

> **Important Methodology Note:** This suite tests deterministic database fixtures, invariant rules, and AST circuit-breaking. It does **not** invoke an LLM. Condition A consists of curated naive queries that omit tenant/soft-delete/units. Condition B consists of curated policy-complete queries validated by `verify_sql`. For live LLM evaluation, see our Antigravity Gemini A/B benchmark.

```bash
# Reproduce with a single command:
uv run python benchmarks/run_n50_benchmark.py
```

## 🏆 Suite Summary

* **Total Evaluated Tasks:** $N = 50$
* **Condition A (Curated Naive Queries):** **3 / 50** (6.0%)
* **Condition B (Curated Policy-Complete + Guarded):** **50 / 50** (100.0%)
* **Destructive Mutations Blocked:** **8 / 8 (100%)** intercepted pre-execution.
* **Zero False Alarms:** 100% specificity on safe, compliant queries.
* **Local Overhead:** **0.34 ms** grounding + **0.548 ms** verification (< 1 ms local latency).

## 📊 Stratum-by-Stratum Performance Breakdown

| Stratum | Tasks | Description & Tested Invariant | Cond A (Naive SQL) | Cond B (Policy-Complete) | Gold Verification |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **`tenant`** | 12 | Multi-tenant tenant isolation (`org_id`). Baseline frequently omits tenant filters, leaking cross-tenant records. | 2/12 (16.7%) | **12/12 (100.0%)** | Validated |
| **`soft-delete`** | 8 | Soft-delete invariants (`deleted_at IS NULL`). Baseline includes suspended/deleted users and refunded payments. | 0/8 (0.0%) | **8/8 (100.0%)** | Validated |
| **`units`** | 10 | Monetary units stored in integer cents (`cents / 100.0`). Baseline outputs raw cents (e.g. 299700 vs $2,997.00). | 0/10 (0.0%) | **10/10 (100.0%)** | Validated |
| **`joins`** | 12 | Multi-hop foreign key traversal (`payments -> invoices -> orgs`). Baseline produces cartesian hazards or ambiguous column collisions. | 1/12 (8.3%) | **12/12 (100.0%)** | Validated |
| **`mutations`** | 8 | Destructive operations (`DELETE`, `UPDATE`, `DROP`, `TRUNCATE`, `ALTER`). Baseline executes destructive queries. | 0/8 (0.0%) | **8/8 (100.0%)** | Validated |

---

## 🔬 Benchmark Methodology & Protocol

### 1. Dual Real Schemas

1. **Multi-Tenant B2B SaaS (35 Tasks):** `organizations`, `users`, `plans`, `subscriptions`, `invoices`, `invoice_items`, `payments`, `usage_events`.
2. **E-Commerce & Retail (15 Tasks):** `categories`, `products`, `orders`, `order_items`, `payments`, `users`, `reviews`, `coupon_codes`.

### 2. Regression Protocol

* **Condition A (Naive SQL):** Uses curated baseline queries illustrating common failure patterns (omitted tenant filters, ignored soft deletes, unscaled cents).
* **Condition B (Policy-Complete):** Uses curated reference queries conforming to Schemap invariants and validated through `verify_sql`.
* **Executable Gold Answers:** Every analytical query is validated against live database execution (checking exact row counts, scalar values, or exact ID sets). Every mutation task is checked for pre-execution interception.

---

## 📦 Reproducibility

All tasks, seed data, reference queries, and evaluation scripts are checked into the repository:
* Tasks definition: [`benchmarks/n50_tasks.json`](n50_tasks.json)
* Runner script: [`benchmarks/run_n50_benchmark.py`](run_n50_benchmark.py)
* SaaS DDL & Seed: [`benchmarks/saas_benchmark_schema.sql`](saas_benchmark_schema.sql)
* E-Commerce DDL & Seed: [`scripts/setup_demo_db.py`](../scripts/setup_demo_db.py)