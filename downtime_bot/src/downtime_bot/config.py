from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    discord_token: str
    discord_guild_id: int | None
    staff_log_channel_id: int | None
    downtime_ledger_channel_id: int | None
    downtime_db_path: Path
    allowed_content_path: Path
    sync_mode: str


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def load_config() -> Config:
    return Config(
        discord_token=os.getenv("DISCORD_TOKEN", ""),
        discord_guild_id=_to_int(os.getenv("DISCORD_GUILD_ID")),
        staff_log_channel_id=_to_int(os.getenv("STAFF_LOG_CHANNEL_ID")),
        downtime_ledger_channel_id=_to_int(os.getenv("DOWNTIME_LEDGER_CHANNEL_ID")),
        downtime_db_path=Path(os.getenv("DOWNTIME_DB_PATH", "downtime_bot/data/downtime.sqlite")),
        allowed_content_path=Path(os.getenv("ALLOWED_CONTENT_PATH", "data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json")),
        sync_mode=os.getenv("SYNC_MODE", "guild").strip().lower() or "guild",
    )
