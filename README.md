<div align="center">
  <img src="docs/assets/Text_Logo__Dark_-removebg-preview2.png" alt="Schemap Logo — AI Database Context Compiler" width="340" />

  <br/>
  <br/>

  <h1>Stop AI Agents From Guessing Your Database.</h1>
  <p><strong>The Deterministic AI Database Context Compiler for Claude Code, Cursor, Windsurf, Codex, and Copilot.</strong></p>

  <p>
    <a href="https://pypi.org/project/schemap-tool/"><img src="https://img.shields.io/pypi/v/schemap-tool.svg?color=blue" alt="PyPI Version"></a>
    <a href="https://pypi.org/project/schemap-tool/"><img src="https://img.shields.io/pypi/pyversions/schemap-tool.svg" alt="Python Versions"></a>
    <a href="https://github.com/alansyahmi/Schemap/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
    <img src="https://img.shields.io/badge/Claude%20Code-Supported-6366f1?logo=anthropic" alt="Claude Code">
    <img src="https://img.shields.io/badge/Cursor-Rules%20Ready-000000" alt="Cursor">
    <img src="https://img.shields.io/badge/Privacy-100%25%20Local--First-10b981" alt="Local First">
  </p>
</div>

---

## ⚡ The Problem: Why AI Coding Agents Fail at SQL

Modern AI coding agents (Claude Code, Cursor, GitHub Copilot, Codex) struggle with production databases:
* Raw `pg_dump` SQL dumps waste **10,000+ tokens** of precious context window.
* Cluttered DDL dumps introduce noisy system metadata and lock definitions.
* LLMs hallucinate non-existent foreign keys (e.g. guessing `orders.customer_id` when the column is `orders.user_id`), creating broken multi-table `JOIN`s.

**Schemap solves this.** Schemap is a high-speed CLI compiler that introspects your database, computes an **AI Readiness Score**, and outputs clean, token-optimized context maps (`schemap_database_context.md`, `CLAUDE.md`, `AGENTS.md`).

---

## 📊 Before vs. After Schemap

| Metric | Raw SQL Dump (`pg_dump`) | Schemap Compiled Context | Impact |
| :--- | :--- | :--- | :--- |
| **Token Footprint** | ~14,500 tokens | **~820 tokens** | **94% Context Window Savings** |
| **Relationship Mapping** | Implicit / Scattered across DDL | **Explicit Foreign Key Graph** | **Zero Broken JOIN Queries** |
| **Database Diagnostics** | Unmeasured | **AI Readiness Score (e.g. 88/100)** | **Identifies Missing FKs & Gaps** |
| **Agent Rule Files** | None | **Auto-generated `CLAUDE.md` & `AGENTS.md`** | **Instant Workspace Sync** |
| **Compilation Latency** | Slow DDL export | **< 3ms local execution** | **Instant CI/CD & CLI feedback** |

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
| `schemap benchmark` | Measure raw SQL vs. Schemap token savings & speed | `schemap benchmark --json` |
| `schemap score` | Calculate AI Readiness Score (0–100) & improvement roadmap | `schemap score --json` |
| `schemap explain` | Explain table architecture, columns, and relationships | `schemap explain <table_name>` |
| `schemap join` | Find foreign key join paths and generate SQL snippets | `schemap join <table> <table>` |
| `schemap diff` | Track structural schema changes (`+`, `~`, `-`) | N/A |
| `schemap export` | Export schema as JSON or code for Agent Frameworks | `schemap export --format=json` |
| `schemap hook` | Install/manage Git pre-commit hooks for auto-compilation | `schemap hook install` |
| `schemap watch` | Watch directory for changes and auto-regenerate context | N/A |

---

## 🗄️ Supported Databases

* **PostgreSQL** (`postgresql://user:password@localhost:5432/my_db`)
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
name: Update Schemap Context

on:
  push:
    branches: [main]
    paths:
      - 'migrations/**'
      - 'alembic/versions/**'
      - 'prisma/schema.prisma'

jobs:
  update-schema-map:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          version: "latest"
      - name: Compile Schemap Context
        env:
          SCHEMAP_LICENSE_KEY: ${{ secrets.SCHEMAP_LICENSE_KEY }}
        run: uvx schemap-tool context
      - name: Commit and Push Updated Context
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add schemap_database_context.md CLAUDE.md AGENTS.md
          git diff --quiet && git diff --staged --quiet || (git commit -m "docs: auto-update AI database context" && git push)
```

---

## 🔑 License & Editions

* **Free Tier:** Full local CLI for databases up to 100 tables, including diagnostics, scoring, context compilation, diffs, benchmarks, and exports.
* **Pro Tier:** Unlimited tables, team seat management, CI/CD automated workflows, and production support.

### License Management
```bash
# Activate a Pro license key
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
    <a href="https://schemap-tool.pages.dev/#features">Documentation</a> •
    <a href="https://github.com/alansyahmi/Schemap/issues">Issues & Support</a>
  </p>
</div>
