<div align="center">
  <img src="docs/assets/Text_Logo__Dark_-removebg-preview2.png" alt="Schemap Logo — Local Semantic Compiler" width="340" />

  <br/>
  <br/>

  <h1>Schemap</h1>
  <p><strong>The local semantic compiler for AI agents working with real databases.</strong></p>
  <p>Compile schema semantics, relationships, and database invariants into deterministic agent context.<br/>Verify generated SQL before it executes.</p>

  <p>
    <a href="https://pypi.org/project/schemap-tool/"><img src="https://img.shields.io/pypi/v/schemap-tool.svg?color=blue" alt="PyPI Version"></a>
    <a href="https://pypi.org/project/schemap-tool/"><img src="https://img.shields.io/pypi/pyversions/schemap-tool.svg" alt="Python Versions"></a>
    <a href="https://github.com/alansyahmi/Schemap/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
    <img src="https://img.shields.io/badge/Status-Beta-orange" alt="Status: Beta">
    <img src="https://img.shields.io/badge/Execution-Local%20Only-success" alt="Local First">
  </p>
</div>

---

## ⚡ The Architecture: Grounding → Generation → Verification

AI coding assistants (Cursor, Claude Code, Windsurf, Codex) are fluent in SQL syntax, but fail at production relational databases because raw schema DDL omits implicit operational invariants:

```text
                    SCHEMAP 4.0

                 ┌─────────────────┐
                 │ Database Schema │
                 └────────┬────────┘
                          │ (Introspect tables, FKs, types)
                          ▼
               ┌─────────────────────┐
               │  Semantic Compiler  │
               │                     │
               │ • Entity Roles      │
               │ • Measure Units     │
               │ • Join Graphs       │
               │ • Tenant Invariants │
               │ • Lifecycle Rules   │
               │ • Provenance Tags   │
               └─────────┬───────────┘
                         │
                         ▼
                   GroundedPlan
                         │ (Provided to LLM via MCP or CLI)
                         ▼
               ┌─────────────────────┐
               │   AI Coding Agent   │
               │   (Claude, Cursor,  │
               │    Gemini, Codex)   │
               └─────────┬───────────┘
                         │
                         ▼
                   Generated SQL
                         │
                         ▼
               ┌─────────────────────┐
               │  AST Policy Engine  │
               │                     │
               │ • Mutation blocking │
               │ • Tenant validation │
               │ • Soft-delete check │
               │ • Cartesian hazard  │
               └─────────┬───────────┘
                         │
             ALLOW / REJECT / RE-VALIDATE
                         │
                         ▼
                  Database Execution
```

---

## 🛑 The Problem: The Hidden Traps of Naked Schema Prompts

In production databases, queries fail not from syntax errors, but from missing invariants:

* **The "Cents Illusion":** Models sum integer currency columns (`amount_cents`), reporting **$19,900.00** instead of **$199.00** ($100\times$ metric distortion).
* **Zombie Records:** Soft-deleted records and cancelled subscriptions (`deleted_at IS NOT NULL` or `is_deleted = TRUE`) are counted as active data.
* **Tenant Data Leaks:** Multi-table joins drop tenant predicates (`org_id`), leaking neighboring customer records.
* **Cartesian Hazards:** Disconnected joins (`FROM invoices, plans`) produce accidental Cartesian products.
* **Destructive Operations:** Agents generate `DELETE` or `DROP TABLE` queries without execution safeguards.

---

## 🚀 Quick Start: Model Context Protocol (MCP)

Schemap exposes three native MCP tools for Cursor, Claude Code, and Windsurf.

### 1. Configure MCP Server

Add Schemap to your `claude_desktop_config.json` or `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "schemap": {
      "command": "uvx",
      "args": ["schemap-tool", "mcp"],
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/production_db"
      }
    }
  }
}
```

*Zero YAML required.* Schemap inspects the database connection locally and provides three tools:

