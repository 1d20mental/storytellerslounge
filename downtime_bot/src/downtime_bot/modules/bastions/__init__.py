from __future__ import annotations

from typing import Any


def setup(core: dict[str, Any]) -> None:
    engine = core["activity_engine"]

    async def resolve_research_lore(project: dict[str, Any], activity: dict[str, Any]) -> dict[str, Any]:
        return {
            "outcome": activity.get("outcome", "Completed."),
            "rolls": [],
            "gp_spent": activity.get("gp_cost", 0),
            "dtp_spent": activity.get("dtp_cost", 0),
        }

    engine.register("research_lore", resolve_research_lore)
