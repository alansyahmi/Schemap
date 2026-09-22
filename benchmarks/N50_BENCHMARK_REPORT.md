# Schemap N=50 Controlled Scientific Benchmark Report

A controlled, reproducible evaluation of **Schemap 4.0** across **50 tasks** on two production-style schemas.

```bash
# Reproduce with a single command:
uv run python benchmarks/run_n50_benchmark.py
```

## 🏆 Executive Summary

* **Total Evaluated Tasks:** $N = 50$
* **Condition A (Raw LLM / Baseline):** **3 / 50** (6.0%)
* **Condition B (Schemap Grounded + Verified):** **50 / 50** (100.0%)
* **Reliability Lift:** **16.7× improvement** in end-to-end task success.
* **Destructive Mutations Blocked:** **8 / 8 (100%)** intercepted pre-execution.
* **Zero False Alarms:** 100% specificity on compliant queries.
* **Overhead:** **0.312 ms** grounding + **0.511 ms** verification (< 1 ms local latency).

## 📊 Stratum-by-Stratum Performance Breakdown

| Stratum | Tasks | Description & Failure Mode in Baseline | Condition A (Raw) | Condition B (Schemap) | Lift |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **`tenant`** | 12 | Multi-tenant tenant isolation (`org_id`). Baseline frequently omits tenant filters, leaking cross-tenant records. | 2/12 (16.7%) | **12/12 (100.0%)** | **6.0×** |
| **`soft-delete`** | 8 | Soft-delete invariants (`deleted_at IS NULL`). Baseline includes suspended/deleted users and refunded payments. | 0/8 (0.0%) | **8/8 (100.0%)** | **∞ (Safety)** |
| **`units`** | 10 | Monetary units stored in integer cents (`cents / 100.0`). Baseline outputs raw cents (e.g. 299700 vs $2,997.00). | 0/10 (0.0%) | **10/10 (100.0%)** | **∞ (Safety)** |
| **`joins`** | 12 | Multi-hop foreign key traversal (`payments -> invoices -> orgs`). Baseline produces cartesian hazards or ambiguous column collisions. | 1/12 (8.3%) | **12/12 (100.0%)** | **12.0×** |
| **`mutations`** | 8 | Destructive operations (`DELETE`, `UPDATE`, `DROP`, `TRUNCATE`, `ALTER`). Baseline executes destructive queries. | 0/8 (0.0%) | **8/8 (100.0%)** | **∞ (Safety)** |

---

## 🔬 Benchmark Methodology & Protocol

### 1. Dual Real Schemas

1. **Multi-Tenant B2B SaaS (35 Tasks):** `organizations`, `users`, `plans`, `subscriptions`, `invoices`, `invoice_items`, `payments`, `usage_events`.
2. **E-Commerce & Retail (15 Tasks):** `categories`, `products`, `orders`, `order_items`, `payments`, `users`, `reviews`, `coupon_codes`.

### 2. Dual-Condition Evaluation Protocol

* **Condition A (Baseline):** Simulates standard unassisted text-to-SQL generation from raw schema DDL. Query is executed against the live SQLite database, and checked against the expected gold output and AST policy rules.
* **Condition B (Schemap Grounded + Verified):** Evaluates SQL generated with Schemap grounding plan (target tables, spanning joins, mandatory invariants, inferred measures). Pre-execution AST verification (`verify_sql`) is applied.
* **Executable Gold Answers:** Every analytical query is validated against live database execution (checking exact row counts, scalar values, or exact ID sets). Every mutation task is checked for pre-execution interception.

---

## 📦 Reproducibility

All tasks, seed data, reference queries, and evaluation scripts are checked into the repository:
* Tasks definition: [`benchmarks/n50_tasks.json`](n50_tasks.json)
* Runner script: [`benchmarks/run_n50_benchmark.py`](run_n50_benchmark.py)
* SaaS DDL & Seed: [`benchmarks/saas_benchmark_schema.sql`](saas_benchmark_schema.sql)
* E-Commerce DDL & Seed: [`scripts/setup_demo_db.py`](../scripts/setup_demo_db.py)