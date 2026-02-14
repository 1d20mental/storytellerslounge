from __future__ import annotations

import discord


class PermissionService:
    @staticmethod
    def is_staff(member: discord.Member) -> bool:
        if member.guild_permissions.manage_guild:
            return True
        return any(role.name.lower() in {"staff", "dm", "moderator"} for role in member.roles)
