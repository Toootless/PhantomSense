"""
SQLite persistence for PhantomSense hub.

Tables:
  activities    — every activity dict received from ESP32 units
  llm_reasoning — every completed LLM analysis result

All writes are fire-and-forget (async, runs in a thread pool).
"""

import sqlite3
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_db_path: Optional[Path] = None


# ── schema ──────────────────────────────────────────────────────────────────

_CREATE_ACTIVITIES = """
CREATE TABLE IF NOT EXISTS activities (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id        TEXT    NOT NULL,
    timestamp_wall TEXT    NOT NULL,
    timestamp_ms   INTEGER,
    activity_score INTEGER,
    rssi           INTEGER,
    snr            REAL,
    phase_velocity REAL,
    amplitude_mean REAL,
    noise_floor    REAL
);
CREATE INDEX IF NOT EXISTS idx_act_unit ON activities(unit_id);
CREATE INDEX IF NOT EXISTS idx_act_wall ON activities(timestamp_wall);
"""

_CREATE_LLM_REASONING = """
CREATE TABLE IF NOT EXISTS llm_reasoning (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id          TEXT    NOT NULL,
    timestamp        TEXT    NOT NULL,
    model            TEXT,
    reasoning        TEXT,
    confidence       INTEGER,
    activity_summary TEXT
);
CREATE INDEX IF NOT EXISTS idx_llm_unit ON llm_reasoning(unit_id);
CREATE INDEX IF NOT EXISTS idx_llm_ts   ON llm_reasoning(timestamp);
"""


# ── connection helper ────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    """Return a new per-call connection (thread-safe for run_in_executor)."""
    conn = sqlite3.connect(str(_db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # allow concurrent reads
    conn.execute("PRAGMA synchronous=NORMAL") # good balance of safety/speed
    return conn


# ── public API ───────────────────────────────────────────────────────────────

def init_db(db_path: Path) -> None:
    """Create tables if they don't exist. Called once at startup (sync)."""
    global _db_path
    _db_path = db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _get_conn() as conn:
        conn.executescript(_CREATE_ACTIVITIES)
        conn.executescript(_CREATE_LLM_REASONING)
    logger.info(f"Database ready: {db_path}")


def _sync_save_activity(unit_id: str, activity: dict) -> None:
    wall = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO activities
               (unit_id, timestamp_wall, timestamp_ms, activity_score,
                rssi, snr, phase_velocity, amplitude_mean, noise_floor)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                unit_id,
                wall,
                activity.get("timestamp_ms"),
                activity.get("activity_score"),
                activity.get("rssi"),
                activity.get("snr"),
                activity.get("phase_velocity"),
                activity.get("amplitude_mean"),
                activity.get("noise_floor"),
            ),
        )


async def save_activity(unit_id: str, activity: dict) -> None:
    """Async wrapper — write an activity row without blocking the event loop."""
    try:
        await asyncio.to_thread(_sync_save_activity, unit_id, activity)
    except Exception as e:
        logger.error(f"DB save_activity failed: {e}")


def _sync_save_reasoning(unit_id: str, result: dict) -> None:
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO llm_reasoning
               (unit_id, timestamp, model, reasoning, confidence, activity_summary)
               VALUES (?,?,?,?,?,?)""",
            (
                unit_id,
                result.get("timestamp", datetime.now(timezone.utc).isoformat()),
                result.get("model"),
                result.get("reasoning"),
                result.get("confidence"),
                result.get("activity_summary"),
            ),
        )


async def save_reasoning(unit_id: str, result: dict) -> None:
    """Async wrapper — write an LLM reasoning row without blocking the event loop."""
    try:
        await asyncio.to_thread(_sync_save_reasoning, unit_id, result)
    except Exception as e:
        logger.error(f"DB save_reasoning failed: {e}")


def _sync_get_activities(unit_id: str, limit: int) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM activities
               WHERE unit_id = ?
               ORDER BY timestamp_wall DESC
               LIMIT ?""",
            (unit_id, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]  # oldest-first for LLM


async def get_activities(unit_id: str, limit: int = 1000) -> list[dict]:
    """Return up to *limit* most-recent activities for a unit (oldest first)."""
    return await asyncio.to_thread(_sync_get_activities, unit_id, limit)


def _sync_get_reasoning_history(unit_id: str, limit: int) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM llm_reasoning
               WHERE unit_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (unit_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


async def get_reasoning_history(unit_id: str, limit: int = 50) -> list[dict]:
    """Return past LLM reasoning results for a unit (newest first)."""
    return await asyncio.to_thread(_sync_get_reasoning_history, unit_id, limit)


def _sync_load_last_reasoning_all() -> dict[str, dict]:
    """Return {unit_id: latest_reasoning_dict} — used to restore cache on startup."""
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT r.*
               FROM llm_reasoning r
               INNER JOIN (
                   SELECT unit_id, MAX(timestamp) AS max_ts
                   FROM llm_reasoning
                   GROUP BY unit_id
               ) latest ON r.unit_id = latest.unit_id AND r.timestamp = latest.max_ts"""
        ).fetchall()
    return {r["unit_id"]: dict(r) for r in rows}


async def load_last_reasoning_all() -> dict[str, dict]:
    """Restore the newest reasoning result per unit into the LLM cache on startup."""
    try:
        return await asyncio.to_thread(_sync_load_last_reasoning_all)
    except Exception as e:
        logger.error(f"DB load_last_reasoning_all failed: {e}")
        return {}


def _sync_get_all_unit_ids() -> list[str]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT unit_id FROM activities ORDER BY unit_id"
        ).fetchall()
    return [r["unit_id"] for r in rows]


async def get_all_unit_ids() -> list[str]:
    """Return every unit_id that has ever written activities."""
    return await asyncio.to_thread(_sync_get_all_unit_ids)
