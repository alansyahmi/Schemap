<div align="center">
  <img src="docs/assets/Text_Logo__Dark_-removebg-preview.png" alt="Schemap Logo" width="300" />
</div>

<br/>

<div align="center">
  <strong>The fastest way to make your database AI-ready.</strong>
</div>

<div align="center">
  Schemap evolves your database schemas into an AI Database Context Compiler. Turn complex database structures into optimized context for AI coding agents (Claude Code, Cursor, Codex, Copilot).
</div>

<br/>

## Product Architecture

Schemap operates in 3 deterministic layers:

1. **Layer 1: Database Intelligence** (`inspect`, `score`, `diff`)
2. **Layer 2: AI Context Generation** (`context`) -> `database_context.md`
3. **Layer 3: AI Agent Integration** (`agents`) -> `CLAUDE.md` & `AGENTS.md`

## CLI Commands

### 1. `schemap doctor`
Run the AI Database Health Check onboarding diagnostic to analyze schema health and get direct recommendations.

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
  ██████████░░░░░░░░ 53/100

  Top Issues Identified:
  - [Priority 1 - Missing Documentation] 39 tables lack descriptions/comments (-20 pts)
  - [Priority 2 - Disconnected Entities] 20 tables have no foreign keys (-7 pts)
  - [Priority 3 - Ambiguous Naming] 44 unresolved abbreviations detected (-20 pts)
--------------------------------------------------
 Recommendation: Run `schemap context` to generate AI-ready database context.
==================================================
```

### 2. `schemap context`
Compile AI-optimized database context (`database_context.md`) including:
- **Database Overview**
- **Schema Relationship Map**
- **Central Tables** (ranked by centrality & utility signal filtering)
- **Query Examples** (standard SQL JOIN snippets)

```bash
schemap context
```

### 3. `schemap benchmark`
Calculate context efficiency metrics comparing raw SQL dumps against Schemap context maps.

```bash
schemap benchmark
```

*Output:*
```text
==================================================
 Schemap Context Efficiency Benchmark
==================================================
  Raw SQL Dump:         6,714 tokens
  Schemap AI Context:   804 tokens
  Context Reduction:   88%
--------------------------------------------------
  Relationship Graph:   explicit graph (26 links)
  Agent Files Ready:    CLAUDE.md [OK], AGENTS.md [OK]
==================================================
```

### 4. `schemap score`
Analyze your schema's AI Readiness Score (0-100) and prioritized issue roadmap.

```bash
schemap score
```

### 5. `schemap agents`
Automatically generate target files for AI coding agents:
- `CLAUDE.md` (optimized for Claude Code & Anthropic models)
- `AGENTS.md` (standardized for Codex, Cursor, & AI agents)

```bash
schemap agents
```

### Machine-Readable JSON Output (`--json`)
Available on `schemap doctor`, `schemap score`, `schemap inspect`, and `schemap benchmark` for CI/CD pipelines & extensions:

```bash
schemap doctor --json
```

## Installation

```bash
pip install schemap-tool
```

## Supported Databases

- PostgreSQL (`postgresql://...`)
- Turso / remote libSQL (`libsql://...`)
- Local SQLite (`sqlite:///...`)
- MySQL (`mysql://...`)
- Oracle (`oracle://...`)

## Licensing

- **Free Tier:** Locally inspect and compile context for databases up to 50 tables.
- **Pro Tier:** Unlimited tables, advanced scoring, and CI/CD automation.
