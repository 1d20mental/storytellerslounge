from __future__ import annotations

import discord


class PlayerEditModal(discord.ui.Modal, title="Edit Player Rewards"):
    gp = discord.ui.TextInput(label="GP", required=False, placeholder="0")
    loot = discord.ui.TextInput(label="Loot", required=False)
    used = discord.ui.TextInput(label="Used Resources", required=False)
    incentives = discord.ui.TextInput(label="Incentives", required=False)
    notes = discord.ui.TextInput(label="Notes", required=False)

    def __init__(self, bot, draft: dict, part: int, user_id: int) -> None:
        super().__init__()
        self.bot = bot
        self.draft = draft
        self.part = part
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        payload = {
            "gp": float(self.gp.value) if self.gp.value else 0,
            "loot": self.loot.value,
            "used": self.used.value,
            "incentives": self.incentives.value,
            "notes": self.notes.value,
        }
        self.bot.service.update_player_rewards(self.draft, self.user_id, self.part, payload)
        self.bot.storage.save_draft(interaction.guild_id, self.draft)
        await interaction.response.send_message("Player rewards updated.", ephemeral=True)


class DmEditModal(discord.ui.Modal, title="Edit DM Rewards"):
    dmpc_name = discord.ui.TextInput(label="DMPC Name", required=False)
    dmpc_level = discord.ui.TextInput(label="DMPC Level", required=False, placeholder="1")
    gp = discord.ui.TextInput(label="GP", required=False)
    loot = discord.ui.TextInput(label="Loot", required=False)

    def __init__(self, bot, draft: dict, part: int, apply_all: bool, dm_user_id: int) -> None:
        super().__init__()
        self.bot = bot
        self.draft = draft
        self.part = part
        self.apply_all = apply_all
        self.dm_user_id = dm_user_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        hours = float(self.draft["parts"][str(self.part)])
        level = int(self.dmpc_level.value or 1)
        payload = {
            "dm_user_id": str(self.dm_user_id),
            "dmpc_name": self.dmpc_name.value or "DMPC",
            "dmpc_level": level,
            "xp": self.bot.service.xp_for(level, hours),
            "dtp": self.bot.service.dtp_for(hours),
            "gp": float(self.gp.value) if self.gp.value else self.bot.service.suggest_dm_gp(level, hours),
            "loot": self.loot.value,
            "notes": "",
        }
        self.bot.service.update_dm_reward(self.draft, self.part, payload, self.apply_all)
        self.bot.storage.save_draft(interaction.guild_id, self.draft)
        await interaction.response.send_message("DM rewards updated.", ephemeral=True)


class NarrativeModal(discord.ui.Modal, title="Edit Narrative"):
    story_note = discord.ui.TextInput(label="Story Note", required=False, style=discord.TextStyle.paragraph)
    session_summary = discord.ui.TextInput(
        label="Session Summary", required=False, style=discord.TextStyle.paragraph
    )

    def __init__(self, bot, draft: dict, part: int) -> None:
        super().__init__()
        self.bot = bot
        self.draft = draft
        self.part = part

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.bot.service.update_narrative(
            self.draft,
            self.part,
            self.story_note.value,
            self.session_summary.value,
        )
        self.bot.storage.save_draft(interaction.guild_id, self.draft)
        await interaction.response.send_message("Narrative updated.", ephemeral=True)
