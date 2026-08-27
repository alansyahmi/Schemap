import pytest
import sqlite3
import time
from pathlib import Path
from click.testing import CliRunner

from schemap.models import DatabaseSchemaModel, TableModel, ColumnModel
from schemap.watcher import (
    discover_watch_paths, get_latest_mtime, SchemaWatcher, dispatch_webhook
)
from schemap.cli import cli


def test_discover_watch_paths(tmp_path):
    (tmp_path / "schemap.yaml").write_text("database:\n  connection_url: sqlite:///:memory:")
    prisma_dir = tmp_path / "prisma" / "migrations"
    prisma_dir.mkdir(parents=True)
    (prisma_dir / "migration.sql").write_text("CREATE TABLE test (id INT);")

    paths = discover_watch_paths(tmp_path)
    path_names = [p.name for p in paths]
    assert "schemap.yaml" in path_names
    assert "migrations" in path_names


def test_get_latest_mtime(tmp_path):
    f1 = tmp_path / "f1.sql"
    f1.write_text("SELECT 1;")
    mtime1 = f1.stat().st_mtime

    latest = get_latest_mtime([f1])
    assert latest >= mtime1


def test_schema_watcher_sync_once(tmp_path):
    from schemap.license import _write_cache
    _write_cache("TEST-TEAM-KEY", plan_tier="team")

    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, price INTEGER);")
    conn.commit()
    conn.close()

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text(f"""
database:
  connection_url: "sqlite:///{db_file.as_posix()}"
license_key: "TEST-TEAM-KEY"
targets:
  - claude
  - codex
  - cursor
""")

    logs = []
    watcher = SchemaWatcher(
        config_path=str(cfg_file),
        logger=lambda m: logs.append(m)
    )

    res = watcher.sync_once()
    assert res["is_first_run"] is True
    assert res["tables_count"] == 1
    assert res["fingerprint"] is not None

    # Check generated files
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / "schemap_database_context.md").exists()

    # Mutation: add table
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, total INTEGER);")
    conn.commit()
    conn.close()

    res2 = watcher.sync_once()
    assert res2["is_first_run"] is False
    assert res2["has_changed"] is True
    assert res2["tables_count"] == 2


def test_schema_watcher_start_bounded_loop(tmp_path):
    from schemap.license import _write_cache
    _write_cache("TEST-TEAM-KEY", plan_tier="team")

    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE items (id INTEGER PRIMARY KEY);")
    conn.commit()
    conn.close()

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text(f"""
database:
  connection_url: "sqlite:///{db_file.as_posix()}"
license_key: "TEST-TEAM-KEY"
""")

    logs = []
    watcher = SchemaWatcher(
        config_path=str(cfg_file),
        logger=lambda m: logs.append(m)
    )
    watcher.start(max_iterations=1, poll_interval_sec=0.01)
    assert any("Schemap Watcher active" in log for log in logs)


def test_cli_watch_once(tmp_path):
    from schemap.license import _write_cache
    _write_cache("TEST-TEAM-KEY", plan_tier="team")

    runner = CliRunner()
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE logs (id INTEGER PRIMARY KEY, message TEXT);")
    conn.commit()
    conn.close()

    cfg_file = tmp_path / "schemap.yaml"
    cfg_file.write_text(f"""
database:
  connection_url: "sqlite:///{db_file.as_posix()}"
license_key: "TEST-TEAM-KEY"
""")

    res = runner.invoke(cli, ["watch", "--config", str(cfg_file), "--once"])
    assert res.exit_code == 0
    assert "Synchronized AI agent context files" in res.output



def test_dispatch_webhook_safety():
    # Verify non-blocking graceful failure when given dummy URL
    res = dispatch_webhook("http://127.0.0.1:9999/dummy-endpoint", "schema.updated", {"message": "test"}, timeout=0.1)
    assert res is False

    # Empty URL returns False immediately
    assert dispatch_webhook("", "schema.updated", {}) is False
