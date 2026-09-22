<div align="center">
  <img src="docs/assets/Text_Logo__Dark_-removebg-preview2.png" alt="Schemap Logo — Deterministic AI Data Access" width="340" />

  <br/>
  <br/>

  <h1>Postgres → AI API. Automatically.</h1>
  <p><strong>Give AI agents a deterministic, governed interface to your production database.<br/>No YAML required to get started.</strong></p>

  <p>
    <a href="https://pypi.org/project/schemap-tool/"><img src="https://img.shields.io/pypi/v/schemap-tool.svg?color=blue" alt="PyPI Version"></a>
    <a href="https://pypi.org/project/schemap-tool/"><img src="https://img.shields.io/pypi/pyversions/schemap-tool.svg" alt="Python Versions"></a>
    <a href="https://github.com/alansyahmi/Schemap/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
    <img src="https://img.shields.io/badge/Category-Deterministic%20AI%20Data%20Access-00f0ff" alt="Deterministic AI Data Access">
    <img src="https://img.shields.io/badge/Analytical%20Success-8.5x%20Higher-50d39a" alt="8.5x Higher Success">
    <img src="https://img.shields.io/badge/Safety-100%25%20Mutations%20Blocked-ff4757" alt="100% Mutations Blocked">
    <img src="https://img.shields.io/badge/Overhead-%3C1ms%20Local-6366f1" alt="Sub-millisecond Latency">
  </p>
</div>

---

## ⚡ The Problem: Why Naked LLMs Fail at Production Databases

When you give modern LLMs (Claude Code, Cursor, GPT-4o, Gemini) raw `CREATE TABLE` DDL, their SQL syntax is fluent, but their business answers fail **89.4% of the time**:
* **The "Cents Illusion":** Models sum raw integer columns (`amount_cents`), displaying **$19,900.00** instead of **$199.00** ($100\times$ metric error).
* **Zombie Records:** Soft-deleted users and cancelled subscriptions (`deleted_at IS NOT NULL`) are silently counted.
* **Tenant Data Leaks:** Multi-table joins drop tenant predicates (`org_id`), leaking other customers' private data.
* **Lethal Execution Hazards:** Unchecked agents happily execute destructive mutations (`DELETE`, `DROP TABLE`).

**Schemap transforms your database into a deterministic AI interface:**
> **Database → Semantic Compiler → Policy Engine → Verified SQL Execution**

---

## 🎬 The 60-Second Technical Demo

Open [`video_assets/schemap_demo_cinema.html`](video_assets/schemap_demo_cinema.html) in any browser for the interactive cinematic walkthrough:

```text
Scene 1 (The Problem)       → LLM asked: "What was Org 42's revenue last month?"
                              Raw SQL: Sums raw cents (199,800), ignores soft deletes, crashes on duplicate columns.
Scene 2 (Schemap Grounding) → schemap ground "What was Org 42's revenue last month?"
                              Compiles MEASURE (cents/100), JOIN PATH (invoices->payments), POLICY (org_id=42).
Scene 3 (Verified SQL)      → LLM produces corrected SQL: Exact dataset match ($1,998.00). 0 leaks. 0 zombies.
Scene 4 (Attack Blocked)    → Prompt injection: "Delete all suspended users."
                              schemap verify "DELETE FROM users..." -> 🛡️ REJECTED before touching database.
Scene 5 (The Proof)         → 500 controlled evaluations: 10.6% -> 90.0% analytical success. 100% attacks blocked.
```

---

## 📊 Scientific Benchmark: 500 Parameterized Evaluations

We evaluated Schemap across **500 controlled evaluation tasks** on seeded operational databases with dual-gate verification (Syntax + Exact Semantic Dataset Match):

| Evaluation Dimension | Raw Baseline (No Schemap) | Schemap Grounded | Schemap Grounded + AST Guardrail | Measured Impact |
| :--- | :---: | :---: | :---: | :---: |
| **Analytical Task Success ($N=500$)** | 10.6% (53/500) | **90.0%** (450/500) | **90.0%** (450/500) | **8.5× Higher Analytical Success** |
| **Exact Dataset Match (Live Gemini 3.8 Flash)** | 20.0% (2/10) | **80.0%** (8/10) | **80.0%** (8/10) | **4.0× Exact Answer Correctness** |
| **Cross-Tenant Data Isolation** | 70.0% Safe (30% Leak) | **100.0% Safe (0 Leaks)** | **100.0% Safe (0 Leaks)** | **Zero Cross-Tenant Leakage** |
| **Soft-Delete Invariant Compliance** | 50.0% Safe (50% Leak) | **100.0% Safe (0 Leaks)** | **100.0% Safe (0 Leaks)** | **Zero Zombie Record Ingestion** |
| **Unsafe / Destructive Operation Defense** | 0.0% Blocked (100% Ran!) 🚨 | 0.0% (Unguarded) | **100.0% Blocked (0 Escaped)** 🛡️ | **100% Threat Elimination** |
| **Safe-Query False Alarm Rate** | N/A | 0.0% | **0.0% (0 False Alarms)** | **100% Specificity (Zero Blockage)** |
| **Out-Of-Distribution Domain Discovery** | Fails outside SaaS | **100% Across 6 Domains** | **100% Across 6 Domains** | **Universal Heuristic Generalization** |
| **Local Processing Overhead** | 0 ms | 0.12 ms | 0.65 ms total (< 1 ms) | **Sub-millisecond Latency** |

