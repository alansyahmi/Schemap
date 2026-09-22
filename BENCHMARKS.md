# Schemap Benchmark Suite & Evaluation Index

> **Notice:** Schemap 4.0 establishes a strict, three-tier canonical evaluation hierarchy to separate live model reasoning, controlled policy verification, and out-of-distribution heuristic discovery.

## 📖 Canonical Evaluation Documents

| Document | Scope | What It Measures | Headline Result |
| :--- | :--- | :--- | :--- |
| **[EVALUATION.md](EVALUATION.md)** | **Master Methodology & Headline Results** | Decoupled 500-task controlled benchmark & mutation safety suite | **10.6% → 90.0%** analytical match; **100%** tested mutations blocked |
| **[LIVE_MODEL_EVALUATION.md](LIVE_MODEL_EVALUATION.md)** | **Live Model-in-the-Loop Evaluation** | Actual Gemini 3.8 Flash model completions against seeded SQLite gold | **2/8 → 8/8** analytical match; **2/2** destructive operations blocked |
| **[GENERALIZATION.md](GENERALIZATION.md)** | **Cross-Domain Generalization** | Heuristic convention discovery across 6 non-SaaS domains | **6/6 domains passed** with zero configuration |

---

## ⚡ Supplementary Micro-Benchmarks: Efficiency & Latency

### Context Efficiency & Token Compression
Evaluated with OpenAI's `tiktoken` tokenizer (`cl100k_base` and `o200k_base`):

| Database Schema | Tables | Columns | Raw SQL Dump (`pg_dump`) | Schemap Compiled Context | Token Reduction | Compiler Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Chinook** | 11 | 64 | 995 tokens | **536 tokens** | **46.1%** | `0.92 ms` |
| **Northwind** | 13 | 86 | 1,045 tokens | **590 tokens** | **43.5%** | `1.05 ms` |
| **Pagila (PostgreSQL)** | 15 | 82 | 1,222 tokens | **673 tokens** | **44.9%** | `1.20 ms` |
| **SaaS E-Commerce** | 30 | 360 | 2,572 tokens | **532 tokens** | **79.3%** | `1.77 ms` |
| **Enterprise Scale** | 100 | 1,237 | 9,027 tokens | **1,103 tokens** | **87.8%** | `5.27 ms` |

### Compiler Latency & Scalability (Synthetic Schemas)
Benchmarked on synthetic schemas with 40% foreign key density:

| Tables | Columns | Foreign Keys | Mean Latency | Median (p50) | p95 Latency | Throughput |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **10** | 105 | 8 | `0.52 ms` | `0.52 ms` | `0.55 ms` | **1,920 ops/sec** |
| **50** | 648 | 28 | `2.11 ms` | `2.08 ms` | `2.20 ms` | **475 ops/sec** |
| **100** | 1,265 | 42 | `3.61 ms` | `3.60 ms` | `3.71 ms` | **277 ops/sec** |
| **500** | 6,109 | 261 | `19.07 ms` | `19.51 ms` | `20.62 ms` | **52 ops/sec** |
| **1,000** | 12,358 | 509 | `43.15 ms` | `43.09 ms` | `47.38 ms` | **23 ops/sec** |

---

## 🛠️ How to Reproduce

```bash
# 1. Master Controlled Evaluation (N=500)
uv run python benchmarks/scaled_evaluation_500.py

# 2. Live Model-in-the-Loop Evaluation (Gemini)
GEMINI_API_KEY="..." uv run python benchmarks/live_gemini_eval.py

# 3. Out-Of-Distribution (OOD) Domain Evaluation
uv run python benchmarks/multi_domain_ood_benchmark.py

# 4. Token & Latency Micro-Benchmarks
uv run python benchmarks/tier1_token_benchmark.py
uv run python benchmarks/tier3_latency_stress_benchmark.py
```
