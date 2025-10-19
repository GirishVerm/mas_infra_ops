import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

try:
    from .models import AgentRun
except ImportError:
    from models import AgentRun


# Use relative path for database, create in project root
DB_PATH = Path(__file__).parent / "agentops.db"


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_run_id INTEGER,
            workflow TEXT,
            agent TEXT,
            status TEXT,
            cost REAL,
            output TEXT,
            error TEXT,
            retries INTEGER
        )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS workflow_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow TEXT,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            finished_at DATETIME
        )"""
        )
        conn.commit()


def save_run(workflow_name: str, result: AgentRun, workflow_run_id: int | None = None) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO runs (workflow_run_id, workflow, agent, status, cost, output, error, retries) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                workflow_run_id,
                workflow_name,
                result.name,
                result.status,
                result.cost,
                result.output,
                result.error,
                result.retries,
            ),
        )
        conn.commit()


def list_runs(limit: int = 20) -> List[Tuple[int, str, str, str, float]]:
    """Return recent runs: (id, workflow, agent, status, cost)."""
    with _conn() as conn:
        cur = conn.execute(
            "SELECT id, workflow, agent, status, cost FROM runs ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return list(cur.fetchall())


def get_runs_for_workflow(workflow: str, limit: Optional[int] = None) -> List[Tuple[int, str, str, str, float, Optional[str]]]:
    """Return runs for a workflow: (id, workflow, agent, status, cost, output)."""
    with _conn() as conn:
        if limit is None:
            cur = conn.execute(
                "SELECT id, workflow, agent, status, cost, output FROM runs WHERE workflow = ? ORDER BY id DESC",
                (workflow,),
            )
        else:
            cur = conn.execute(
                "SELECT id, workflow, agent, status, cost, output FROM runs WHERE workflow = ? ORDER BY id DESC LIMIT ?",
                (workflow, limit),
            )
        return list(cur.fetchall())


def create_workflow_run(workflow: str) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO workflow_runs (workflow) VALUES (?)",
            (workflow,),
        )
        conn.commit()
        return int(cur.lastrowid)


def finalize_workflow_run(run_id: int) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE workflow_runs SET finished_at = CURRENT_TIMESTAMP WHERE id = ?",
            (run_id,),
        )
        conn.commit()


