# ⚠️ Schemap Tier 2 Benchmark: AI Text-to-SQL Accuracy & Hallucination Elimination

> **STATUS: BENCHMARK NOT RUN — requires an API key and live LLM execution.**  
> **Reason:** `Live LLM API credentials missing or invalid.`  
> *No live LLM API calls were executed. To prevent misleading or synthetic metrics, Schemap does not fabricate or substitute synthetic results.*

---

## Methodology & Reproduction
To run live text-to-SQL accuracy evaluations across Chinook, Northwind, and Pagila:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
uv run python benchmarks/tier2_live_eval.py
```

*Report generated: 2026-09-06 22:58:10 UTC*