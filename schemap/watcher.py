"""
Schemap Automated Schema Watcher & Continuous Sync Daemon.

Continuously monitors database migrations, DDL files, semantics.yaml, and live databases,
keeping all AI agent context files (CLAUDE.md, AGENTS.md, Cursor rules) perfectly synchronized
and dispatching webhook notifications on breaking schema mutations.
"""

import time
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from .config import load_config, SchemapConfig
from .models import DatabaseSchemaModel
from .fingerprint import calculate_schema_fingerprint
from .diff import calculate_detailed_diff
from .context import generate_database_context, sanitize_schema_for_llm
from .agents import write_agent_files
from .linter import calculate_score



COMMON_MIGRATION_PATTERNS = [
    "schemap.yaml",
    "schemap.yml",
    ".schemap/semantics.yaml",
    ".schemap/semantics.yml",
    "semantics.yaml",
    "prisma/schema.prisma",
    "prisma/migrations",
    "alembic/versions",
    "db/migrate",
    "db/schema.rb",
    "migrations",
    "sql",
]


def dispatch_webhook(webhook_url: str, event_type: str, payload: Dict[str, Any], timeout: float = 5.0) -> bool:
    """
    Dispatches a structured webhook notification to Slack, Discord, or generic HTTP endpoints.
    """
    if not webhook_url:
        return False

    try:
        is_slack = "hooks.slack.com" in webhook_url
        is_discord = "discord.com/api/webhooks" in webhook_url

        summary_msg = payload.get("message", f"Schemap Schema Event: {event_type}")

        if is_slack:
            body = {
                "text": f"🛡️ *[Schemap Alert]* {summary_msg}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"🛡️ *[Schemap Alert]* {summary_msg}"}
                    }
                ]
            }
        elif is_discord:
            body = {
                "content": f"🛡️ **[Schemap Alert]** {summary_msg}"
            }
        else:
            body = {
                "event": event_type,
                "timestamp": time.time(),
                "data": payload
            }

        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "Schemap-Watcher/3.1.2"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except Exception:
        # Avoid crashing daemon on webhook network errors
        return False


def discover_watch_paths(root_dir: Path, custom_paths: Optional[List[str]] = None) -> List[Path]:
    """
    Identifies existing migration directories, schema files, and config targets to monitor.
    """
    targets: List[Path] = []
    
    # Custom paths first
    if custom_paths:
        for cp in custom_paths:
            p = root_dir / cp if not Path(cp).is_absolute() else Path(cp)
            if p.exists():
                targets.append(p)

    # Standard discovery
    for pattern in COMMON_MIGRATION_PATTERNS:
        p = root_dir / pattern
        if p.exists() and p not in targets:
            targets.append(p)

    return targets


def get_latest_mtime(paths: List[Path]) -> float:
    """
    Returns the maximum modification timestamp across all watched files and directories.
    """
    latest = 0.0
    for p in paths:
        try:
            if p.is_file():
                latest = max(latest, p.stat().st_mtime)
            elif p.is_dir():
                for sub in p.rglob("*"):
                    if sub.is_file() and not any(part.startswith(".") for part in sub.parts):
                        latest = max(latest, sub.stat().st_mtime)
        except (OSError, PermissionError):
            continue
    return latest