| Tool | Phase | Function |
| :--- | :--- | :--- |
| **`schemap_ground`** | *Before writing SQL* | Resolves target tables, foreign-key join paths, monetary measures, and tenant invariants with explicit provenance (`[DECLARED]` vs `[INFERRED]`). |
| **`schemap_verify`** | *Before executing SQL* | Deny-by-default AST policy circuit breaker that blocks mutations (`DELETE`, `DROP`, `UPDATE`), Cartesian products, and tenant omissions. |
| **`schemap_patch`** | *Remediating SQL* | Injects missing tenant and soft-delete filters, then **re-validates** the patched AST to ensure no hazards remain. |

---

## 💻 CLI Usage

For terminal workflows, scripts, and local pair-programming:

```bash
# 1. Ground an analytical question before writing SQL
schemap ground "What was Org 42's revenue last month?" --db "$DATABASE_URL" --tenant-id 42

# 2. Verify SQL before executing against production
schemap verify "SELECT * FROM orders" --db "$DATABASE_URL" --tenant-id 42

# 3. Patch missing invariants with safety re-verification
schemap patch "SELECT * FROM orders" --db "$DATABASE_URL" --tenant-id 42
```

---

## 🔬 Evidence & Evaluation

Schemap maintains three canonical evaluation documents separating live model reasoning, controlled policy verification, and domain generalization:

### 1. Master Methodology & Headline Results — [EVALUATION.md](EVALUATION.md)
* **Analytical Success:** In our 500-task controlled benchmark on seeded operational schemas, the raw-schema baseline achieved **10.6%** first-pass analytical success versus **90.0%** with Schemap grounding.
* **Destructive Operation Blocking:** Schemap blocked **100% of unsafe operations** tested in our mutation suite (0 escapes).
* **Decoupled Denominators:** Analytical correctness and mutation safety are independently measured.

### 2. Live Model-in-the-Loop Evaluation — [LIVE_MODEL_EVALUATION.md](LIVE_MODEL_EVALUATION.md)
* Evaluates live completions from **Gemini 3.8 Flash** executing against a seeded SQLite operational database.
* **Exact Dataset Match:** Lifted from **2/8 (25%)** on raw DDL to **8/8 (100%)** with Schemap grounding.
* **Safety Gate:** Unguarded models produced 2 destructive mutations; `schemap_verify` blocked 2/2.

### 3. Cross-Domain Generalization — [GENERALIZATION.md](GENERALIZATION.md)
* Evaluates heuristic convention discovery across **6 non-SaaS domains** (E-Commerce, Fintech Ledger, Healthcare EHR, Education LMS, HR & Payroll, IoT Fleet).
* Implements a three-tier provenance model:
  - **`DECLARED`**: Explicit constraints defined in DDL or configuration.
  - **`INFERRED`**: Recovered via structural conventions (e.g. `_cents`, `_id`, timestamps).
  - **`UNKNOWN`**: Flagged ambiguities (e.g., dual foreign keys between the same tables) requiring human declaration.

---

## 🗄️ Supporting Tools & Capabilities

Beyond real-time MCP grounding, Schemap includes tools for local repo maintenance:

* **Static Agent Context:** `schemap context` compiles a token-compressed `schemap_database_context.md`.
* **Agent Rule Files:** `schemap agents` generates synchronized `CLAUDE.md`, `AGENTS.md`, and `.cursorrules`.
* **Schema Health Diagnostic:** `schemap doctor` audits missing foreign keys, orphan tables, and naming consistency.
* **Supported Databases:** PostgreSQL, MySQL, SQLite, Turso / libSQL, Oracle.

---

## 📄 License & Community

Schemap is licensed under the [MIT License](LICENSE).
* Website: [schemap-tool.pages.dev](https://schemap-tool.pages.dev/)
* Issues & Contributions: [github.com/alansyahmi/Schemap](https://github.com/alansyahmi/Schemap)
