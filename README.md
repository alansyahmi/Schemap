<div align="center">
  <img src="docs/assets/Text_Logo__Dark_-removebg-preview.png" alt="Schemap Logo — AI Database Context Compiler" width="320" />
</div>

<br/>

<div align="center">
  <h1>Stop AI Agents From Guessing Your Database.</h1>
  <p><strong>The Deterministic AI Database Context Compiler for Claude Code, Cursor, Codex, and Copilot.</strong></p>
</div>

<br/>

[![PyPI Version](https://img.shields.io/pypi/v/schemap-tool.svg)](https://pypi.org/project/schemap-tool/)
[![Python Version](https://img.shields.io/pypi/pyversions/schemap-tool.svg)](https://pypi.org/project/schemap-tool/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Why Schemap?

Modern **AI coding agents** (Claude Code, Cursor, GitHub Copilot, Codex) struggle with complex production databases. 

Raw `pg_dump` SQL dumps waste **10,000+ tokens**, introduce noisy system metadata, cause broken multi-table JOINs, and force LLMs to guess business relationships.

**Schemap solves this.** Schemap is a deterministic CLI compiler that extracts database schemas, computes **AI Readiness Scores**, and generates compressed, token-optimized context maps (`database_context.md`, `CLAUDE.md`, `AGENTS.md`).

- **90%+ Token Reduction:** Cut database prompt overhead from ~18,000 tokens to ~1,100 tokens.
- **100% Deterministic & Private:** Runs locally without external API keys. Zero data leaves your network.
- **Sub-2ms Compilation:** Compiles 200+ table database schemas in under 3 milliseconds.
- **Multi-Database Support:** PostgreSQL, MySQL, Turso / libSQL, SQLite, and Oracle.

---

## Benchmark: Raw SQL vs. Schemap Context

| Metric | Raw SQL Dump | Schemap AI Context | Difference |
| :--- | :--- | :--- | :--- |
| **Token Footprint** | ~18,432 tokens | **~1,120 tokens** | **93.9% Token Reduction** |
| **Relationship Mapping** | Implicit / Scattered | **Explicit FK Graph** | **Instant JOIN Clarity** |
| **AI Readiness Score** | Unmeasured | **Diagnosed (e.g. 78/100)** | **Actionable Fix Roadmap** |
| **Agent Rule Files** | None | **CLAUDE.md & AGENTS.md** | **Native Agent Integration** |

---

## Installation & Quick Start

Install Schemap via PyPI (or `uv`):

```bash
pip install schemap-tool
```

### 1. Initialize Configuration
Generate a lightweight `schemap.yaml` config file:

```bash
schemap init
```

*For full boilerplate options (domain mappings, schema overrides):*
```bash
schemap init --full
```

### 2. Run Database Health Diagnostic (`schemap doctor`)
Diagnose database readiness and identify missing foreign keys, undocumented tables, or ambiguous column names:

```bash
schemap doctor
```

*Output:*
```text
==================================================
 Schemap AI Database Health Check
==================================================
  Connection:            Connected (39 tables)
  Relationships Analyzed: 26
--------------------------------------------------
  AI Readiness Score:
  [###########---------] 53/100

  Top Issues Identified:
  - [Priority 1 - Missing Documentation] 39 tables lack descriptions/comments (-20 pts)
  - [Priority 2 - Disconnected Entities] 20 tables have no foreign keys (-7 pts)
  - [Priority 3 - Ambiguous Naming] 44 unresolved abbreviations detected (-20 pts)
--------------------------------------------------
 Recommendation: Run `schemap context` to generate AI-ready database context.
==================================================
```

### 3. Compile AI Database Context (`schemap context`)
Compile `database_context.md` containing relationship maps, central tables, and standard SQL JOIN snippets:

```bash
schemap context
```

### 4. Generate Agent Instruction Files (`schemap agents`)
Generate `CLAUDE.md` and `AGENTS.md` rules for your workspace:

```bash
schemap agents
```

### 5. Benchmark Context Efficiency (`schemap benchmark`)
Measure real-time token compression and compilation speed:

```bash
schemap benchmark
```

---

## Complete CLI Reference

| Command | Purpose | JSON Output Flag |
| :--- | :--- | :--- |
| `schemap doctor` | Onboarding health check & diagnostic | `schemap doctor --json` |
| `schemap context` | Compile `database_context.md` context map | `schemap context --format=json` |
| `schemap agents` | Generate `CLAUDE.md` and `AGENTS.md` | N/A |
| `schemap benchmark` | Measure raw SQL vs Schemap token savings & latency | `schemap benchmark --json` |
| `schemap score` | Analyze AI Readiness Score (0-100) & issue roadmap | `schemap score --json` |
| `schemap inspect` | Inspect raw database table & column metadata | `schemap inspect --json` |
| `schemap diff` | Track structural schema changes (`+`, `~`, `-`) | N/A |

---

## Supported Databases

- **PostgreSQL** (`postgresql://user:password@localhost:5432/my_db`)
- **Turso / Remote libSQL** (`libsql://...`)
- **Local SQLite** (`sqlite:///path/to/db.sqlite3`)
- **MySQL** (`mysql://user:password@localhost:3306/my_db`)
- **Oracle** (`oracle://user:password@localhost:1521/my_db`)

---

## CI/CD Integration & Licensing

Automate context map updates on every migration commit with GitHub Actions:

- **Free Tier:** Inspect & compile database context locally for databases up to 50 tables.
- **Pro Tier:** Unlimited tables, schema diff intelligence, and CI/CD GitHub Actions integration.

---

## Key Terms & Keywords (SEO)

`database context for AI agents` • `Claude Code database schema` • `Cursor rules database context` • `SQL token reduction` • `database schema to markdown` • `MCP database server` • `LangChain database tool` • `text-to-SQL prompt optimization` • `AI database schema generator`
