<div align="center">
  <img src="docs/assets/Text_Logo__Dark_-removebg-preview.png" alt="Schemap Logo" width="300" />
</div>

<br/>

<div align="center">
  <strong>Token-Optimized Database Context for AI Pipelines.</strong>
</div>

<div align="center">
  Don't waste 50,000 tokens on raw SQL dumps. Schemap is a zero-friction CLI that condenses your database schema into an LLM-perfect data contract.
</div>

<br/>

## Why Schemap?

When building AI agents or RAG pipelines that interact with databases, developers usually dump raw `pg_dump` schemas into the context window. This wastes massive amounts of tokens, causes the LLM to hallucinate over irrelevant system tables, and breaks easily when schemas change.

**Schemap solves this.**
It natively connects to your database, strips out the noise, and generates a highly compressed, token-optimized Markdown file representing your exact data contract.

- **Zero-Friction:** No heavy setup. Generates a clean config in one command.
- **Multi-Dialect Routing:** Native support for PostgreSQL, MySQL, Oracle, Turso/libSQL, and SQLite.
- **Token Estimation:** Automatically calculates your exact token footprint (`~4,894 tokens`).
- **CI/CD Native:** Automatically run it in GitHub Actions to keep your context maps perfectly synced with your migrations.

## Installation

Schemap is published on PyPI. Install it globally or within your project environment:

```bash
pip install schemap
```

*(Note: We highly recommend using [uv](https://github.com/astral-sh/uv) for blazing-fast environment management.)*

## Quick Start

1. **Initialize the configuration:**
   Run the following command in your project root to generate a boilerplate `schemap.yaml` file:
   ```bash
   schemap init
   ```

2. **Configure your connection:**
   Open `schemap.yaml` and paste your database connection URL. You can also define wildcard exclusions to ignore system tables.
   ```yaml
   database:
     connection_url: "postgresql://user:password@localhost:5432/my_db"
     exclude_tables:
       - "spatial_ref_sys"
       - "alembic_version"
       - "*_history"
   ```

3. **Generate your context map:**
   ```bash
   schemap generate
   ```
   *Output:*
   ```text
   -> Loading configuration from ./schemap.yaml... OK
   -> Connecting to database... Connected. Found 39 active tables
   -> Validating schema objects contract... OK
   -> Compiling context engine via Jinja2... OK
   [SUCCESS] Context map generated successfully at ./llm_data_context.md [14.0 KB / ~4,894 tokens]
   ```

## Supported Databases

- PostgreSQL (`postgresql://...`)
- Turso / remote libSQL (`libsql://...`)
- Local SQLite (`sqlite:///...`)
- MySQL (`mysql://...`)
- Oracle (`oracle://...`)

## Continuous Integration (CI/CD)

Want to automate your context map generation every time you merge a database migration?

Run:
```bash
schemap init-ci
```
This drops a ready-to-use `.github/workflows/schemap.yml` action into your repository that runs Schemap and commits the new Markdown file automatically.

## Licensing

Schemap operates on a Frictionless License Model. 
- **Developer Tier (Free):** Use Schemap for free locally on databases with up to 10 tables.
- **Professional & Team Tiers:** For unlimited tables, wildcard filtering, and CI/CD pipeline automation, purchase a license key at [schemap.com](https://your-username.github.io/schemap).

Once purchased, simply drop your key into the `schemap.yaml`:
```yaml
database:
  license_key: "YOUR_LICENSE_KEY_HERE"
```

## Built With
- `psycopg` (PostgreSQL)
- `libsql` (Turso)
- `pymysql` (MySQL)
- `oracledb` (Oracle)
- `pydantic` v2 (Strict type-safety)
- `jinja2` (Markdown compilation)
- `tiktoken` (Token counting)
