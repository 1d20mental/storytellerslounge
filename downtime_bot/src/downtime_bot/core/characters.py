from __future__ import annotations

import sqlite3


class CharacterService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def register(self, owner_discord_id: str, name: str, level: int | None = None, tier: int | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO characters (owner_discord_id, name, level, tier) VALUES (?, ?, ?, ?)",
            (owner_discord_id, name, level, tier),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def select_active(self, owner_discord_id: str, name: str) -> int | None:
        row = self.conn.execute(
            "SELECT id FROM characters WHERE owner_discord_id = ? AND name = ?",
            (owner_discord_id, name),
        ).fetchone()
        if not row:
            return None
        character_id = int(row["id"])
        self.conn.execute("UPDATE characters SET is_active = 0 WHERE owner_discord_id = ?", (owner_discord_id,))
        self.conn.execute("UPDATE characters SET is_active = 1 WHERE id = ?", (character_id,))
        self.conn.commit()
        return character_id

    def get_active(self, owner_discord_id: str):
        return self.conn.execute(
            "SELECT * FROM characters WHERE owner_discord_id = ? AND is_active = 1",
            (owner_discord_id,),
        ).fetchone()

    def get_by_id(self, character_id: int):
        return self.conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()

    def get_by_name(self, name: str):
        return self.conn.execute("SELECT * FROM characters WHERE name = ?", (name,)).fetchone()
