# ⚠️ Schemap Tier 1 Benchmark: Database Reasoning Outcome

> **STATUS: BENCHMARK NOT RUN — requires an API key and live LLM execution.**  
> **Reason:** `Pre-flight API check failed: Anthropic HTTP 402: {"error":{"message":"Insufficient Balance","type":"unknown_error","param":null,"code":"invalid_request_error"}}`  
> *No live LLM API calls were executed. To prevent misleading or synthetic metrics, Schemap does not fabricate, simulate, or substitute synthetic results.*

---

## ⚡ Hero Question

> **Does Schemap make AI coding agents faster, cheaper, and less error-prone when working with real databases?**

---

## 🔬 Empirical Benchmark Architecture & Methodology

The benchmark framework is fully built and launch-ready for live execution under a controlled experimental protocol:

### 1. Controlled Experimental Protocol: Same Model · Same Database · Same Task
Every evaluation tests the identical task against the identical database under three experimental conditions:
- **Mode A: Blind (Zero Context)** — User question only, zero schema provided (establishes baseline hallucination rate).
- **Mode B: Raw DDL (`pg_dump`)** — Full CREATE TABLE statements and constraints (traditional developer approach).
- **Mode C: Schemap Compiled Context** — Deterministic relationship graph, explicit join paths, and AI readiness rules.

### 2. Dual-Gate Scientific Verification Standard
Generated SQL queries are evaluated against two strict, automated gates:
1. **Gate 1 (Syntax & Execution):** The query must execute cleanly in SQLite without syntax errors, missing tables, or unknown columns.
2. **Gate 2 (Semantic Dataset Result Match):** The query's executed output rows are compared against ground-truth outputs on seeded relational databases (Chinook, Northwind, Pagila). Queries that execute but produce incorrect rows fail immediately.

### 3. Metric Separation
- **Observed Metrics:** Actual prompt tokens, completion tokens, execution latency (ms), syntax validity, and semantic dataset match.
- **Calculated Metrics:** Projected inference cost at standard model pricing ($2.00 / 1M tokens).
- **Strict No-Fallback Policy:** No simulated ground truth substitution. If an API key is absent or fails, the benchmark halts cleanly with `BENCHMARK NOT RUN`.

---

## 🎯 Benchmark Matrix: 10 Realistic Developer Tasks

Planned total evaluations: **150 trials** (10 tasks × 5 runs × 3 context modes across 4 difficulty tiers).

| Task ID | Difficulty | Target Database | Real-World Engineering Objective |
| :--- | :---: | :---: | :--- |
| `task-01-easy` | **Easy** | Chinook | Track names and album titles for artist 'AC/DC' (2-table join) |
| `task-02-easy` | **Easy** | Northwind | Product inventory & reorder requirements by category (aggregate join) |
| `task-03-medium` | **Medium** | Chinook | Top 5 spending customers with assigned support sales rep (multi-table join) |
| `task-04-medium` | **Medium** | Northwind | Employee order fulfillment audit with freight shipper information (multi-join) |
| `task-05-medium` | **Medium** | Pagila | Store manager total rental revenue collections (3-table join) |
| `task-06-hard` | **Hard** | Pagila | Top 5 actors by appearances in 'Action' category films (many-to-many join) |
| `task-07-hard` | **Hard** | Chinook | Total revenue breakdown per music genre with customer invoicing (5-table join) |
| `task-08-hard` | **Hard** | Northwind | Top 3 revenue-generating products factoring line item discounts (complex math) |
| `task-09-vhard` | **Very Hard** | Pagila | Count distinct active rental customers per city (6-table join hierarchy) |
| `task-10-vhard` | **Very Hard** | Chinook | Cross-domain customer invoice line-item analysis with media types (deep schema) |

---

## 🚀 How to Execute the Live Benchmark

When API credits are configured, run:

```bash
# 1. Set your API credentials
export ANTHROPIC_API_KEY="sk-ant-..."
# or
export OPENAI_API_KEY="sk-..."

# 2. Run the live benchmark across 150 evaluations (5 runs per task)
uv run python benchmarks/tier1_outcome_benchmark.py --runs 5
```

The benchmark will execute all 150 live queries, evaluate syntax and dataset correctness, and populate this report with empirical observed metrics.

---
*Report generated: 2026-09-06 22:57:52 UTC*