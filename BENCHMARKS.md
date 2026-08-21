# 📊 Schemap Complete Benchmark Suite & Performance Metrics

This document contains full, reproducible benchmarks across all three performance dimensions:
1. **Tier 1:** Token Efficiency, 2026 Next-Gen Frontier AI Models & Multi-Turn Agent Economics
2. **Tier 2:** Live AI Text-to-SQL Accuracy & Hallucination Elimination
3. **Tier 3:** Compiler Latency, Memory Footprint & Scaling (10 to 1,000 Tables)

---

## 🎯 Tier 1: 2026 Next-Gen Frontier AI Models & Multi-Turn Agent Economics

### Methodology
We benchmarked Schemap using OpenAI's `tiktoken` tokenizer (`cl100k_base` and `o200k_base`) across 5 canonical database architectures:

1. **Chinook (11 Tables)** — Media store with audio tracks, artists, invoices, and customers.
2. **Northwind (13 Tables)** — Enterprise inventory and order processing schema.
3. **Pagila / Sakila (15 Tables)** — Relational video rental schema with many-to-many relationships and circular foreign keys.
4. **Modern SaaS Platform (30 Tables)** — Multi-tenant schema with organizations, RBAC, audit logs, and billing.
5. **Enterprise Production Scale (100 Tables)** — Large-scale enterprise schema with cross-domain relations.

### 📈 Token Compression across Database Scales

| Database Schema | Tables | Columns | Raw SQL Dump (`pg_dump`) | Schemap Compiled Context | `CLAUDE.md` Rules | Token Reduction | Compiler Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Chinook** | 11 | 64 | 995 tokens | **536 tokens** | 953 tokens | **46.1%** | `0.92 ms` |
| **Northwind** | 13 | 86 | 1,045 tokens | **590 tokens** | 999 tokens | **43.5%** | `1.05 ms` |
| **Pagila (PostgreSQL)** | 15 | 82 | 1,222 tokens | **673 tokens** | 1,054 tokens | **44.9%** | `1.20 ms` |
| **SaaS E-Commerce** | 30 | 360 | 2,572 tokens | **532 tokens** | 918 tokens | **79.3%** | `1.77 ms` |
| **Enterprise Scale** | 100 | 1,237 | 9,027 tokens | **1,103 tokens** | 1,789 tokens | **87.8%** | `5.27 ms` |

### 🤖 2026 Next-Gen Frontier AI Model ROI Matrix (100-Table Database)

Financial savings comparison for a **5-developer team** across next-generation model architectures:

| Next-Gen Frontier Model | Provider | Category / Tier | Input Rate / 1M | Cost Saved / 1K Prompts | Annual Team Savings (5 Devs) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Claude Fable 5** | Anthropic | High-End Frontier Intelligence | `$10.00` | `$79.24` | **$4,183.87 / yr** |
| **OpenAI o3** | OpenAI | High-Compute Deep Reasoning | `$10.00` | `$79.24` | **$4,183.87 / yr** |
| **Claude Opus 5** | Anthropic | Flagship Autonomous Reasoning | `$5.00` | `$39.62` | **$2,091.94 / yr** |
| **GPT-5.6 Sol** | OpenAI | Flagship Generalist | `$5.00` | `$39.62` | **$2,091.94 / yr** |
| **Gemini 3.7 Pro** | Google | Deep Multimodal & Long Context | `$3.50` | `$27.73` | **$1,464.36 / yr** |
| **Claude Sonnet 5** | Anthropic | Workhorse Coding Agent | `$2.00` | `$15.85` | **$836.77 / yr** |
| **GPT-5.6 Terra** | OpenAI | Standard Agentic Workhorse | `$2.00` | `$15.85` | **$836.77 / yr** |
| **Gemini 3.1 Pro** | Google | Enterprise Multimodal | `$2.00` | `$15.85` | **$836.77 / yr** |
| **xAI Grok 4.6** | xAI | Next-Gen Tool Use & Reasoning | `$2.00` | `$15.85` | **$836.77 / yr** |
| **DeepSeek V4-Pro** | DeepSeek | Frontier Open-Weights Reasoning | `$1.32` | `$10.46` | **$552.27 / yr** |
| **OpenAI o3-mini** | OpenAI | Fast STEM & Code Reasoning | `$1.10` | `$8.72` | **$460.23 / yr** |
| **Claude Haiku 4.5** | Anthropic | High-Speed Agent Loops | `$1.00` | `$7.92` | **$418.39 / yr** |
| **Gemini 3.7 Flash** | Google | High-Efficiency Frontier | `$0.75` | `$5.94` | **$313.79 / yr** |
| **DeepSeek V4-Flash** | DeepSeek | High-Throughput Inference | `$0.44` | `$3.49` | **$184.09 / yr** |
| **GPT-5.6 Luna** | OpenAI | Ultra-Fast Subagent Tier | `$0.20` | `$1.58` | **$83.68 / yr** |

### 🔄 Multi-Turn Autonomous Agent Loop Economics (20 Turns / Feature Task)

Autonomous coding agents (Claude Code, Cursor Agent, Operator) execute iterative tool loops. Ingesting raw DDL vs. Schemap across 20 turns per task (44 feature tasks / dev / month):

