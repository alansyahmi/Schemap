# Schemap MCP Distribution & Registry Kit

This document provides ready-to-use distribution manifests, registry submission templates, and copy-paste client configurations for listing and spreading **Schemap MCP** across the Model Context Protocol ecosystem.

---

## 1. Registry Submission Information

Use this metadata when submitting Schemap to:
* **Smithery.ai** (`https://smithery.ai`)
* **Glama.ai MCP Registry** (`https://glama.ai/mcp/servers`)
* **Awesome MCP Servers** (`https://github.com/modelcontextprotocol/servers` & community lists)
* **mcp.run / Cursor Directory** (`https://cursor.directory`)

| Field | Value |
| :--- | :--- |
| **Server Name** | `schemap-mcp` |
| **Display Name** | Schemap — AI Database Context & Guardrails |
| **Description** | Token-compressed database schema compiler, automated shortest-path SQL JOIN resolver, PII sanitizer, and query immutability guardrails for AI coding agents. |
| **Package / Command** | `uvx schemap-tool mcp` or `pip install schemap-tool && schemap-tool mcp` |
| **License** | MIT |
| **Repository** | https://github.com/alansyahmi/Schemap |
| **Website** | https://schemap-tool.pages.dev |
| **Supported Protocols** | Model Context Protocol (MCP) JSON-RPC 2.0 (stdio) |
| **Key Tools** | `schemap_get_schema`, `schemap_get_join_path`, `schemap_validate_query`, `schemap_get_glossary`, `schemap_check_blast_radius` |

---

## 2. Copy-Paste Client Configurations

### A. Claude Desktop (`claude_desktop_config.json`)

**MacOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "schemap": {
      "command": "uvx",
      "args": ["schemap-tool", "mcp", "--config", "/absolute/path/to/schemap.yaml"]
    }
  }
}
```
*(If using standard Python without `uvx`, replace `"command": "uvx"` with `"command": "python"` and `"args": ["-m", "schemap.cli", "mcp", "--config", "..."]`)*

---

### B. Cursor (`.cursor/mcp.json`)

Place this in your workspace root at `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "schemap": {
      "command": "uvx",
      "args": ["schemap-tool", "mcp", "--config", "./schemap.yaml"]
    }
  }
}
```

---

### C. Windsurf (`~/.codeium/windsurf/mcp_config.json`)

```json
{
  "mcpServers": {
    "schemap": {
      "command": "uvx",
      "args": ["schemap-tool", "mcp", "--config", "./schemap.yaml"]
    }
  }
}
```

---

## 3. What Makes Schemap MCP Different from Raw SQL MCP Servers?

When posting or pitching Schemap on Reddit (e.g. `r/Cursor`, `r/ClaudeAI`, `r/LocalLLaMA`, `r/PostgreSQL`):

| Traditional Raw SQL MCP Servers | Schemap MCP |
| :--- | :--- |
| **Blind Execution:** Lets the agent execute raw SQL directly, risking accidental `DELETE` / `DROP TABLE` or high resource queries. | **Guardrails First:** Contains automated safety checks (`schemap_validate_query`) preventing destructive queries and enforcing soft-delete policies. |
| **Token Bloat:** Dumps 10,000–30,000 tokens of raw DDL, indexes, and constraints into agent context. | **Compressed Token Map:** Delivers an 80%+ compressed schema representation with explicit FK topologies. |
| **Broken Multi-Hop JOINs:** Agents hallucinate intermediate tables when schemas have 10+ tables. | **Dynamic Path Solving:** `schemap_get_join_path` finds the shortest verified JOIN route between any two tables automatically. |
| **Privacy Leaks:** Raw DDL exposes PII column formats and sample data. | **Auto-Sanitization:** Strips PII and credential markers by default before returning schema context. |
