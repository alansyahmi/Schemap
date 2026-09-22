# Schemap 4.0.0 Release Notes — Deterministic AI Data Access & Governance

Schemap 4.0 marks a major product milestone: transitioning Schemap from a passive markdown context generator into a deterministic, governed interface for AI data access.

> **Database → Semantic Compiler → Policy Engine → Verified SQL Execution**  
> *"Postgres → AI API. Automatically. No YAML required to get started."*

---

## 🌟 What's New in 4.0.0

### 1. Dual-Payload Model Context Protocol (MCP) Server
* Native support for Cursor, Claude Desktop, Claude Code, and Windsurf via standard JSON-RPC 2.0 MCP.
* Every tool call returns **dual output**:
  * Human-readable markdown in `content` for chat interfaces.
  * Machine-readable structured payloads in `structuredContent` conforming to declared `outputSchema`.
* **Zero Credentials in Prompts:** Schemap MCP reads connection strings directly from `DATABASE_URL` or `SCHEMAP_DATABASE_URL` in the environment. Zero configuration files or manual exports needed.

### 2. Three Native AI Agent Tools
* **`schemap_ground`:** Call before writing SQL. Resolves target tables, spanning-tree multi-hop JOIN paths, measures, and mandatory tenant/soft-delete invariants with visible provenance (`[INFERRED]` vs `[DECLARED]`).
* **`schemap_verify`:** Call before executing SQL. AST parser powered by `sqlglot` (Postgres dialect). Mutations (`DELETE`, `UPDATE`, `DROP`, `ALTER`, `TRUNCATE`, `INSERT`) are **deny-by-default**. SELECT queries are allowed unless policy invariants fail.
* **`schemap_patch`:** Explicitly auto-patches queries to inject missing tenant isolation predicates (`org_id = 42`) and soft-delete exclusions (`deleted_at IS NULL`) without silent execution.

### 3. Empirical Scientific Benchmark Evidence ($N=500$)
* **8.5× Higher Analytical Success:** 10.6% raw LLM success → **90.0%** Schemap grounded success across 500 controlled evaluations ($p < 10^{-10}$).
* **100% Mutations Blocked:** 0 destructive operations escaped the pre-execution AST circuit breaker.
* **0.0% False Alarms:** 100% specificity on safe, compliant queries.
* **Sub-Millisecond Overhead:** 0.12ms grounding + 0.53ms AST validation (< 1ms total local latency).
* **Universal Domain Generalization:** Verified across 6 non-SaaS industry schemas (E-Commerce, Fintech Ledger, Healthcare EHR, Education LMS, HR/Payroll, IoT Telematics) with zero human configuration.

### 4. Dual CLI Entry Points
* Registering both `schemap` and `schemap-tool` in `[project.scripts]`.
* Instant execution without cloning or manual virtual environment management:
  ```bash
  uvx schemap-tool --version       # Schemap 4.0.0
  uvx schemap-tool ground "What was total revenue?"
  uvx schemap-tool verify "SELECT * FROM orders"
  ```

---

## 📦 Upgrading to 4.0.0

Via **`uv`**:
```bash
uv tool install --upgrade schemap-tool
```

Via **`pip`**:
```bash
pip install --upgrade schemap-tool
```

Via **`uvx`** (Instant zero-install):
```bash
uvx schemap-tool --version
```
