from __future__ import annotations

from typing import Any

from recap_scribe.storage import JsonGuildStorage
from recap_scribe.utils import dtp_for_hours, split_hours


class RecapService:
    def __init__(self, storage: JsonGuildStorage, rules: dict[str, Any]) -> None:
        self.storage = storage
        self.rules = rules

    def create_draft(
        self,
        guild_id: int,
        user_id: int,
        session_name: str,
        total_hours: float,
        game_version: str,
        game_format: str,
        application_format: str,
        event: str | None,
    ) -> dict:
        parts_list = split_hours(total_hours)
        parts = {str(i + 1): h for i, h in enumerate(parts_list)}
        draft = {
            "id": self.storage.generate_draft_id(),
            "created_by_user_id": str(user_id),
            "session_name": session_name,
            "total_hours": total_hours,
            "game_version": game_version,
            "game_format": game_format,
            "application_format": application_format,
            "event": event or "",
            "parts": parts,
            "roster": {},
            "per_part_rewards": {},
            "dm_reward_by_part": {},
            "narrative_by_part": {},
            "current_part_by_user_id": {str(user_id): 1},
        }
        self.storage.save_draft(guild_id, draft)
        self.storage.set_active_draft(guild_id, user_id, draft["id"])
        return draft

    def get_active_or_none(self, guild_id: int, user_id: int) -> dict | None:
        return self.storage.get_active_draft(guild_id, user_id)

    def set_current_part(self, draft: dict, user_id: int, part_number: int) -> None:
        draft["current_part_by_user_id"][str(user_id)] = part_number

    def current_part(self, draft: dict, user_id: int) -> int:
        return int(draft["current_part_by_user_id"].get(str(user_id), 1))

    def upsert_player(
        self,
        draft: dict,
        user_id: int,
        discord_name: str,
        character_name: str,
        level: int,
        part: int,
        gp: float | None,
        loot: str | None,
        used: str | None,
        incentives: str | None,
        notes: str | None,
    ) -> None:
        uid = str(user_id)
        draft["roster"][uid] = {
            "discord_name": discord_name,
            "character_name": character_name,
            "level": level,
        }
        if any(v is not None for v in [gp, loot, used, incentives, notes]):
            rewards = draft["per_part_rewards"].setdefault(str(part), {})
            rewards[uid] = {
                "gp": gp if gp is not None else 0,
                "loot": loot or "",
                "used": used or "",
                "incentives": incentives or "",
                "notes": notes or "",
            }

    def remove_player(self, draft: dict, user_id: int) -> None:
        uid = str(user_id)
        draft["roster"].pop(uid, None)
        for part in draft["per_part_rewards"].values():
            part.pop(uid, None)

    def update_player_rewards(self, draft: dict, user_id: int, part: int, payload: dict) -> None:
        rewards = draft["per_part_rewards"].setdefault(str(part), {})
        rewards[str(user_id)] = payload

    def update_dm_reward(self, draft: dict, part: int, payload: dict, apply_all: bool) -> None:
        if apply_all:
            for pn in draft["parts"].keys():
                draft["dm_reward_by_part"][pn] = payload
        else:
            draft["dm_reward_by_part"][str(part)] = payload

    def update_narrative(self, draft: dict, part: int, story_note: str, session_summary: str) -> None:
        draft["narrative_by_part"][str(part)] = {
            "story_note": story_note,
            "session_summary": session_summary,
        }

    def xp_for(self, level: int, hours: float) -> int:
        xp_hour = int(self.rules["xp_per_hour"][str(level)])
        return int(xp_hour * hours)

    def dtp_for(self, hours: float) -> int:
        return dtp_for_hours(hours)

    def max_gp_hint(self, level: int) -> float:
        return float(self.rules["max_gp_by_level"].get(str(level), 0))

    def suggest_dm_gp(self, level: int, hours: float) -> float:
        per_hour = float(self.rules["dm_gp_suggestion_per_hour_by_level"].get(str(level), 0))
        return round(per_hour * hours, 2)
