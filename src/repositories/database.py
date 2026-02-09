"""SQLite database initialization and connection management."""
from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".personal_dashboard" / "dashboard.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS expenses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amount          INTEGER NOT NULL CHECK(amount >= 0),
    category        TEXT    NOT NULL,
    expense_date    TEXT    NOT NULL,  -- ISO 8601 date (YYYY-MM-DD)
    payment_method  TEXT    NOT NULL,
    recurrence      TEXT    NOT NULL DEFAULT 'none',
    notes           TEXT    NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);

CREATE TABLE IF NOT EXISTS incomes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amount      INTEGER NOT NULL CHECK(amount >= 0),
    income_date TEXT    NOT NULL,
    client      TEXT    NOT NULL,
    job_type    TEXT    NOT NULL,
    notes       TEXT    NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_incomes_date ON incomes(income_date);
CREATE INDEX IF NOT EXISTS idx_incomes_client ON incomes(client);

CREATE TABLE IF NOT EXISTS events (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT    NOT NULL,
    event_date        TEXT    NOT NULL,
    category          TEXT    NOT NULL,
    start_time        TEXT,           -- HH:MM or NULL
    end_time          TEXT,           -- HH:MM or NULL
    recurrence        TEXT    NOT NULL DEFAULT 'none',
    color             TEXT,           -- hex color override or NULL
    notes             TEXT    NOT NULL DEFAULT '',
    linked_income_id  INTEGER REFERENCES incomes(id) ON DELETE SET NULL,
    linked_expense_id INTEGER REFERENCES expenses(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def get_connection(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open (or create) the database and return a connection.

    Enables WAL mode and foreign keys for correctness and performance.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