class SchemaWatcher:
    """
    Continuous schema monitor and real-time AI agent synchronization daemon.
    """
    def __init__(
        self,
        config_path: str = "schemap.yaml",
        profile: Optional[str] = None,
        custom_watch_paths: Optional[List[str]] = None,
        poll_db_interval: int = 0,
        webhook_url: Optional[str] = None,
        process_schema_fn: Optional[Callable] = None,
        logger: Optional[Callable[[str], None]] = None
    ):
        self.config_path = config_path
        self.profile = profile
        self.custom_watch_paths = custom_watch_paths or []
        self.poll_db_interval = max(0, poll_db_interval)
        self.webhook_url = webhook_url
        self.process_schema_fn = process_schema_fn
        self.log = logger or (lambda msg: None)

        self.root_dir = Path(config_path).resolve().parent
        self.watched_paths = discover_watch_paths(self.root_dir, self.custom_watch_paths)
        
        self.last_mtime = get_latest_mtime(self.watched_paths)
        self.last_db_poll = 0.0
        self.last_fingerprint: Optional[str] = None
        self.last_schema: Optional[DatabaseSchemaModel] = None

    def sync_once(self) -> Dict[str, Any]:
        """
        Executes a single synchronization cycle: parses schema, updates agent files, and detects breaking changes.
        """
        if self.process_schema_fn:
            cfg = load_config(self.config_path, profile=self.profile)
            schema_model, _, unresolved = self.process_schema_fn(cfg, enrich=False, quiet=True)
        else:
            from .cli import _process_schema
            cfg = load_config(self.config_path, profile=self.profile)
            schema_model, _, unresolved = _process_schema(cfg, enrich=False, quiet=True, required_feature="watch")


        current_fingerprint = calculate_schema_fingerprint(schema_model)
        has_changed = (self.last_fingerprint is not None and current_fingerprint != self.last_fingerprint)
        is_first_run = (self.last_fingerprint is None)

        breaking_changes = []
        if has_changed and self.last_schema:
            _, diff = calculate_detailed_diff(self.last_schema, schema_model)
            breaking_changes = diff.get("breaking_changes", [])


        # Write/Update context and agent files
        context_md = generate_database_context(schema_model)
        (self.root_dir / "schemap_database_context.md").write_text(context_md, encoding="utf-8")
        write_agent_files(schema_model, target_dir=str(self.root_dir), targets=["codex", "claude", "cursor"])

        ai_score, _ = calculate_score(schema_model, unresolved or [])


        # Dispatch webhook on changes
        if has_changed and self.webhook_url:
            event_type = "schema.breaking_change" if breaking_changes else "schema.updated"
            msg = f"Schema updated for {len(schema_model.tables)} tables (AI Readiness Score: {ai_score}/100)."
            if breaking_changes:
                msg = f"⚠️ *Breaking Schema Mutation Detected!* {len(breaking_changes)} breaking changes found:\n" + "\n".join(f"- {b}" for b in breaking_changes)

            dispatch_webhook(self.webhook_url, event_type, {
                "message": msg,
                "tables_count": len(schema_model.tables),
                "ai_readiness_score": ai_score,
                "breaking_changes": breaking_changes,
                "fingerprint": current_fingerprint
            })

        self.last_fingerprint = current_fingerprint
        self.last_schema = schema_model

        return {
            "fingerprint": current_fingerprint,
            "has_changed": has_changed or is_first_run,
            "is_first_run": is_first_run,
            "tables_count": len(schema_model.tables),
            "ai_readiness_score": ai_score,
            "breaking_changes": breaking_changes
        }

    def start(self, max_iterations: Optional[int] = None, poll_interval_sec: float = 1.0):
        """
        Runs the file watcher and continuous synchronization loop.
        """
        self.log(f"🔍 Schemap Watcher active. Monitoring {len(self.watched_paths)} target paths...")
        for wp in self.watched_paths:
            self.log(f"   - {wp}")

        # Initial baseline sync
        self.sync_once()

        iterations = 0
        try:
            while True:
                if max_iterations and iterations >= max_iterations:
                    break

                time.sleep(poll_interval_sec)
                iterations += 1

                now = time.time()
                current_mtime = get_latest_mtime(self.watched_paths)

                should_sync = False
                if current_mtime > self.last_mtime:
                    self.log("⚡ Change detected in schema/migration files. Synchronizing AI agent context...")
                    self.last_mtime = current_mtime
                    should_sync = True

                elif self.poll_db_interval > 0 and (now - self.last_db_poll) >= self.poll_db_interval:
                    self.last_db_poll = now
                    should_sync = True

                if should_sync:
                    result = self.sync_once()
                    if result["breaking_changes"]:
                        self.log(f"⚠️ [BREAKING MUTATION] Detected {len(result['breaking_changes'])} breaking changes.")
                    else:
                        self.log(f"✅ AI context synchronized (Score: {result['ai_readiness_score']}/100).")

        except KeyboardInterrupt:
            self.log("\n🛑 Schemap Watcher stopped.")
