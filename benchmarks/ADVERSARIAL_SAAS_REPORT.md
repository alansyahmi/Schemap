# Schemap 4.0 Adversarial Multi-Tenant SaaS Benchmark Report

## 🎯 Executive Benchmark Summary
- **Evaluation Set:** 20 Adversarial Tasks (Chinook/Northwind replaced with live multi-tenant SaaS schema).
- **Core Verification Standard:**
  1. *Gate 1 (Syntax & Execution):* Zero syntax or runtime execution errors.
  2. *Gate 2 (Semantic Dataset Correctness):* Exact output match on seeded production data.
  3. *Gate 3 (Tenant Isolation & Safety):* Zero cross-tenant data leaks and 100% destructive query interception.

| Mode | Passed Tasks | Success Rate | Cross-Tenant Leaks | Soft-Delete Leaks | Destructive Queries Blocked |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Mode A: Raw LLM (Naïve DDL)** | 1/20 | **5.0%** | 7 leaks | 1 leaks | 0/4 (All Executed!) 🚨 |
| **Mode B: Schemap Grounded** | 15/20 | **75.0%** | 0 leaks | 0 leaks | 0/4 (Unguarded) |
| **Mode C: Grounded + AST Guardrail** | **20/20** | **100.0%** | **0 leaks** | **0 leaks** | **4/4 Blocked (100%)** 🛡️ |

---

## 🔍 Key Empirical Findings

1. **The Silent Corruption Hazard (Mode A):**
   Raw LLMs without semantic grounding failed **75%** of adversarial queries. The most dangerous failures were silent: queries executed cleanly without syntax errors, but leaked other tenants' customer lists and included soft-deleted employees and failed payments.
2. **Tenant Isolation Guarantee (Mode B & C):**
   Schemap's `ground()` primitive successfully bound multi-tenant scope to the target organization across all tasks, reducing tenant leaks from **7** down to **0**.
3. **The Necessity of AST Enforcement (Mode C):**
   Grounding alone provides semantic context, but **cannot prevent malicious or accidental mutations** (`DROP TABLE`, `DELETE`, `TRUNCATE`). Schemap's AST guardrail (`verify_sql`) achieved a **100% interception rate** on all destructive operations.
