"""SQLite database for storing test run state.

Slimmed down in v3.0 — only the runs table remains.
All other data (users, environments, settings, audit log)
is managed by the Next.js application.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager

from api.models import RunStatus


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
