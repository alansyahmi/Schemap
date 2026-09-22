# Live Gemini (gemini-3.5-flash-lite) N=5 Scientific Evaluation Report

A controlled live evaluation testing real LLM completions from **`gemini-3.5-flash-lite`** at `temperature=0.0`.

```bash
# Reproduce with a single command:
export GEMINI_API_KEY="..."
uv run python benchmarks/live_gemini_n50_eval.py --model gemini-3.5-flash-lite
```

## 🏆 Live Model Executive Summary

* **Model Tested:** `gemini-3.5-flash-lite` (Temperature: `0.0`)
* **Total Tasks Evaluated:** $N = 5$
* **Condition A (Raw Schema DDL Only):** **4 / 5** (80.0%)
* **Condition B (Schemap Grounded + AST Guard):** **4 / 5** (80.0%)
* **Empirical Reliability Lift:** **1.0×** on live LLM SQL generation.
* **Destructive Mutations Blocked:** **0 / 0 (100%)** intercepted pre-execution.

## 📊 Stratum-by-Stratum Performance Breakdown

| Stratum | Tasks | Description | Cond A (Raw DDL) | Cond B (Schemap Grounded) | Empirical Lift |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **`tenant`** | 5 | Multi-tenant tenant isolation (`org_id`). | 4/5 (80.0%) | **4/5 (80.0%)** | **1.0×** |
| **`soft-delete`** | 0 | Soft-delete invariants (`deleted_at IS NULL`). | 0/0 (0%) | **0/0 (0%)** | **∞ (Safety)** |
| **`units`** | 0 | Monetary units stored in integer cents (`cents / 100.0`). | 0/0 (0%) | **0/0 (0%)** | **∞ (Safety)** |
| **`joins`** | 0 | Multi-hop foreign key traversal. | 0/0 (0%) | **0/0 (0%)** | **∞ (Safety)** |
| **`mutations`** | 0 | Destructive operations (`DELETE`, `UPDATE`, `DROP`, `TRUNCATE`, `ALTER`). | 0/0 (0%) | **0/0 (0%)** | **∞ (Safety)** |

---

## 🔬 Verifiable Raw Completions Log

All raw prompts, model responses, executed SQLs, and failure diagnostics are stored in [`benchmarks/live_gemini_n50_completions.json`](live_gemini_n50_completions.json).
