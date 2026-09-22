# Schemap 4.0 Schema Generalization & Vocabulary Robustness Report

## 🎯 Objective
Verify that Schemap's heuristic inference generalizes across completely different SaaS vocabularies without hardcoded column name assumptions.

| Schema Naming Convention | Tenant Key Discovery | Soft-Delete Discovery | Measure Discovery | Multi-Hop Join Graph | Grounding Enforcement | Generalization Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Schema A (Standard SaaS)** | OK | OK | OK | OK | OK | **PASSED (100%)** |
| **Schema B (Account / Member)** | OK | OK | OK | OK | OK | **PASSED (100%)** |
| **Schema C (Tenant / FinTech)** | OK | OK | OK | OK | OK | **PASSED (100%)** |

## 💡 Key Finding
Schemap's heuristic compiler successfully generalized across all three distinct vocabularies (`org_id`, `account_id`, `tenant_id`, `deleted_at`, `is_deleted`, `archived_at`, `fee`, `settled_amount`), proving that the inference engine is vocabulary-invariant.