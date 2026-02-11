from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Protocol


class DraftStorage(Protocol):
    def list_user_drafts(self, guild_id: int, user_id: int) -> list[dict]: ...

    def get_active_draft(self, guild_id: int, user_id: int) -> dict | None: ...

    def get_draft(self, guild_id: int, draft_id: str) -> dict | None: ...

    def save_draft(self, guild_id: int, draft: dict) -> None: ...

    def delete_draft(self, guild_id: int, draft_id: str) -> bool: ...

    def set_active_draft(self, guild_id: int, user_id: int, draft_id: str | None) -> None: ...


class JsonGuildStorage:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, guild_id: int) -> Path:
        return self.base_dir / f"guild_{guild_id}.json"

    def _load(self, guild_id: int) -> dict:
        path = self._path(guild_id)
        if not path.exists():
            return {"drafts": {}, "active_draft_by_user": {}}
        return json.loads(path.read_text(encoding="utf-8"))

    def _save(self, guild_id: int, payload: dict) -> None:
        self._path(guild_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def generate_draft_id(self) -> str:
        return uuid.uuid4().hex[:8]

    def list_user_drafts(self, guild_id: int, user_id: int) -> list[dict]:
        payload = self._load(guild_id)
        drafts = payload["drafts"].values()
        return [d for d in drafts if d["created_by_user_id"] == str(user_id)]

    def get_active_draft(self, guild_id: int, user_id: int) -> dict | None:
        payload = self._load(guild_id)
        draft_id = payload["active_draft_by_user"].get(str(user_id))
        if not draft_id:
            return None
        return payload["drafts"].get(draft_id)

    def get_draft(self, guild_id: int, draft_id: str) -> dict | None:
        return self._load(guild_id)["drafts"].get(draft_id)

    def save_draft(self, guild_id: int, draft: dict) -> None:
        payload = self._load(guild_id)
        payload["drafts"][draft["id"]] = draft
        self._save(guild_id, payload)

    def delete_draft(self, guild_id: int, draft_id: str) -> bool:
        payload = self._load(guild_id)
        if draft_id not in payload["drafts"]:
            return False
        del payload["drafts"][draft_id]
        for uid, aid in list(payload["active_draft_by_user"].items()):
            if aid == draft_id:
                payload["active_draft_by_user"][uid] = None
        self._save(guild_id, payload)
        return True

    def set_active_draft(self, guild_id: int, user_id: int, draft_id: str | None) -> None:
        payload = self._load(guild_id)
        payload["active_draft_by_user"][str(user_id)] = draft_id
        self._save(guild_id, payload)
