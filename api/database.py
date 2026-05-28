"""SQLite database for storing test run history."""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

from api.models import RunStatus, TestStatus


DB_PATH = Path(__file__).parent.parent / "api_runs.db"


@contextmanager
def get_connection():
    """Context manager for database connections. Ensures connections are always closed."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                module TEXT NOT NULL,
                sub_module TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                total_tests INTEGER DEFAULT 0,
                passed INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                skipped INTEGER DEFAULT 0,
                duration REAL,
                started_at TEXT,
                completed_at TEXT,
                results TEXT,
                report_path TEXT
            );

            CREATE TABLE IF NOT EXISTS environments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_url TEXT NOT NULL,
                browser TEXT DEFAULT 'Chrome',
                status TEXT DEFAULT 'active',
                last_used TEXT,
                color TEXT DEFAULT 'bg-green-500',
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS settings (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL UNIQUE,
                label TEXT NOT NULL,
                value TEXT,
                type TEXT DEFAULT 'text',
                description TEXT,
                category TEXT DEFAULT 'System',
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                user_name TEXT,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id TEXT,
                target_label TEXT,
                details TEXT,
                created_at TEXT
            );
        """)
        conn.commit()


def create_run(module: str, sub_module: str = None) -> str:
    """Create a new run record, return the run ID (full UUID to avoid collisions)."""
    run_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO runs (id, module, sub_module, status) VALUES (?, ?, ?, ?)",
            (run_id, module, sub_module, RunStatus.PENDING.value)
        )
        conn.commit()
    return run_id


def update_run_started(run_id: str):
    """Mark a run as started with the current timestamp."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE runs SET status = ?, started_at = ? WHERE id = ?",
            (RunStatus.RUNNING.value, datetime.now(timezone.utc).isoformat(), run_id)
        )
        conn.commit()


def update_run_completed(
    run_id: str,
    status: RunStatus,
    total: int,
    passed: int,
    failed: int,
    skipped: int,
    duration: float,
    results: list,
    report_path: str = None,
):
    """Update a run record with final results."""
    with get_connection() as conn:
        conn.execute(
            """UPDATE runs SET status = ?, total_tests = ?, passed = ?, failed = ?,
               skipped = ?, duration = ?, completed_at = ?, results = ?, report_path = ?
               WHERE id = ?""",
            (
                status.value, total, passed, failed, skipped, duration,
                datetime.now(timezone.utc).isoformat(),
                json.dumps([r.model_dump() for r in results]),
                report_path, run_id
            )
        )
        conn.commit()


def update_run_status(run_id: str, status: RunStatus):
    """Update only the status of a run (e.g. to STOPPED)."""
    with get_connection() as conn:
        completed_at = datetime.now(timezone.utc).isoformat() if status == RunStatus.STOPPED else None
        conn.execute(
            "UPDATE runs SET status = ?, completed_at = COALESCE(?, completed_at) WHERE id = ?",
            (status.value, completed_at, run_id)
        )
        conn.commit()


def get_run(run_id: str) -> dict | None:
    """Get a single run by ID. Returns None if not found."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["results"] = json.loads(d["results"]) if d["results"] else []
    return d


def list_runs(limit: int = 50, offset: int = 0) -> list[dict]:
    """List runs with pagination (most recent first)."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, module, sub_module, status, total_tests, passed, failed,
               started_at, duration FROM runs
               ORDER BY started_at DESC LIMIT ? OFFSET ?""",
            (limit, offset)
        ).fetchall()
    return [dict(r) for r in rows]


def get_failed_tests(run_id: str) -> list[str]:
    """Get names of failed tests from a run (for rerun)."""
    data = get_run(run_id)
    if not data or not data["results"]:
        return []
    return [r["name"] for r in data["results"] if r["status"] == "failed"]


def delete_run(run_id: str) -> bool:
    """Delete a run record. Returns True if deleted, False if not found."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        conn.commit()
        return cursor.rowcount > 0


# ================================================================
# ENVIRONMENTS CRUD
# ================================================================

def list_environments() -> list[dict]:
    """List all environments."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM environments ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def get_environment(env_id: str) -> dict | None:
    """Get a single environment by ID."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM environments WHERE id = ?", (env_id,)).fetchone()
    return dict(row) if row else None


def create_environment(name: str, base_url: str, browser: str = "Chrome",
                       status: str = "active", color: str = "bg-green-500") -> str:
    """Create a new environment. Returns the environment ID."""
    env_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO environments (id, name, base_url, browser, status, color, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (env_id, name, base_url, browser, status, color, now, now)
        )
        conn.commit()
    return env_id


def update_environment(env_id: str, **kwargs) -> bool:
    """Update an environment. Returns True if updated, False if not found."""
    allowed = {"name", "base_url", "browser", "status", "color", "last_used"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [env_id]
    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE environments SET {set_clause} WHERE id = ?", values
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_environment(env_id: str) -> bool:
    """Delete an environment. Returns True if deleted, False if not found."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM environments WHERE id = ?", (env_id,))
        conn.commit()
        return cursor.rowcount > 0


