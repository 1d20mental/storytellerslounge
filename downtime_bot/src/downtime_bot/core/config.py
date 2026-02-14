from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BotConfig:
    token: str
    guild_id: int
    database_path: Path
    allowed_content_path: Path
    staff_log_channel_id: int | None
    downtime_ledger_channel_id: int | None


    @staticmethod
    def from_env() -> "BotConfig":
        token = os.getenv("DISCORD_TOKEN", "")
        guild_id = int(os.getenv("DISCORD_GUILD_ID", "0"))
        database_path = Path(os.getenv("DOWNTIME_DB_PATH", "downtime_bot/data/downtime.sqlite"))
        allowed_content_path = Path(
            os.getenv(
                "ALLOWED_CONTENT_PATH",
                "data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json",
            )
        )
        staff_log_channel_id = os.getenv("STAFF_LOG_CHANNEL_ID")
        downtime_ledger_channel_id = os.getenv("DOWNTIME_LEDGER_CHANNEL_ID")

        return BotConfig(
            token=token,
            guild_id=guild_id,
            database_path=database_path,
            allowed_content_path=allowed_content_path,
            staff_log_channel_id=int(staff_log_channel_id) if staff_log_channel_id else None,
            downtime_ledger_channel_id=int(downtime_ledger_channel_id) if downtime_ledger_channel_id else None,
        )