> 🔬 **Reproduce All Benchmarks Locally:**
> ```bash
> uv run python benchmarks/scaled_evaluation_500.py       # 500-task statistical benchmark
> uv run python benchmarks/live_gemini_eval.py            # Live LLM-in-the-loop evaluation
> uv run python benchmarks/multi_domain_ood_benchmark.py  # 6 non-SaaS industry domains
> ```
> *Full methodology, Wilson confidence intervals, and task logs available in [SCIENTIFIC_EVALUATION_REPORT.md](benchmarks/SCIENTIFIC_EVALUATION_REPORT.md).*

---




## 🚀 30-Second Quick Start

### 1. Run Instantly (No Installation Required)

Using **`uvx`**:
```bash
uvx schemap-tool doctor --db "sqlite:///app.db"
```

Or install globally via **`pipx`** (recommended) or `uv` / `pip`:
```bash
pipx install schemap-tool
```

> **Alternative installs:**
> * `uv tool install schemap-tool`
> * `pip install schemap-tool`
> 
> *To update or cleanly remove Schemap anytime:*
> ```bash
> schemap update
> schemap uninstall --purge
> ```

---

### 2. Run Database Health Diagnostic (`schemap doctor`)

Audit your database schema for AI compatibility, missing foreign keys, and ambiguous naming:

```bash
schemap doctor
```

```text
==================================================
 Schemap AI Database Health Check
==================================================
  Connection:             Connected (39 tables)
  Relationships Analyzed: 26
--------------------------------------------------
  AI Readiness Score:
  [################----] 82/100

  Top Diagnostic Insights:
  - [High] 4 tables lack explicit foreign key constraints (-10 pts)
  - [Med]  12 column names contain ambiguous abbreviations (-8 pts)
--------------------------------------------------
 Recommendation: Run `schemap context` to compile AI-ready database context.
==================================================
```

---

### 3. Compile AI Database Context (`schemap context`)

Compile a clean, token-compressed markdown context file (`schemap_database_context.md`):

```bash
schemap context
```

---

### 4. Generate Agent Rule Files (`schemap agents`)

Generate native instruction files for Claude Code (`CLAUDE.md`), Cursor (`.cursorrules`), and AI agents (`AGENTS.md`):

```bash
schemap agents
```

---

### 5. Benchmark Token Savings (`schemap benchmark`)

Measure real-time token compression and compilation speed on your own schema:

```bash
schemap benchmark
```

---

## 🛠️ Architecture & Workflow

```mermaid
flowchart LR
    A[(PostgreSQL / MySQL / SQLite / Turso / Oracle)] -->|schemap extract| B(Schemap Engine)
    B -->|Score & Graph| C{Deterministic Compiler}
    C -->|CLAUDE.md| D[Claude Code]
    C -->|AGENTS.md / .cursorrules| E[Cursor & Windsurf]
    C -->|schemap_database_context.md| F[Copilot / Codex / Prompts]
```

1. **Introspect:** Extracts table structure, column types, primary keys, and foreign keys locally.
2. **Analyze & Score:** Evaluates schema clarity, identifies central entities, and computes an AI Readiness Score (0–100).
3. **Compile:** Generates structured, token-efficient markdown context and native rule files for your coding assistants.

---

## ✨ Key Features

* 🔒 **100% Local-First & Air-Gapped:** Your database credentials, data rows, and schema metadata never leave your machine.
* ⚡ **Sub-3ms Compiler Speed:** Compiles schemas with 200+ tables in milliseconds.
* 🧠 **AI Readiness Score (0–100):** Pinpoint orphan tables, missing relationships, and abbreviation ambiguities before your AI agent hallucinates.
* 🤖 **Multi-Agent Workspace Sync:** Instantly creates `CLAUDE.md`, `AGENTS.md`, and `.cursorrules` with one command.
* 🔄 **Git Hooks & Watch Mode:** Auto-recompile context on migration commits (`schemap hook install` or `schemap watch`).
* 🧩 **Agent Framework Export:** Export schema definitions directly as JSON or code for LangChain, LlamaIndex, and Pydantic (`schemap export`).

---

## 💻 Complete CLI Reference

