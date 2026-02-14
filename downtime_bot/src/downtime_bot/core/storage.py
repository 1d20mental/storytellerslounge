from __future__ import annotations

import sqlite3
from pathlib import Path


class Storage:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def migrate(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_discord_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    level INTEGER,
                    tier INTEGER,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner_discord_id, name)
                );

                CREATE TABLE IF NOT EXISTS ledger_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    actor_discord_id TEXT NOT NULL,
                    character_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(character_id) REFERENCES characters(id)
                );

                CREATE TABLE IF NOT EXISTS downtime_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER NOT NULL,
                    activity_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    dtp_required INTEGER NOT NULL,
                    dtp_committed INTEGER NOT NULL DEFAULT 0,
                    gp_required INTEGER,
                    gp_committed INTEGER NOT NULL DEFAULT 0,
                    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    deadline_at TEXT,
                    options_json TEXT NOT NULL DEFAULT '{}',
                    result_json TEXT,
                    FOREIGN KEY(character_id) REFERENCES characters(id)
                );
                """
            )
