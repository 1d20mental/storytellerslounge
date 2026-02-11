from __future__ import annotations

from recap_scribe.utils import apl_and_tier


def format_part_recap(draft: dict, part_number: int, service) -> str:
    part_key = str(part_number)
    hours = float(draft["parts"][part_key])
    roster = draft["roster"]
    levels = [int(entry["level"]) for entry in roster.values()]
    apl, tier = apl_and_tier(levels)

    lines: list[str] = [
        f"**Session Name**: {draft['session_name']}",
        f"**Game Version**: {draft['game_version']}",
        f"**Game Format**: {draft['game_format']}",
        f"**Application Format**: {draft['application_format']}",
        f"**APL and Tier**: APL {apl} Tier {tier}",
        f"**Hours Played**: {hours}",
        "",
        "**EXP, DTP, GP, Loot, and Resources Used: **",
    ]

    rewards_for_part = draft["per_part_rewards"].get(part_key, {})
    for uid, player in roster.items():
        reward = rewards_for_part.get(uid, {})
        xp = service.xp_for(int(player["level"]), hours)
        dtp = service.dtp_for(hours)
        line = (
            f"<@{uid}> as {player['character_name']} ({player['level']}) gains "
            f"{xp}XP, {reward.get('gp', 0)}GP, {dtp}DTP"
        )
        if reward.get("incentives"):
            line += f" {reward['incentives']}"
        if reward.get("loot"):
            line += f" and receives {reward['loot']}"
        if reward.get("used"):
            line += f" and uses {reward['used']}"
        if reward.get("notes"):
            line += f" ({reward['notes']})"
        lines.append(line)

    dm = draft["dm_reward_by_part"].get(part_key)
    if dm:
        lines.append("")
        dm_line = (
            f"**DM Rewards: ** <@{dm['dm_user_id']}> as {dm['dmpc_name']} "
            f"({dm['dmpc_level']}) gains {dm.get('xp', 0)}XP, {dm.get('dtp', 0)}DTP, {dm.get('gp', 0)}GP"
        )
        if dm.get("loot"):
            dm_line += f" and {dm['loot']}"
        lines.append(dm_line)

    narrative = draft["narrative_by_part"].get(part_key, {})
    if narrative.get("story_note"):
        lines.extend(["", f"**Story Note:** {narrative['story_note']}"])

    lines.extend(["", "**Session Summary**"])
    if narrative.get("session_summary"):
        lines.append(narrative["session_summary"])

    return "\n".join(lines)


def format_part_header(part_number: int) -> str:
    return f"--- Part {part_number} ---"
