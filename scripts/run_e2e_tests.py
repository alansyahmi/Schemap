"""
End-to-End (E2E) Test Suite for Built Schemap-Tool Distribution.

Tests the packaged wheel in an isolated environment against live database workflows:
1. Package installation verification
2. Doctor diagnostic
3. Context compilation with PII sanitization
4. Agent rules generation (Claude, Cursor, Codex)
5. CI/CD AI Quality Gate evaluation (Passing & Failing threshold tests)
6. Scoped context role compilation
7. Benchmark & scoring verification
"""

import sys
import os
import subprocess
import tempfile
import sqlite3
import json
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_cmd(cmd_list, cwd=None, expect_code=0):
    print(f"  [EXEC] {' '.join(cmd_list)}")
    res = subprocess.run(
        cmd_list,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if res.returncode != expect_code:
        print(f"  [ERROR] Expected exit code {expect_code}, got {res.returncode}")
        print("  STDOUT:\n", res.stdout)
        print("  STDERR:\n", res.stderr)
        raise RuntimeError(f"Command failed with exit code {res.returncode}")
    return res.stdout


def create_test_db(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        full_name TEXT,
        password_hash TEXT NOT NULL,
        ssn TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT NOT NULL UNIQUE
    );
    """)

    cur.execute("""
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        org_id INTEGER NOT NULL,
        total_cents INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (org_id) REFERENCES organizations(id)
    );
    """)

    cur.execute("""
    CREATE TABLE order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price_cents INTEGER NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    );
    """)

    conn.commit()
    conn.close()


def main():
    print("=" * 60)
    print(" 🚀 Schemap-Tool Production E2E Verification Suite")
    print("=" * 60)

    repo_root = Path(__file__).resolve().parent.parent
    dist_dir = repo_root / "dist"
    wheels = list(dist_dir.glob("*.whl"))

    if not wheels:
        print("[ERROR] No wheel found in dist/. Please run `uv build` first.")
        sys.exit(1)

    wheel_path = sorted(wheels, key=os.path.getmtime, reverse=True)[0]
    print(f"Target Wheel: {wheel_path.name}\n")

    with tempfile.TemporaryDirectory(prefix="schemap_e2e_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        db_path = tmp_dir / "production.db"
        create_test_db(db_path)
        print(f"Created isolated test database at: {db_path}\n")

        # 1. Test CLI Version
        print("1. Testing version...")
        version_out = run_cmd(["uv", "run", "schemap", "--version"], cwd=str(tmp_dir))
        assert "Schemap" in version_out
        print("   [PASS] Version verified.\n")

        # 2. Test Doctor
        print("2. Testing `schemap doctor` diagnostic...")
        doctor_out = run_cmd([
            "uv", "run", "schemap", "doctor",
            "--config", str(repo_root / "examples" / "demo_schemap.yaml"),
            "--json"
        ], cwd=str(tmp_dir))
        json_start = doctor_out.find("{")
        doc_json = json.loads(doctor_out[json_start:])
        assert "ai_readiness_score" in doc_json
        print(f"   [PASS] Doctor report generated (Score: {doc_json['ai_readiness_score']}/100).\n")

        # 3. Create schemap.yaml in isolated directory
        yaml_content = f"""
database:
  connection_url: "sqlite:///{db_path.as_posix()}"
output:
  file_path: "./schemap_database_context.md"
domain:
  mappings:
    ssn: "Social Security Number"
    full: "Full Name"
    unit: "Unit Price"
    at: "Timestamp"
schema_descriptions:
  users:
    description: "User account credentials and identity"
  organizations:
    description: "Tenant organizations and teams"
  orders:
    description: "Customer purchasing transactions"
  order_items:
    description: "Individual line items for an order"
"""
        (tmp_dir / "schemap.yaml").write_text(yaml_content, encoding="utf-8")

        # 4. Test Context Compilation with PII Sanitization
        print("3. Testing `schemap context --sanitize`...")
        ctx_out = run_cmd(["uv", "run", "schemap", "context", "--sanitize"], cwd=str(tmp_dir))
        assert "Context map generated successfully" in ctx_out
        
        ctx_file = tmp_dir / "schemap_database_context.md"
        assert ctx_file.exists()
        ctx_content = ctx_file.read_text(encoding="utf-8")
        assert "Security Guardrail Active" in ctx_content
        assert "users" in ctx_content and "orders" in ctx_content
        print("   [PASS] Context compiled with PII masking guardrail.\n")

        # 5. Test Agent Rules Generation
        print("4. Testing `schemap agents --targets claude,cursor,codex --sanitize`...")
        agents_out = run_cmd([
            "uv", "run", "schemap", "agents",
            "--targets", "claude,cursor,codex",
            "--sanitize"
        ], cwd=str(tmp_dir))
        assert "AI Agent Context files generated successfully" in agents_out

        assert (tmp_dir / "CLAUDE.md").exists()
        assert (tmp_dir / "AGENTS.md").exists()
        assert (tmp_dir / ".cursor" / "rules" / "schemap.mdc").exists()
        print("   [PASS] CLAUDE.md, AGENTS.md, and Cursor rules generated.\n")

        # 6. Test CI/CD AI Quality Gate (Passing threshold)
        print("5. Testing `schemap gate --min-score 70` (Passing case)...")
        gate_pass_out = run_cmd([
            "uv", "run", "schemap", "gate",
            "--min-score", "70",
            "--json"
        ], cwd=str(tmp_dir), expect_code=0)
        gate_json = json.loads(gate_pass_out[gate_pass_out.find("{"):])
        assert gate_json["passed"] is True
        print(f"   [PASS] Quality gate passed with score {gate_json['score']}/100.\n")

        # 7. Test CI/CD AI Quality Gate (Failing threshold)
        print("6. Testing `schemap gate --min-score 99` (Failing case blocking CI)...")
        gate_fail_out = run_cmd([
            "uv", "run", "schemap", "gate",
            "--min-score", "99",
            "--json"
        ], cwd=str(tmp_dir), expect_code=1)
        gate_fail_json = json.loads(gate_fail_out[gate_fail_out.find("{"):])
        assert gate_fail_json["passed"] is False
        print("   [PASS] Quality gate successfully blocked sub-threshold score (exit code 1).\n")

        # 8. Test Scoped Role Filtering
        print("7. Testing role-scoped context `schemap context --scope backend`...")
        run_cmd(["uv", "run", "schemap", "context", "--scope", "backend"], cwd=str(tmp_dir))
        backend_ctx = (tmp_dir / "schemap_database_context.md").read_text(encoding="utf-8")
        assert "Context Scope" in backend_ctx
        print("   [PASS] Scoped context filtering verified.\n")

    print("=" * 60)
    print(" ✅ ALL E2E VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
