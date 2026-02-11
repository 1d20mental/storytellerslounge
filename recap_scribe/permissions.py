from __future__ import annotations

import discord


class PermissionError(Exception):
    pass


def validate_dm_context(
    interaction: discord.Interaction,
    dm_role_name: str,
    draft_channel_name: str,
) -> None:
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        raise PermissionError("This command can only be used in a server.")

    guild = interaction.guild
    member = interaction.user

    dm_role = discord.utils.find(lambda r: r.name == dm_role_name, guild.roles)
    has_dm_role = dm_role is not None and dm_role in member.roles
    fallback_allowed = member.guild_permissions.manage_guild or guild.owner_id == member.id

    if dm_role is not None:
        if not has_dm_role:
            raise PermissionError(f"You must have the '{dm_role_name}' role.")
    elif not fallback_allowed:
        raise PermissionError(
            f"Role '{dm_role_name}' was not found. Only server owner/admin fallback is allowed."
        )

    if interaction.channel is None or interaction.channel.name != draft_channel_name:
        raise PermissionError(f"This command must be used in #{draft_channel_name}.")
