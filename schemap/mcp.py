"""
Schemap Model Context Protocol (MCP) Server.

Provides a standard JSON-RPC 2.0 Model Context Protocol interface for AI coding agents
(Claude Desktop, Cursor, Windsurf, LangChain, Roo Code, etc.) to query Schemap dynamically
at runtime for schema context, JOIN path solving, SQL validation, glossary metrics, and blast-radius checks.
"""

import sys
import json
from typing import Dict, Any, List
from pathlib import Path

from .models import DatabaseSchemaModel
from .context import generate_database_context, sanitize_schema_for_llm, filter_schema_by_scope
from .query_explainer import find_join_path, explain_table, validate_query_against_schema
from .config import load_config
from . import __version__


MCP_TOOLS = [
    {
        "name": "schemap_get_schema",
        "description": "Returns token-compressed database schema context with column types, primary/foreign keys, ownership, and query guardrails.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of specific tables to retrieve. Omit for full schema."
                },
                "scope": {
                    "type": "string",
                    "enum": ["all", "analytics", "backend", "core"],
                    "default": "all",
                    "description": "Role-scoped schema filter profile."
                },
                "sanitize": {
                    "type": "boolean",
                    "default": True,
                    "description": "Automatically redact PII, credentials, and sensitive tokens for safety."
                }
            }
        }
    },
    {
        "name": "schemap_get_join_path",
        "description": "Finds the shortest verified JOIN path (physical or virtual foreign keys) between tables and returns a valid SQL JOIN template.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_table": {
                    "type": "string",
                    "description": "Source table name."
                },
                "to_table": {
                    "type": "string",
                    "description": "Target destination table name to join with."
                }
            },
            "required": ["from_table", "to_table"]
        }
    },
    {
        "name": "schemap_validate_query",
        "description": "Validates a SQL query string against known database tables, columns, data types, and organizational guardrails (e.g. soft-delete, tenant isolation, PII).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query string to validate."
                }
            },
            "required": ["sql"]
        }
    },
    {
        "name": "schemap_get_glossary",
        "description": "Retrieves business definitions, canonical calculation formulas, and global database policies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {
                    "type": "string",
                    "description": "Optional specific business metric or term (e.g., 'GMV', 'MRR'). If omitted, returns entire glossary."
                }
            }
        }
    },
    {
        "name": "schemap_check_blast_radius",
        "description": "Analyzes dependencies and safety risks for a table (incoming/outgoing FKs, degree centrality, and affected policies).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_table": {
                    "type": "string",
                    "description": "Target table name to analyze."
                }
            },
            "required": ["target_table"]
        }
    },
    {
        "name": "schemap_ground",
        "description": "Call before writing SQL for any analytical or multi-table question. Grounds a natural language query into deterministic target tables, spanning-tree JOIN paths, measures, and mandatory invariants with provenance (INFERRED vs DECLARED).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The natural language business or analytical question to ground."
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Optional tenant identifier to isolate query scope."
                }
            },
            "required": ["question"]
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "target_tables": {"type": "array", "items": {"type": "string"}},
                "join_sql": {"type": ["string", "null"]},
                "mandatory_filters": {"type": "array", "items": {"type": "string"}},
                "measures": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "table": {"type": "string"},
                            "column": {"type": "string"},
                            "expression": {"type": "string"},
                            "provenance": {"type": "string"}
                        },
                        "required": ["table", "column", "expression", "provenance"]
                    }
                },
                "provenance": {
                    "type": "object",
                    "additionalProperties": {"type": "string"}
                },
                "ambiguities": {"type": "array", "items": {"type": "string"}},
                "prompt_instructions": {"type": "string"}
            },
            "required": [
                "question",
                "target_tables",
                "mandatory_filters",
                "measures",
                "provenance",
                "ambiguities",
                "prompt_instructions"
            ]
        }
    },
    {
        "name": "schemap_verify",
        "description": "Call before executing any SQL. Deny-by-default for mutations (DELETE, UPDATE, DROP, ALTER, TRUNCATE, INSERT). SELECT queries are allowed unless policy fails. When patch=true and violations occur, use 'patched_sql' instead of the rejected original SQL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query to verify."
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Optional tenant identifier to enforce."
                },
                "patch": {
                    "type": "boolean",
                    "default": False,
                    "description": "Generate auto-patched SQL if violations occur. Defaults to false (never silently rewrites SQL unless explicitly requested)."
                }
            },
            "required": ["sql"]
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["allow", "reject"]},
                "passed": {"type": "boolean"},
                "violations": {"type": "array", "items": {"type": "string"}},
                "patched_sql": {
                    "type": ["string", "null"],
                    "description": "When patch=true and violations occur, use this sanitized query to execute safely."
                },
                "patch_requested": {"type": "boolean"}
            },
            "required": ["status", "passed", "violations", "patch_requested"]
        }
    },
    {
        "name": "schemap_patch",
        "description": "Only call when user explicitly wants auto-injected tenant or soft-delete filters. Auto-patches SQL using AST transformations without silent execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL query to patch."
                },
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier to inject."
                }
            },
            "required": ["sql", "tenant_id"]
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["allow", "reject"]},
                "passed": {"type": "boolean"},
                "violations": {"type": "array", "items": {"type": "string"}},
                "original_sql": {"type": "string"},
                "patched_sql": {"type": ["string", "null"]},
                "patch_applied": {"type": "boolean"}
            },
            "required": ["status", "passed", "violations", "original_sql", "patch_applied"]
        }
    }
]


