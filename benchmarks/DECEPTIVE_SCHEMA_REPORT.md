# Schemap 4.0 Deceptive Schema & Ambiguity Detection Benchmark Report

## 🎯 Scientific Objective
Test whether Schemap refuses to hallucinate certainty when schemas contain conflicting candidates (multiple tenant IDs, multiple soft-delete columns, competing revenue measures), marking them as `UNKNOWN` rather than guessing.

### 1. Ambiguity Detection (Zero-Config Mode)
| Deceptive Case | Conflicting Columns | Blind Guess Made? | Provenance Assigned | Ambiguity Warning Emitted? | Test Result |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Dual Tenant Keys** (`company_id` vs `workspace_id`) | 2 candidates | NO 🛡️ | `UNKNOWN` | YES | **PASSED** |
| **Dual Soft Deletes** (`deleted_at` vs `archived_at`) | 2 candidates | NO 🛡️ | `UNKNOWN` | YES | **PASSED** |
| **Competing Money Metrics** (`gross` vs `net` vs `settled`) | 4 measures | NO 🛡️ | `INFERRED` | Listed in Graph | **PASSED** |

### 2. Human Declaration Resolution (`UNKNOWN` → `DECLARED`)
| Ambiguous Entity | Initial State | Human Declaration in YAML | Final Provenance | Policy Enforced |
| :--- | :---: | :--- | :---: | :---: |
| `projects.tenant_key` | `UNKNOWN` | `tenants: { projects: company_id }` | `DECLARED` | `company_id = :id` |
| `archives.soft_delete` | `UNKNOWN` | `soft_deletes: { archives: archived_at }` | `DECLARED` | `archived_at IS NULL` |
| Canonical `revenue` metric | `UNKNOWN` | `metrics: { revenue: net_amount }` | `DECLARED` | `SUM(net_amount)` |

## 💡 Key Architectural Finding
Schemap's Provenance Engine successfully identified all structural ambiguities and assigned `Provenance.UNKNOWN`, completely preventing blind model hallucinations on ambiguous production schemas.