from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger("downtime_bot")


class AllowedContentError(Exception):
    pass


def validate_allowed_content(data: dict[str, Any]) -> None:
    required = {"downtime_activities", "bastion_facilities"}
    missing = [key for key in required if key not in data]
    if missing:
        raise AllowedContentError(f"Allowed content JSON missing required keys: {', '.join(missing)}")


class AllowedContentIndex:
    def __init__(self, data: dict[str, Any]):
        validate_allowed_content(data)
        self.data = data
        self.activities_by_key: dict[str, dict[str, Any]] = {
            activity["key"]: activity for activity in data["downtime_activities"]
        }
        self.facilities_by_key: dict[str, dict[str, Any]] = {
            facility["key"]: facility for facility in data["bastion_facilities"]
        }

    def list_downtime_activities(self) -> list[dict[str, Any]]:
        return list(self.activities_by_key.values())

    def get_activity(self, activity_key: str) -> dict[str, Any] | None:
        return self.activities_by_key.get(activity_key)

    def list_bastion_facilities(self) -> list[dict[str, Any]]:
        return list(self.facilities_by_key.values())


def load_allowed_content(path: Path) -> AllowedContentIndex:
    data = json.load(open(path, "r", encoding="utf-8"))

    index = AllowedContentIndex(data)
    top_level_keys = list(data.keys())
    logger.info("Loaded allowed content JSON")
    logger.info(
        "Allowed content counts: downtime activities=%s bastion facilities=%s",
        len(index.activities_by_key),
        len(index.facilities_by_key),
    )
    logger.info("Detected top-level keys: %s", ", ".join(top_level_keys))
    return index