# ================================================================
# SETTINGS CRUD
# ================================================================

def list_settings() -> list[dict]:
    """List all settings."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM settings ORDER BY category, label").fetchall()
    return [dict(r) for r in rows]


def get_setting(key: str) -> dict | None:
    """Get a single setting by key."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM settings WHERE key = ?", (key,)).fetchone()
    return dict(row) if row else None


def upsert_setting(key: str, label: str, value: str = "", type: str = "text",
                   description: str = "", category: str = "System") -> str:
    """Insert or update a setting. Returns the setting ID."""
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM settings WHERE key = ?", (key,)).fetchone()
        if existing:
            setting_id = existing["id"]
            conn.execute(
                """UPDATE settings SET label = ?, value = ?, type = ?, description = ?,
                   category = ?, updated_at = ? WHERE key = ?""",
                (label, value, type, description, category, now, key)
            )
        else:
            setting_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO settings (id, key, label, value, type, description, category, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (setting_id, key, label, value, type, description, category, now, now)
            )
        conn.commit()
    return setting_id


def delete_setting(key: str) -> bool:
    """Delete a setting by key. Returns True if deleted, False if not found."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM settings WHERE key = ?", (key,))
        conn.commit()
        return cursor.rowcount > 0


def seed_default_settings():
    """Insert default settings if the settings table is empty."""
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM settings").fetchone()[0]
    if count > 0:
        return
    defaults = [
        ("selenium_grid_url", "Selenium Grid URL", "http://localhost:4444/wd/hub", "text", "URL of the Selenium Grid hub for remote WebDriver execution", "Execution"),
        ("cdp_target_url", "CDP Target URL", "http://localhost:9222", "text", "Chrome DevTools Protocol target for live browser screencast", "Execution"),
        ("default_timeout", "Default Test Timeout (sec)", "30", "number", "Maximum time to wait for a single test step before failing", "Execution"),
        ("max_retries", "Max Retries per Test", "2", "number", "Number of retry attempts for a failed test before marking as permanently failed", "Execution"),
        ("parallel_workers", "Parallel Workers", "3", "number", "Maximum number of tests that can run in parallel", "Execution"),
        ("slack_webhook", "Slack Webhook URL", "", "text", "Slack incoming webhook URL for run completion notifications", "Notifications"),
        ("teams_webhook", "MS Teams Webhook URL", "", "text", "Microsoft Teams incoming webhook for run notifications", "Notifications"),
        ("notify_on_failure", "Notify on Test Failure", "true", "boolean", "Send a notification when any test fails during a run", "Notifications"),
        ("notify_on_complete", "Notify on Run Complete", "true", "boolean", "Send a summary notification when a full run completes", "Notifications"),
        ("auto_screenshot_fail", "Auto-screenshot on Failure", "true", "boolean", "Automatically capture a screenshot when a test fails", "Execution"),
        ("log_level", "Log Level", "info", "select", "Console log verbosity level", "System"),
        ("session_timeout", "Session Timeout (hours)", "168", "number", "User session duration before automatic logout (default 168 = 7 days)", "System"),
    ]
    for key, label, value, stype, description, category in defaults:
        upsert_setting(key, label, value, stype, description, category)


# ================================================================
# AUDIT LOG CRUD
# ================================================================

def list_audit_log(limit: int = 100, offset: int = 0) -> list[dict]:
    """List audit log entries (most recent first)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
    return [dict(r) for r in rows]


def add_audit_entry(user_id: str, user_name: str, action: str,
                     target_type: str = None, target_id: str = None,
                     target_label: str = None, details: str = None) -> str:
    """Add an audit log entry. Returns the entry ID."""
    entry_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO audit_log (id, user_id, user_name, action, target_type, target_id, target_label, details, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (entry_id, user_id, user_name, action, target_type, target_id, target_label, details, now)
        )
        conn.commit()
    return entry_id
