"""SQLite database for storing test run history."""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from api.models import RunStatus, TestStatus


DB_PATH = Path(__file__).parent.parent / "api_runs.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
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
    conn.close()


def create_run(module: str, sub_module: str = None) -> str:
    """Create a new run record, return the run ID."""
    run_id = str(uuid.uuid4())[:8]
    conn = get_connection()
    conn.execute(
        "INSERT INTO runs (id, module, sub_module, status) VALUES (?, ?, ?, ?)",
        (run_id, module, sub_module, RunStatus.PENDING.value)
    )
    conn.commit()
    conn.close()
    return run_id


def update_run_started(run_id: str):
    conn = get_connection()
    conn.execute(
        "UPDATE runs SET status = ?, started_at = ? WHERE id = ?",
        (RunStatus.RUNNING.value, datetime.now(timezone.utc).isoformat(), run_id)
    )
    conn.commit()
    conn.close()


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
    conn = get_connection()
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
    conn.close()


def get_run(run_id: str) -> dict:
    conn = get_connection()
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["results"] = json.loads(d["results"]) if d["results"] else []
    return d


def list_runs(limit: int = 50) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, module, sub_module, status, total_tests, passed, failed, started_at, duration FROM runs ORDER BY started_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_failed_tests(run_id: str) -> list[str]:
    """Get names of failed tests from a run (for rerun)."""
    data = get_run(run_id)
    if not data or not data["results"]:
        return []
    return [r["name"] for r in data["results"] if r["status"] == "failed"]