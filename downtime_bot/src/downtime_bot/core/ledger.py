from __future__ import annotations

import json
import sqlite3
from typing import Any


class LedgerService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def append_transaction(
        self,
        *,
        actor_discord_id: str,
        character_id: int,
        tx_type: str,
        amount: int,
        reason: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        metadata_json = json.dumps(metadata or {})
        cur = self.conn.execute(
            """
            INSERT INTO ledger_transactions (actor_discord_id, character_id, type, amount, reason, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (actor_discord_id, character_id, tx_type, amount, reason, metadata_json),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def get_balance(self, character_id: int) -> int:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS balance FROM ledger_transactions WHERE character_id = ?",
            (character_id,),
        ).fetchone()
        return int(row["balance"])

    def list_transactions(self, character_id: int, limit: int = 10):
        return self.conn.execute(
            """
            SELECT * FROM ledger_transactions
            WHERE character_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (character_id, limit),
        ).fetchall()
