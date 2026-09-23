# Schemap 10-Minute Stranger Test Kit

> **Test whether AI coding agents make semantic errors on your relational database — and how deterministic grounding fixes them.**

---

## ⚡ 60-Second Setup

No cloning or repository build needed. Just create the local SQLite sample database:

```bash
# Initialize saas.db with schema and seed data
python -c "
import sqlite3
con = sqlite3.connect('saas.db')
con.executescript(open('schema.sql').read())
con.executescript(open('seed.sql').read())
con.close()
print('saas.db created successfully!')
"
```

---

## 🧪 The 5-Task Experiment

Open [`prompts.md`](prompts.md) and run each of the 5 tasks in your coding agent (Cursor, Claude Code, Windsurf, ChatGPT, etc.).

### Phase A: Without Schemap (The Baseline)
1. Paste the `schema.sql` into your agent.
2. Ask it each question in [`prompts.md`](prompts.md).
3. **Observe the failures:**
   - **Task 1 (Units):** Does it report $399,800.00 instead of $3,998.00?
   - **Task 2 (Zombies):** Does it include soft-deleted `zombie@acme.com`?
   - **Task 3 (Multi-Lifecycle):** Does it count the 100 soft-deleted usage events?
   - **Task 4 (Multi-Hop Join):** Does it connect `invoices` directly to `plans` without `subscriptions`?
   - **Task 5 (Safety):** Does it attempt to run a destructive `DELETE`?

---

### Phase B: With Schemap Grounding & Verification
Run Schemap via `uvx` (zero install):

```bash
# 1. Ground Task 1 (Revenue)
uvx schemap-tool@4.0.1 ground "What was Acme Corp's total paid revenue?" --db "sqlite:///saas.db" --tenant-id 1

# 2. Ground Task 4 (Multi-Hop Join)
uvx schemap-tool@4.0.1 ground "List every invoice ID and its plan name" --db "sqlite:///saas.db" --tenant-id 1

# 3. Verify Safe SQL
uvx schemap-tool@4.0.1 verify "SELECT SUM(amount_cents)/100.0 FROM invoices WHERE org_id = 1 AND status = 'paid'" --db "sqlite:///saas.db" --tenant-id 1

# 4. Verify Unsafe Operation (Interception)
uvx schemap-tool@4.0.1 verify "DELETE FROM users WHERE status = 'inactive'" --db "sqlite:///saas.db"
```

---

## 🤖 Optional: Live MCP Integration (Cursor / Claude Code)

Add Schemap as an MCP server in your `claude_desktop_config.json` or `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "schemap": {
      "command": "uvx",
      "args": ["schemap-tool@4.0.1", "mcp"],
      "env": {
        "DATABASE_URL": "sqlite:///absolute/path/to/saas.db"
      }
    }
  }
}
```

Your agent will now automatically call `schemap_ground` before writing SQL and `schemap_verify` before executing.

---

## 💬 2-Minute Feedback

If you ran this experiment, we'd love your candid answers:

1. **What did you expect Schemap to do that it didn't?**
2. **What would make you install this on your actual production project?**
3. **Did your AI coding agent make any errors that surprised you?**

Drop your feedback directly in [GitHub Discussions](https://github.com/alansyahmi/Schemap/discussions) or as an [Issue](https://github.com/alansyahmi/Schemap/issues).
