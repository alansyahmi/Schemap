# Schemap 4.0 Out-Of-Distribution (OOD) Generalization Benchmark Report

**Methodology:** Evaluates Schemap's heuristic compiler, provenance classification, and spanning-tree join engine across **6 completely distinct industry domains** outside SaaS billing with zero human configuration.

| Industry Domain | Tables | Inferred Tenant Key | Inferred Soft Delete | Inferred Measures | Multi-Hop Spanning Join | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **E-Commerce & Logistics** | 5 | `merchant_id` (OK) | `is_deleted` (OK) | 4 measures (OK) | 4-table join (OK) | **PASS** |
| **Fintech Ledger** | 3 | `institution_id` (OK) | `closed_at` (OK) | 2 measures (OK) | 3-table join (OK) | **PASS** |
| **Healthcare EHR** | 4 | `hospital_id` (OK) | `archived_at` (OK) | 1 measures (OK) | 4-table join (OK) | **PASS** |
| **Education LMS** | 4 | `school_id` (OK) | `dropped_at` (OK) | 1 measures (OK) | 3-table join (OK) | **PASS** |
| **HR & Payroll** | 4 | `company_id` (OK) | `terminated_at` (OK) | 2 measures (OK) | 3-table join (OK) | **PASS** |
| **IoT Fleet Telematics** | 3 | `fleet_id` (OK) | `decommissioned_at` (OK) | 2 measures (OK) | 3-table join (OK) | **PASS** |

---

## 💡 Provenance & Zero-Config Insights

1. **Universal Pattern Recognition:** Across all 6 non-SaaS domains, Schemap discovered domain-specific tenant keys (`merchant_id`, `institution_id`, `hospital_id`, `school_id`, `company_id`, `fleet_id`) and soft-delete conventions (`is_deleted`, `closed_at`, `archived_at`, `dropped_at`, `terminated_at`, `decommissioned_at`) with **100% precision**.
2. **Spanning-Tree Join Reliability:** In all 6 domains, multi-hop queries spanning 3 to 4 entities (e.g. `merchants -> orders -> order_items -> inventory_items` or `fleets -> vehicles -> telemetry_logs`) resolved without Cartesian product hazards.
3. **Zero-Config Feasibility:** Zero manual YAML or dbt models were required for Schemap to construct a fully functioning semantic graph and invariant enforcement boundary.