def execute_tool(name: str, arguments: Dict[str, Any], schema_model: DatabaseSchemaModel) -> Dict[str, Any]:
    """
    Executes a Schemap MCP tool call and returns text content response.
    """
    if name == "schemap_get_schema":
        tables = arguments.get("tables")
        scope = arguments.get("scope", "all")
        sanitize = arguments.get("sanitize", True)

        model_to_use = schema_model
        if tables:
            req_set = {t.lower() for t in tables}
            filtered = [t for t in schema_model.tables if t.name.lower() in req_set]
            if filtered:
                model_to_use = DatabaseSchemaModel(
                    tables=filtered,
                    glossary=schema_model.glossary,
                    global_guardrails=schema_model.global_guardrails
                )

        ctx_md = generate_database_context(model_to_use, scope=scope, sanitize=sanitize)
        return {
            "content": [{"type": "text", "text": ctx_md}]
        }

    elif name == "schemap_get_join_path":
        from_table = arguments.get("from_table", "").strip()
        to_table = arguments.get("to_table", "").strip()
        if not from_table or not to_table:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "Error: Both 'from_table' and 'to_table' are required."}]
            }

        try:
            res = find_join_path(schema_model, [from_table, to_table])
            formatted = f"### JOIN Path Result: `{from_table}` ➔ `{to_table}`\n\n"
            if res.get("full_path"):
                formatted += f"**Traversal Path**: `{' ➔ '.join(res['full_path'])}`\n\n"
            formatted += f"```sql\n{res['sql_snippet']}\n```"
            return {"content": [{"type": "text", "text": formatted}]}
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": f"Error finding join path: {str(e)}"}]}

    elif name == "schemap_validate_query":
        sql = arguments.get("sql", "").strip()
        if not sql:
            return {"isError": True, "content": [{"type": "text", "text": "Error: 'sql' argument is required."}]}

        val_res = validate_query_against_schema(schema_model, sql)
        out_lines = [f"### SQL Validation Report", ""]
        if val_res["valid"]:
            out_lines.append("🟢 **Status**: Query is structurally aligned with schema.")
        else:
            out_lines.append("🔴 **Status**: Query contains schema errors / non-existent entities.")

        if val_res["tables_referenced"]:
            out_lines.append(f"- **Referenced Tables**: `{', '.join(val_res['tables_referenced'])}`")

        if val_res["errors"]:
            out_lines.append("\n**Errors**:")
            for err in val_res["errors"]:
                out_lines.append(f"- ❌ {err}")

        if val_res["warnings"]:
            out_lines.append("\n**Warnings & Security Notices**:")
            for w in val_res["warnings"]:
                out_lines.append(f"- ⚠️ {w}")

        if val_res["guardrails_triggered"]:
            out_lines.append("\n**Active Safety Guardrails**:")
            for g in val_res["guardrails_triggered"]:
                out_lines.append(f"- 🛡️ {g}")

        return {"content": [{"type": "text", "text": "\n".join(out_lines)}]}

    elif name == "schemap_get_glossary":
        term = arguments.get("term", "").strip()
        if term:
            # Search specific term
            matched = {k: v for k, v in schema_model.glossary.items() if term.lower() in k.lower()}
            if matched:
                lines = [f"### Business Term: `{term}`", ""]
                for k, v in matched.items():
                    lines.append(f"- **`{k}`**: {v}")
                return {"content": [{"type": "text", "text": "\n".join(lines)}]}
            else:
                return {"content": [{"type": "text", "text": f"No definition found for business term '{term}'."}]}
        else:
            lines = ["### Business Glossary & Domain Semantics", ""]
            if schema_model.glossary:
                for k, v in schema_model.glossary.items():
                    lines.append(f"- **`{k}`**: {v}")
            else:
                lines.append("_No glossary terms defined._")

            if schema_model.global_guardrails:
                lines.append("\n**Global AI Policies**:")
                for r in schema_model.global_guardrails:
                    lines.append(f"- 🛡️ {r}")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    elif name == "schemap_check_blast_radius":
        target = arguments.get("target_table", "").strip()
        if not target:
            return {"isError": True, "content": [{"type": "text", "text": "Error: 'target_table' is required."}]}

        try:
            info = explain_table(schema_model, target)
            lines = [
                f"### Blast Radius Report for Table: `{info['table']}`",
                "",
                f"- **Centrality Score**: `{info['centrality_score']}` ({info['degree_connections']} total connections)",
                f"- **Columns Count**: `{info['columns_count']}` columns",
            ]
            if info.get("description"):
                lines.append(f"- **Description**: {info['description']}")

            if info.get("incoming_relationships"):
                lines.append("\n**Dependent Tables (Incoming Foreign Keys)**:")
                for inc in info["incoming_relationships"]:
                    lines.append(f"- ⚠️ `{inc['from_table']}.{inc['from_column']}` references this table")

            if info.get("outgoing_relationships"):
                lines.append("\n**Upstream Dependencies (Outgoing Foreign Keys)**:")
                for outg in info["outgoing_relationships"]:
                    lines.append(f"- 🔗 References `{outg['ref_table']}.{outg['ref_column']}` via `{outg['column']}`")

            return {"content": [{"type": "text", "text": "\n".join(lines)}]}
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": f"Error: {str(e)}"}]}

    elif name == "schemap_ground":
        from .semantic import compile_semantic_graph
        from .ground import ground as run_ground

        question = arguments.get("question", "").strip()
        if not question:
            return {"isError": True, "content": [{"type": "text", "text": "Error: 'question' argument is required."}]}

        tenant_id = arguments.get("tenant_id")
        graph = compile_semantic_graph(schema_model)
        plan = run_ground(question, graph=graph, tenant_id=tenant_id)

        lines = [
            "### Schemap Deterministic Grounding Plan",
            f"- **Question**: \"{question}\"",
            f"- **Target Tables**: `{', '.join(plan.target_tables)}`",
        ]
        if tenant_id:
            lines.append(f"- **Tenant Scope**: `{tenant_id}` (Enforced)")

        if plan.join_path:
            join_prov = "DECLARED (Virtual Relations)" if any(s.is_virtual for s in plan.join_path.steps) else "INFERRED (Physical Foreign Keys)"
            lines.append(f"\n**Deterministic Join Path [{join_prov}]**:\n```sql\n{plan.join_path.sql_join_clause}\n```")

        if plan.mandatory_filters:
            lines.append("\n**Mandatory Invariants (MUST be included in WHERE clause)**:")
            for f in plan.mandatory_filters:
                tbl = f.split(".")[0]
                if "IS NULL" in f:
                    prov = graph.provenance_map.get(f"{tbl}:soft_delete", "INFERRED")
                else:
                    prov = graph.provenance_map.get(f"{tbl}:tenant_key", "INFERRED")
                prov_str = prov.value if hasattr(prov, "value") else str(prov)
                lines.append(f"- `* {f}` `[{prov_str}]`")

        if plan.measures:
            lines.append("\n**Resolved Measures**:")
            for m in plan.measures:
                expr = m.expression or f"SUM({m.table}.{m.column})"
                lines.append(f"- `{m.table}.{m.column}` `[{m.provenance.value}]`: `{expr}`")

        if plan.ambiguities:
            lines.append("\n**Semantic Ambiguities / Warnings**:")
            for a in plan.ambiguities:
                lines.append(f"- ⚠️ `[UNKNOWN]`: {a}")

        prov_dict = {}
        for tbl in plan.target_tables:
            if tbl in graph.soft_deletes:
                p = graph.provenance_map.get(f"{tbl}:soft_delete", "INFERRED")
                prov_dict[f"{tbl}:soft_delete"] = p.value if hasattr(p, "value") else str(p)
            if tbl in graph.tenant_keys:
                p = graph.provenance_map.get(f"{tbl}:tenant_key", "INFERRED")
                prov_dict[f"{tbl}:tenant_key"] = p.value if hasattr(p, "value") else str(p)

        structured_ground = {
            "question": question,
            "target_tables": plan.target_tables,
            "join_sql": plan.join_path.sql_join_clause if plan.join_path else None,
            "mandatory_filters": plan.mandatory_filters,
            "measures": [
                {
                    "table": m.table,
                    "column": m.column,
                    "expression": m.expression or f"SUM({m.table}.{m.column})",
                    "provenance": m.provenance.value if hasattr(m.provenance, "value") else str(m.provenance),
                }
                for m in plan.measures
            ],
            "provenance": prov_dict,
            "ambiguities": plan.ambiguities,
            "prompt_instructions": plan.prompt_instructions,
        }

        return {
            "content": [{"type": "text", "text": "\n".join(lines)}],
            "structuredContent": structured_ground,
        }

    elif name == "schemap_verify":
        from .semantic import compile_semantic_graph
        from .validator import verify_sql as run_verify_sql

        sql = arguments.get("sql", "").strip()
        if not sql:
            return {"isError": True, "content": [{"type": "text", "text": "Error: 'sql' argument is required."}]}

        tenant_id = arguments.get("tenant_id")
        patch = bool(arguments.get("patch", False))

        graph = compile_semantic_graph(schema_model)
        val_res = run_verify_sql(sql, graph=graph, tenant_id=tenant_id, auto_patch=patch)

        lines = ["### Schemap AST SQL Policy Verification", ""]
        if val_res.passed:
            lines.append("🟢 **STATUS: ALLOWED** — Query is policy-compliant and tenant-safe.")
        else:
            lines.append("🔴 **STATUS: REJECTED (Deny-by-Default)** — Policy violations detected:")
            for v in val_res.violations:
                lines.append(f"- ❌ {v}")

        if patch and val_res.patched_sql:
            lines.append("\n**Explicitly Auto-Patched Sanitized SQL (Execute this instead of the rejected original)**:")
            lines.append(f"```sql\n{val_res.patched_sql}\n```")
        elif not val_res.passed and not patch:
            lines.append("\n*(Note: Auto-patching is disabled by default. Pass `patch: true` or call `schemap_patch` to generate sanitized SQL.)*")

        structured_verify = {
            "status": "allow" if val_res.passed else "reject",
            "passed": val_res.passed,
            "violations": val_res.violations,
            "patched_sql": val_res.patched_sql if patch else None,
            "patch_requested": patch,
        }

        return {
            "content": [{"type": "text", "text": "\n".join(lines)}],
            "structuredContent": structured_verify,
        }

    elif name == "schemap_patch":
        from .semantic import compile_semantic_graph
        from .validator import verify_sql as run_verify_sql

        sql = arguments.get("sql", "").strip()
        if not sql:
            return {"isError": True, "content": [{"type": "text", "text": "Error: 'sql' argument is required."}]}

        tenant_id = arguments.get("tenant_id")
        graph = compile_semantic_graph(schema_model)
        val_res = run_verify_sql(sql, graph=graph, tenant_id=tenant_id, auto_patch=True)

        # Re-validate the patched SQL to ensure no remaining violations exist
        reval_passed = False
        final_violations = list(val_res.violations)
        if val_res.patched_sql:
            reval = run_verify_sql(val_res.patched_sql, graph=graph, tenant_id=tenant_id, auto_patch=False, allow_mutations=False)
            reval_passed = reval.passed
            final_violations = list(reval.violations)

        is_safe = val_res.passed or reval_passed

        lines = ["### Schemap AST SQL Patch Result", ""]
        if is_safe and val_res.patched_sql:
            lines.append("🔧 **Sanitized SQL with injected tenant & soft-delete filters**:")
            lines.append(f"```sql\n{val_res.patched_sql}\n```")
        elif is_safe and val_res.passed:
            lines.append("🟢 **No Patch Needed** — Query is already policy-compliant.")
            lines.append(f"```sql\n{sql}\n```")
        elif val_res.patched_sql and not reval_passed:
            lines.append("🔴 **Incomplete Patch — Remaining Hazards Detected**:")
            lines.append("The query was patched for tenant/soft-delete, but still contains unresolvable safety violations:")
            lines.append(f"```sql\n{val_res.patched_sql}\n```")
            for v in final_violations:
                lines.append(f"- ❌ {v}")
        else:
            lines.append("🔴 **Unpatchable Security Hazard** — The query contains violations that cannot be safely auto-patched (e.g. destructive mutation):")
            for v in val_res.violations:
                lines.append(f"- ❌ {v}")

        structured_patch = {
            "status": "allow" if is_safe else "reject",
            "passed": is_safe,
            "violations": final_violations,
            "original_sql": sql,
            "patched_sql": val_res.patched_sql if is_safe else None,
            "patch_applied": bool(val_res.patched_sql) and is_safe,
        }

        return {
            "content": [{"type": "text", "text": "\n".join(lines)}],
            "structuredContent": structured_patch,
        }

    else:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Unknown MCP tool '{name}'."}]
        }