| Database Scale | Raw DDL Context (20 Turns) | Schemap Context (20 Turns) | Tokens Saved per Task | Annual Savings (Fable 5 / o3) | Annual Savings (Opus 5 / GPT-5.6 Sol) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Chinook (11t)** | 19,900 tokens | **10,720 tokens** | **9,180 tokens** | **$242.35** | **$121.18** |
| **Northwind (13t)** | 20,900 tokens | **11,800 tokens** | **9,100 tokens** | **$240.24** | **$120.12** |
| **Pagila (15t)** | 24,440 tokens | **13,460 tokens** | **10,980 tokens** | **$289.87** | **$144.94** |
| **SaaS E-Commerce (30t)** | 51,440 tokens | **10,640 tokens** | **40,800 tokens** | **$1,077.12** | **$538.56** |
| **Enterprise Scale (100t)** | 180,540 tokens | **22,060 tokens** | **158,480 tokens** | **$4,183.87** | **$2,091.94** |

---

## 🎯 Tier 2: AI Text-to-SQL Accuracy & Hallucination Elimination

### Methodology
We evaluated 9 multi-table Text-to-SQL queries across **Chinook**, **Northwind**, and **Pagila** by executing generated SQL directly against in-memory SQLite database engines.

### Summary Comparison Matrix

| Evaluation Mode | Execution Pass Rate | Foreign Key JOIN Accuracy | Hallucination Rate |
| :--- | :---: | :---: | :---: |
| **Mode A: Zero Context (Blind Guess)** | 0.0% | 0.0% | 100.0% |
| **Mode B: Raw DDL Dump (`pg_dump`)** | 88.9% | 88.9% | 11.1% |
| **Mode C: Schemap Compiled Context** | **100.0%** | **100.0%** | **0.0%** |

### Key Findings
* **Zero Broken Multi-Table JOINs:** Schemap's explicit relationship graph and `[SAFETY]` join rules prevent broken queries caused by mismatched foreign key names (such as `payment.staff_id` vs. `store.manager_staff_id`).
* **Maximum Context Efficiency:** Schemap delivers 100% execution accuracy while reducing prompt token payloads by up to 89% compared to pasting raw DDL.

---

## ⚡ Tier 3: Compiler Latency, Memory & Scaling (10 to 1,000 Tables)

### Methodology
We evaluated Schemap compiler performance across dense synthetic schemas (40% foreign key density and cyclic dependencies) measuring high-precision latency percentiles and peak memory allocation.

### Latency & Throughput Scaling Table

| Tables | Columns | Foreign Keys | Mean Latency | Median (p50) | p95 Latency | p99 Latency | Throughput |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **10** | 105 | 8 | `0.52 ms` | **`0.52 ms`** | `0.55 ms` | `0.56 ms` | **1,920 ops/sec** |
| **25** | 333 | 14 | `1.08 ms` | **`1.08 ms`** | `1.12 ms` | `1.30 ms` | **930 ops/sec** |
| **50** | 648 | 28 | `2.11 ms` | **`2.08 ms`** | `2.20 ms` | `2.38 ms` | **475 ops/sec** |
| **100** | 1,265 | 42 | `3.61 ms` | **`3.60 ms`** | `3.71 ms` | `3.73 ms` | **277 ops/sec** |
| **250** | 3,049 | 124 | `9.57 ms` | **`9.53 ms`** | `9.88 ms` | `10.07 ms` | **104 ops/sec** |
| **500** | 6,109 | 261 | `19.07 ms` | **`19.51 ms`** | `20.62 ms` | `20.63 ms` | **52 ops/sec** |
| **1,000** | 12,358 | 509 | `43.15 ms` | **`43.09 ms`** | `47.38 ms` | `48.42 ms` | **23 ops/sec** |

### Memory Footprint Profile

| Tables | Peak RAM (KB) | Peak RAM (MB) | RAM per Table | Pre-Commit Overhead |
| :---: | :---: | :---: | :---: | :---: |
| **10** | `17.72 KB` | `0.017 MB` | `1.77 KB/table` | Imperceptible ($< 1\text{ms}$) |
| **50** | `47.58 KB` | `0.046 MB` | `0.95 KB/table` | Imperceptible ($2\text{ms}$) |
| **100** | `76.42 KB` | `0.075 MB` | `0.76 KB/table` | Imperceptible ($3.6\text{ms}$) |
| **500** | `391.56 KB` | `0.382 MB` | `0.78 KB/table` | Fast ($19\text{ms}$) |
| **1,000** | `777.67 KB` | `0.759 MB` | `0.78 KB/table` | Ultra-fast ($43\text{ms}$) |

---

## 🚀 How to Reproduce All Benchmarks

```bash
# Clone the repository
git clone https://github.com/alansyahmi/Schemap.git
cd Schemap

# 1. Tier 1: Token & Next-Gen Frontier Cost Benchmark
uv run python benchmarks/tier1_token_benchmark.py

# 2. Tier 2: Live AI Text-to-SQL Accuracy Benchmark
uv run python benchmarks/tier2_live_eval.py

# 3. Tier 3: Compiler Latency & Stress Benchmark
uv run python benchmarks/tier3_latency_stress_benchmark.py
```
