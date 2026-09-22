# Schemap 4.0 Master Evaluation & Empirical Evidence

This document establishes the **canonical evaluation framework and master headline results** for Schemap 4.0.

For focused experimental deep-dives, see:
* **[`LIVE_MODEL_EVALUATION.md`](LIVE_MODEL_EVALUATION.md):** Real model-in-the-loop experiments (Google Gemini 3.8 Flash $N=10$ pilot with raw completion logs).
* **[`GENERALIZATION.md`](GENERALIZATION.md):** Out-of-Distribution (OOD) convention discovery across 6 non-SaaS industry domains.
* **Supplementary Raw Reports:** Listed in the [Index of Underlying Benchmark Fixtures](#-index-of-underlying-benchmark-fixtures).

---

## 🏆 Master Empirical Scorecard (Decoupled Denominators)

Following rigorous evaluation hygiene, we explicitly decouple **Analytical Data Correctness** from **Operational Safety & Enforcement** to prevent denominator blending:

| Evaluation Dimension | Raw Baseline (No Schemap) | Schemap Grounded | Schemap Grounded + AST Guardrail | Measured Result |
| :--- | :---: | :---: | :---: | :---: |
| **Analytical Query Success ($N=500$ controlled)** | 10.6% (53/500) | **90.0%** (450/500) | **90.0%** (450/500) | **8.5× Higher Analytical Success** |
| **Live Frontier Model Pilot ($N=10$ Gemini Flash)** | 20.0% (2/10) | **80.0%** (8/10) | **100.0%** (10/10)* | **4.0× Exact Answer Correctness** |
| **Destructive Mutation Defense ($N=50$ suite)** | 0.0% Blocked (100% Ran!) 🚨 | 0.0% Blocked | **100.0% Blocked (0 Escaped)** 🛡️ | **100% of tested mutations blocked** |
| **Cross-Tenant Data Isolation (Multi-Hop)** | 70.0% Safe (30% Leaked) | **100.0% Safe (0 Leaks)** | **100.0% Safe (0 Leaks)** | **0 cross-tenant leaks in evaluated set** |
| **Soft-Delete Invariant Compliance** | 50.0% Safe (50% Leaked) | **100.0% Safe (0 Leaks)** | **100.0% Safe (0 Leaks)** | **0 ghost records in evaluated set** |
| **Safe-Query Specificity (False Alarms)** | N/A | 0.0% | **0.0% (0 False Alarms)** | **100% Specificity on Safe Queries** |
| **Local Processing Overhead** | 0 ms | 0.12 ms | 0.65 ms total (< 1 ms) | **Sub-millisecond Latency** |

> \* *Clarification on Live Model 10/10:* On the 8 analytical tasks, exact match means matching database ground truth. On the 2 mutation tasks, passing denotes successful pre-execution interception by the AST circuit breaker, preventing unauthorized execution.

---

## 📊 Stratum Analysis: Where Schemap Wins vs. Where Raw Models Tie

Empirical evaluation reveals that modern frontier LLMs are **not uniformly incompetent**; rather, failure modes concentrate in specific database architectural trap classes:

```text
1. Straightforward Tenant SELECTs  → TIE (100% vs 100%)
   On clean, single-table queries with explicit tenant filters requested in the prompt,
   models already produce correct WHERE org_id = 42 clauses without Schemap.

2. Implicit Soft-Delete Lifecycles  → Grounded: 100%; Raw DDL: 33%
   When queries involve soft-deleted users (deleted_at IS NOT NULL), raw DDL fails to
   exclude deleted entities from aggregated metrics (e.g. usage events or payment history).

3. The "Cents Illusion" (Units)     → Grounded: 100%; Raw DDL: 0%
   Raw DDL prompts cause models to default to summing raw integer columns (SUM(amount_cents)),
   returning 199800 instead of $1,998.00 (a 100x metric error). Schemap measures enforce scaling.

4. Multi-Hop Join Traversal        → Grounded: 100%; Raw DDL: 0%
   When joining across unscoped or intermediate bridge tables (invoices -> subscriptions -> plans),
   raw models attempt direct shortcuts (invoices.subscription_id = plans.id) linking wrong entities.

5. Destructive Operations          → AST Guardrail: 100% Blocked; Unguarded: 0%
   Prompt injection or administrative requests (DELETE FROM users) execute unchecked on raw models.
   Schemap's AST circuit breaker intercepts 100% of tested mutations before database dispatch.
```

---

## 🔬 Core Product Architecture

```text
Database Schema
      ↓
Semantic Compiler
   ├── target tables
   ├── join spanning trees
   ├── resolved measures
   ├── tenant invariants
   ├── soft-delete lifecycles
   └── provenance ([INFERRED] vs [DECLARED])
          ↓
     GroundedPlan
          ↓
   AI Coding Agent
 (Cursor / Claude / Copilot)
          ↓
      Draft SQL
          ↓
  AST Policy Engine
   ├── mutation blocking
   ├── tenant check
   ├── soft-delete check
   └── join hazard detection
          ↓
   Database Execution
```

---

## 📦 Index of Underlying Benchmark Fixtures

For full scientific transparency and local reproduction, all raw test harnesses and detailed reports are versioned in `benchmarks/`:

1. **[`benchmarks/scaled_evaluation_500.py`](benchmarks/scaled_evaluation_500.py):** 500-task statistical parameterized battery ([Report](benchmarks/SCALED_EVALUATION_500_REPORT.md)).
2. **[`benchmarks/run_n50_benchmark.py`](benchmarks/run_n50_benchmark.py):** Deterministic 50-task policy and gold-SQL regression suite ([Report](benchmarks/N50_BENCHMARK_REPORT.md)).
3. **[`benchmarks/live_gemini_eval.py`](benchmarks/live_gemini_eval.py):** 10-task model-in-the-loop pilot harness with logged completions ([Report](benchmarks/LIVE_GEMINI_EVALUATION_REPORT.md)).
4. **[`benchmarks/live_gemini_n50_eval.py`](benchmarks/live_gemini_n50_eval.py):** Automated N=50 live model completion runner ([Completions JSON](benchmarks/live_gemini_n50_completions.json)).
5. **[`benchmarks/multi_domain_ood_benchmark.py`](benchmarks/multi_domain_ood_benchmark.py):** Out-of-distribution 6-domain discovery benchmark ([Report](benchmarks/MULTI_DOMAIN_OOD_REPORT.md)).
6. **[`benchmarks/tier1_token_benchmark.py`](benchmarks/tier1_token_benchmark.py):** Token reduction & annual model economics profiling across 15 models ([Report](benchmarks/TIER1_TOKEN_REPORT.md)).
