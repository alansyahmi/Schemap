# Schemap 4.0 Generalization Report: Cross-Domain Convention Discovery

This document details the out-of-distribution (OOD) evaluation of Schemap 4.0's semantic compiler, join graph resolver, and provenance classification across **6 non-SaaS industry domains** with zero human configuration.

---

## 1. What This Evaluation Tests (and What It Does Not)

### What Is Proven:
- **Heuristic Convention Discovery:** Schemap's compiler reliably identifies standard relational database design patterns:
  - Multi-tenant partitioning columns (`merchant_id`, `institution_id`, `hospital_id`, `school_id`, `company_id`, `fleet_id`).
  - Soft-delete and entity lifecycle flags (`is_deleted`, `closed_at`, `archived_at`, `dropped_at`, `terminated_at`, `decommissioned_at`).
  - Additive and monetary measures (`price_cents`, `cost_cents`, `balance_cents`, `salary_cents`, `telemetry metrics`).
  - Deterministic foreign-key spanning trees for multi-hop joins across 3–4 tables without Cartesian hazards.

### What Is NOT Claimed:
- **Zero Arbitrary Business Semantic Reasoning:** Schemap does **not** claim to deduce arbitrary, bespoke business logic (e.g. specific clinical billing guidelines, proprietary payroll tax calculations) purely from schema metadata.
- **Heuristics are Not Guarantees:** Convention recognition is a baseline discovery layer. Real production environments require human-declared guardrails for non-standard schemas.

---

## 2. The Three-Tier Provenance Architecture

To avoid hallucinating semantics, Schemap explicitly categorizes all schema insights into a three-tier provenance model:

```text
┌─────────────────────────────────────────────────────────────┐
│                    Schema Metadata                          │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       Explicit Metadata               Naming Conventions
       (Foreign Keys, PKs)             (Patterns, Affixes)
               │                               │
               ▼                               ▼
     ┌──────────────────┐            ┌──────────────────┐
     │     DECLARED     │            │     INFERRED     │
     │ Hard constraints │            │ Convention-based │
     └──────────────────┘            └──────────────────┘
               ▲
               │ (When ambiguous, e.g. dual FKs)
     ┌──────────────────┐
     │     UNKNOWN      │
     │ Flagged to Agent │
     └──────────────────┘
```

1. **`DECLARED`**: Explicit constraints defined in DDL or configuration (e.g., explicit foreign keys, human-specified tenant keys). Highest confidence.
2. **`INFERRED`**: Recovered via robust structural and naming conventions (e.g., columns ending in `_id` matching external entities, timestamp columns indicating soft deletion, integer columns ending in `_cents`).
3. **`UNKNOWN` / Ambiguous**: Situations where multiple valid interpretations exist (e.g., a ledger transaction table containing both `source_account_id` and `dest_account_id` referencing `accounts`). Schemap surfaces these as ambiguities to the calling agent rather than silently guessing a join path.

---

## 3. Cross-Domain Benchmark Results

The benchmark executes `benchmarks/multi_domain_ood_benchmark.py` across 6 distinct domains with **zero manual configuration**:

| Industry Domain | Tables | Inferred Tenant Key | Inferred Soft Delete / Lifecycle | Inferred Measures | Multi-Hop Spanning Join | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **E-Commerce & Warehouse** | 5 | `merchant_id` | `is_deleted` | 4 measures (`price_cents`, `cost_cents`, `stock_quantity`, `quantity`) | 4-table join (`merchants` → `warehouses` → `inventory_items` → `order_items`) | **PASS** |
| **Fintech Ledger** | 3 | `institution_id` | `closed_at` | 2 measures (`balance_cents`, `amount_cents`) | 3-table join + **Dual-FK ambiguity flagged** | **PASS** |
| **Healthcare Clinical (EHR)** | 4 | `hospital_id` | `archived_at` | 1 measure (`copay_cents`) | 4-table join (`hospitals` → `patients` → `encounters` → `billing_codes`) | **PASS** |
| **Education LMS** | 4 | `school_id` | `dropped_at` | 1 measure (`grade_points`) | 3-table join (`schools` → `courses` → `enrollments`) | **PASS** |
| **HR & Payroll** | 4 | `company_id` | `terminated_at` | 2 measures (`salary_cents`, `bonus_cents`) | 3-table join (`companies` → `departments` → `employees`) | **PASS** |
| **IoT Fleet Telematics** | 3 | `fleet_id` | `decommissioned_at` | 2 measures (`mileage_meters`, `fuel_liters`) | 3-table join (`fleets` → `vehicles` → `telemetry_logs`) | **PASS** |

---

## 4. Key Observations

### 1. Multi-Hop Join Tree Determinism
In standard relational operations, asking an LLM to join across 4 tables without explicit foreign key context often results in disconnected `FROM a, b, c, d` Cartesian products. In all 6 OOD domains, Schemap's breadth-first search join resolver constructed exact, hazard-free join paths directly from schema relationships:
```sql
-- E-Commerce 4-table traversal generated without Cartesian hazard:
FROM merchants
JOIN warehouses ON warehouses.merchant_id = merchants.id
JOIN inventory_items ON inventory_items.warehouse_id = warehouses.id
JOIN order_items ON order_items.inventory_item_id = inventory_items.id
```

### 2. Dual-Relationship Ambiguity Handling
In the Fintech Ledger domain, the `transactions` table contains two foreign keys pointing to `accounts`: `source_account_id` and `dest_account_id`.
Rather than arbitrarily picking one or generating a double join, Schemap identifies the ambiguity and tags it in the `GroundedPlan.ambiguities` output, ensuring the calling agent or human operator can disambiguate intent before query execution.

---

## 5. How to Reproduce

Run the standalone OOD verification suite:

```bash
uv run python benchmarks/multi_domain_ood_benchmark.py
```