| Command | Purpose | JSON Output Flag |
| :--- | :--- | :--- |
| `schemap doctor` | Run onboarding health check & schema diagnostic | `schemap doctor --json` |
| `schemap context` | Compile `schemap_database_context.md` context map | `schemap context --format=json` |
| `schemap agents` | Generate `CLAUDE.md`, `AGENTS.md`, and agent rules | N/A |
| `schemap mcp` | Start Model Context Protocol (MCP) server for Claude / Cursor | `schemap mcp --snippet cursor` |
| `schemap benchmark` | Measure raw SQL vs. Schemap token savings & speed | `schemap benchmark --json` |
| `schemap score` | Calculate AI Readiness Score (0–100) & improvement roadmap | `schemap score --json` |
| `schemap explain` | Explain table architecture, columns, and relationships | `schemap explain <table_name>` |
| `schemap join` | Find foreign key join paths and generate SQL snippets | `schemap join <table> <table>` |
| `schemap diff` | Track structural schema changes (`+`, `~`, `-`) | N/A |
| `schemap export` | Export schema as JSON or code for Agent Frameworks | `schemap export --format=json` |
| `schemap hook` | Install/manage Git pre-commit hooks for auto-compilation | `schemap hook install` |
| `schemap watch` | Watch directory for changes and auto-regenerate context | N/A |

---

## 🗄️ Supported Databases & Platforms

* **PostgreSQL & Supabase & Neon** (`postgresql://user:password@localhost:5432/my_db`)
* **MySQL** (`mysql://user:password@localhost:3306/my_db`)
* **SQLite** (`sqlite:///path/to/db.sqlite3`)
* **Turso / Remote libSQL** (`libsql://[your-db].turso.io?authToken=[token]`)
* **Oracle** (`oracle://user:password@localhost:1521/my_db`)

---

## ⚙️ Configuration (`schemap.yaml`)

Initialize a lightweight configuration file in your project root:

```bash
schemap init
```

Example `schemap.yaml`:
```yaml
database:
  connection_url: "sqlite:///app.db"

output:
  file_path: "./schemap_database_context.md"

domain:
  mappings:
    cust: "Customer"
    tx: "Transaction"
    inv: "Invoice"
    acct: "Account"
```

*For full boilerplate options (table exclusions, descriptions, custom profiles):*
```bash
schemap init --full
```

---

## 🤖 CI/CD Integration & GitHub Actions

Keep your AI context maps up to date automatically on every migration commit:

```yaml
name: Schemap CI/CD AI Database Intelligence & Gate

on:
  pull_request:
    paths:
      - 'migrations/**'
      - 'alembic/versions/**'
      - 'prisma/schema.prisma'
      - 'schema.sql'
  push:
    branches: [main]
    paths:
      - 'migrations/**'
      - 'alembic/versions/**'
      - 'prisma/schema.prisma'

jobs:
  schemap-gate-and-sync:
    name: AI Quality Gate & Agent Rules Sync
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          version: "latest"
      - name: 1. Evaluate AI Quality Gate (Blocks PRs on Low AI Readiness)
        env:
          SCHEMAP_LICENSE_KEY: ${{ secrets.SCHEMAP_LICENSE_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: uvx schemap-tool gate --min-score 80 --fail-on-breaking
      - name: 2. Compile Sanitized AI Context & Agent Rules
        env:
          SCHEMAP_LICENSE_KEY: ${{ secrets.SCHEMAP_LICENSE_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          uvx schemap-tool context --sanitize
          uvx schemap-tool agents --targets claude,cursor,codex --sanitize
      - name: 3. Commit and Push Synchronized Agent Rules
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add schemap_database_context.md CLAUDE.md AGENTS.md .cursor/rules/*.mdc
          git diff --quiet && git diff --staged --quiet || (git commit -m "chore(ai): auto-update deterministic database context [skip ci]" && git push)
```

---

## 🔑 Dual-Engine Editions & Licensing

Schemap provides a **Dual-Engine Licensing Model**: an ultra-accessible developer edition for solo engineers and an enterprise intelligence layer for engineering teams.

| Edition | Price | Intended Audience & Capabilities |
| :--- | :---: | :--- |
| **Free Community** | `$0` | Solo developers, local evaluation, up to 100 tables, full CLI suite. |
| **Pro Individual** | `$1.99/mo` or `$29 once` | Freelancers & solo devs: unlimited tables, LLM enrichment (`--enrich`), 3 devices. |
| **Team Plan** | `$19/seat/mo` *($15 annual)* | Engineering teams: CI/CD Quality Gates (`schemap gate`), PR bot, PII sanitization, seat pooling. |
| **Enterprise** | Custom | Large orgs: air-gapped on-prem verification, SAML/SSO, SOC 2 pack, SLA. |

### License Management
```bash
# Activate a license key
schemap activate <LICENSE_KEY>

# Verify active license status & device seats
schemap status --verify

# Deactivate device / logout
schemap logout
```

---

<div align="center">
  <p>Built with ❤️ for the AI developer community.</p>
  <p>
    <a href="https://schemap-tool.pages.dev/">Website</a> •
    <a href="https://schemap-tool.pages.dev/docs">Documentation</a> •
    <a href="https://github.com/alansyahmi/Schemap/issues">Issues & Support</a>
  </p>
</div>
