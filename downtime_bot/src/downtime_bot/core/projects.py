from __future__ import annotations

import json
import sqlite3
from typing import Any


class ProjectService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def start_project(
        self,
        *,
        character_id: int,
        activity_key: str,
        dtp_required: int,
        gp_required: int | None,
        options: dict[str, Any] | None = None,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO downtime_projects (character_id, activity_key, status, dtp_required, gp_required, options_json)
            VALUES (?, ?, 'started', ?, ?, ?)
            """,
            (character_id, activity_key, dtp_required, gp_required, json.dumps(options or {})),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def commit_dtp(self, project_id: int, dtp_amount: int) -> None:
        self.conn.execute(
            """
            UPDATE downtime_projects
            SET dtp_committed = dtp_committed + ?,
                status = CASE WHEN status = 'started' THEN 'committed' ELSE status END
            WHERE id = ? AND status IN ('started', 'committed')
            """,
            (dtp_amount, project_id),
        )
        self.conn.commit()

    def resolve_project(self, project_id: int, result: dict[str, Any]) -> None:
        self.conn.execute(
            "UPDATE downtime_projects SET status = 'resolved', result_json = ? WHERE id = ?",
            (json.dumps(result), project_id),
        )
        self.conn.commit()

    def get_project(self, project_id: int):
        return self.conn.execute("SELECT * FROM downtime_projects WHERE id = ?", (project_id,)).fetchone()

    def list_open_projects(self, character_id: int):
        return self.conn.execute(
            "SELECT * FROM downtime_projects WHERE character_id = ? AND status IN ('started', 'committed') ORDER BY id DESC",
            (character_id,),
        ).fetchall()
