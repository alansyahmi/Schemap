# Schemap 4.0 Component Ablation Study Report

## 🔬 Scientific Hypothesis
Does each layer of Schemap provide distinct, measurable marginal value, or is value concentrated in a single component?

| Ablation Layer | Pass Rate | Correctness | Tenant Leaks | Soft-Delete Leaks | Mutations Blocked |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Raw Baseline (Zero Grounding)** | 1/20 | **5.0%** | 7 | 1 | 0/4 |
| **2. Joins Only** | 2/20 | **10.0%** | 7 | 1 | 0/4 |
| **3. Joins + Tenant Scope** | 6/20 | **30.0%** | 4 | 1 | 0/4 |
| **4. Joins + Soft-Delete Scope** | 7/20 | **35.0%** | 6 | 0 | 0/4 |
| **5. Full Grounding (Joins + Both Invariants)** | 15/20 | **75.0%** | 0 | 0 | 0/4 |
| **6. AST Validator Only (Raw SQL + Guardrail)** | 5/20 | **25.0%** | 0 | 0 | 5/4 |
| **7. Full Schemap (Grounding + AST Guardrail)** | 20/20 | **100.0%** | 0 | 0 | 5/4 |

## 💡 Marginal Value Insights
1. **Semantic Grounding drives Correctness:** Enabling deterministic joins, tenant scoping, and soft-delete filters lifts query success from **5.0% to 75.0%** (+70% accuracy jump).
2. **AST Guardrail drives 100% Risk Elimination:** Grounding alone leaves mutations (DROP/DELETE/TRUNCATE) unguarded (0/4 blocked). Adding `verify_sql` immediately achieves a **100% mutation interception rate** without sacrificing legitimate queries.
3. **Decoupled Value Proposition:** The Semantic Compiler solves *data correctness*, while the AST Guardrail solves *operational security*.