def dispatch_mcp_request(req: Dict[str, Any], schema_model: DatabaseSchemaModel) -> Dict[str, Any] | None:
    """
    Handles a single JSON-RPC 2.0 MCP request payload.
    """
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    # Notification / no response required
    if method == "notifications/initialized":
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "schemap-mcp",
                    "version": __version__
                }
            }
        }

    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": MCP_TOOLS
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        res = execute_tool(tool_name, arguments, schema_model)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": res
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not found."
            }
        }


def generate_mcp_config_snippet(platform: str = "cursor") -> str:
    """
    Generates ready-to-copy JSON configuration for Cursor or Claude Desktop.
    """
    cursor_snippet = {
        "mcpServers": {
            "schemap": {
                "command": "uvx",
                "args": ["schemap-tool", "mcp"],
                "env": {
                    "DATABASE_URL": "postgresql://user:password@localhost:5432/dbname"
                }
            }
        }
    }
    claude_desktop_snippet = {
        "mcpServers": {
            "schemap": {
                "command": "uvx",
                "args": ["schemap-tool", "mcp", "--config", "./schemap.yaml"],
                "env": {
                    "DATABASE_URL": "postgresql://user:password@localhost:5432/dbname"
                }
            }
        }
    }

    if platform == "claude":
        return json.dumps(claude_desktop_snippet, indent=2)
    return json.dumps(cursor_snippet, indent=2)


def run_mcp_server(schema_model: DatabaseSchemaModel):
    """
    Runs the stdio JSON-RPC MCP server loop.
    """
    # Ensure stdout is in unbuffered or line-buffered mode
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
        except Exception:
            pass

    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
        try:
            req = json.loads(line_str)
            resp = dispatch_mcp_request(req, schema_model)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error or execution failure: {str(e)}"
                }
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()
