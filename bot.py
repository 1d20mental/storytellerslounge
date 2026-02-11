from __future__ import annotations

import json
import logging
import os
from io import BytesIO
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

from recap_scribe.formatter import format_part_header, format_part_recap
from recap_scribe.permissions import PermissionError, validate_dm_context
from recap_scribe.services import RecapService
from recap_scribe.storage import JsonGuildStorage
from recap_scribe.ui_modals import DmEditModal, NarrativeModal, PlayerEditModal
from recap_scribe.utils import clamp_hours, dtp_for_hours, round_half_step, split_discord_messages, split_hours

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recap-scribe")


class RecapScribeBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

        self.sync_mode = os.getenv("SYNC_MODE", "guild")
        self.guild_id = int(os.getenv("DISCORD_GUILD_ID", "0") or "0")
        self.dm_role_name = os.getenv("DM_ROLE_NAME", "DM")
        self.draft_channel_name = os.getenv("DRAFT_CHANNEL_NAME", "dm-drafts")
        self.default_publish_channel = os.getenv("DEFAULT_PUBLISH_CHANNEL", "session-log")
        data_dir = Path(os.getenv("DATA_DIR", "data"))

        self.rules = self._load_rules()
        self.storage = JsonGuildStorage(data_dir)
        self.service = RecapService(self.storage, self.rules)

    def _load_rules(self) -> dict:
        path = Path("config/rules.json")
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return json.loads(Path("config/rules.example.json").read_text(encoding="utf-8"))

    async def setup_hook(self) -> None:
        self.register_commands()
        if self.guild_id and self.sync_mode != "global":
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("Commands synced to guild %s", self.guild_id)
        else:
            await self.tree.sync()
            logger.info("Commands synced globally")

    def register_commands(self) -> None:
        @self.tree.command(name="ping", description="Diagnostic ping")
        async def ping(interaction: discord.Interaction) -> None:
            await interaction.response.send_message("Pong", ephemeral=True)

        @self.tree.command(name="audit", description="Self-audit XP and DTP for session hours")
        @app_commands.describe(level="Character level", hours="Total hours (0.5 to 17.5)")
        async def audit(interaction: discord.Interaction, level: app_commands.Range[int, 1, 20], hours: float) -> None:
            hours = round_half_step(clamp_hours(hours))
            parts = split_hours(hours)
            lines = [f"Audit for level {level}, total hours {hours}"]
            total_xp = 0
            total_dtp = 0
            for idx, part_hours in enumerate(parts, start=1):
                xp = self.service.xp_for(level, part_hours)
                dtp = dtp_for_hours(part_hours)
                total_xp += xp
                total_dtp += dtp
                lines.append(f"Part {idx}: {part_hours}h -> {xp} XP, {dtp} DTP")
            lines.append(f"Totals: {total_xp} XP, {total_dtp} DTP")
            await interaction.response.send_message("\n".join(lines), ephemeral=True)

        admin_group = app_commands.Group(name="admin", description="Admin tools")

        @admin_group.command(name="sync", description="Resync slash commands")
        async def admin_sync(interaction: discord.Interaction) -> None:
            if interaction.guild is None or not isinstance(interaction.user, discord.Member):
                await interaction.response.send_message("Server-only command.", ephemeral=True)
                return
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("Administrator only.", ephemeral=True)
                return
            if self.guild_id and self.sync_mode != "global":
                guild = discord.Object(id=self.guild_id)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                await interaction.response.send_message(f"Synced {len(synced)} guild command(s).", ephemeral=True)
            else:
                synced = await self.tree.sync()
                await interaction.response.send_message(f"Synced {len(synced)} global command(s).", ephemeral=True)

        self.tree.add_command(admin_group)

        recap_group = app_commands.Group(name="recap", description="Session recap drafting tools")
        part_group = app_commands.Group(name="part", description="Current part tools", parent=recap_group)
        player_group = app_commands.Group(name="player", description="Player editing tools", parent=recap_group)
        dm_group = app_commands.Group(name="dm", description="DM reward tools", parent=recap_group)

        async def get_dm_draft(interaction: discord.Interaction) -> dict | None:
            try:
                validate_dm_context(interaction, self.dm_role_name, self.draft_channel_name)
            except PermissionError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return None
            draft = self.service.get_active_or_none(interaction.guild_id, interaction.user.id)
            if not draft:
                await interaction.response.send_message("No active draft. Use /recap start first.", ephemeral=True)
            return draft

        @recap_group.command(name="start", description="Start a new recap draft")
        @app_commands.choices(
            game_format=[
                app_commands.Choice(name="Voice", value="Voice"),
                app_commands.Choice(name="Text", value="Text"),
                app_commands.Choice(name="PBP", value="PBP"),
            ],
            application_format=[
                app_commands.Choice(name="Open", value="Open"),
                app_commands.Choice(name="Closed", value="Closed"),
            ],
        )
        async def recap_start(
            interaction: discord.Interaction,
            session_name: str,
            hours: float,
            game_version: str = "2024",
            game_format: app_commands.Choice[str] | None = None,
            application_format: app_commands.Choice[str] | None = None,
            event: str | None = None,
        ) -> None:
            try:
                validate_dm_context(interaction, self.dm_role_name, self.draft_channel_name)
            except PermissionError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return

            rounded_hours = round_half_step(clamp_hours(hours))
            draft = self.service.create_draft(
                interaction.guild_id,
                interaction.user.id,
                session_name,
                rounded_hours,
                game_version,
                (game_format.value if game_format else "Voice"),
                (application_format.value if application_format else "Open"),
                event,
            )
            parts_text = ", ".join([f"Part {k}: {v}h" for k, v in draft["parts"].items()])
            await interaction.response.send_message(
                f"Draft `{draft['id']}` created and set active. Total hours rounded to {rounded_hours}.\n{parts_text}",
                ephemeral=True,
            )

        @recap_group.command(name="list", description="List your drafts")
        async def recap_list(interaction: discord.Interaction) -> None:
            try:
                validate_dm_context(interaction, self.dm_role_name, self.draft_channel_name)
            except PermissionError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
            drafts = self.storage.list_user_drafts(interaction.guild_id, interaction.user.id)
            active = self.storage.get_active_draft(interaction.guild_id, interaction.user.id)
            if not drafts:
                await interaction.response.send_message("No drafts found.", ephemeral=True)
                return
            lines = []
            for d in drafts:
                flag = " (active)" if active and d["id"] == active["id"] else ""
                lines.append(f"`{d['id']}` - {d['session_name']}{flag}")
            await interaction.response.send_message("\n".join(lines), ephemeral=True)

        @recap_group.command(name="use", description="Set active draft")
        async def recap_use(interaction: discord.Interaction, draft_id: str) -> None:
            try:
                validate_dm_context(interaction, self.dm_role_name, self.draft_channel_name)
            except PermissionError as exc:
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
            target = self.storage.get_draft(interaction.guild_id, draft_id)
            if not target:
                await interaction.response.send_message("Draft not found.", ephemeral=True)
                return
            self.storage.set_active_draft(interaction.guild_id, interaction.user.id, draft_id)
            await interaction.response.send_message(f"Active draft set to `{draft_id}`.", ephemeral=True)

        @recap_group.command(name="delete", description="Delete active draft")
        async def recap_delete(interaction: discord.Interaction) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return
            self.storage.delete_draft(interaction.guild_id, draft["id"])
            await interaction.response.send_message(f"Deleted draft `{draft['id']}`.", ephemeral=True)

        @part_group.command(name="list", description="List parts and current part")
        async def part_list(interaction: discord.Interaction) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return
            current = self.service.current_part(draft, interaction.user.id)
            lines = []
            for pnum, phours in draft["parts"].items():
                marker = " <- current" if int(pnum) == current else ""
                lines.append(f"Part {pnum}: {phours}h{marker}")
            await interaction.response.send_message("\n".join(lines), ephemeral=True)

        @part_group.command(name="set", description="Set current part")
        async def part_set(interaction: discord.Interaction, part_number: int) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return
            if str(part_number) not in draft["parts"]:
                await interaction.response.send_message("Invalid part number.", ephemeral=True)
                return
            self.service.set_current_part(draft, interaction.user.id, part_number)
            self.storage.save_draft(interaction.guild_id, draft)
            await interaction.response.send_message(f"Current part set to {part_number}.", ephemeral=True)

        @player_group.command(name="add", description="Add or update a player in roster")
        async def player_add(
            interaction: discord.Interaction,
            user: discord.Member,
            character_name: str,
            level: app_commands.Range[int, 1, 20],
            gp: float | None = None,
            loot: str | None = None,
            used: str | None = None,
            incentives: str | None = None,
            notes: str | None = None,
            part_number: int | None = None,
        ) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return
            part = part_number or self.service.current_part(draft, interaction.user.id)
            if str(part) not in draft["parts"]:
                await interaction.response.send_message("Invalid part number.", ephemeral=True)
                return
            self.service.upsert_player(
                draft,
                user.id,
                user.display_name,
                character_name,
                int(level),
                part,
                gp,
                loot,
                used,
                incentives,
                notes,
            )
            self.storage.save_draft(interaction.guild_id, draft)
            max_gp = self.service.max_gp_hint(int(level))
            await interaction.response.send_message(
                f"Player {user.mention} set as {character_name} level {level}. Max GP hint: {max_gp}",
                ephemeral=True,
            )

        @player_group.command(name="edit", description="Edit player rewards by modal")
        async def player_edit(interaction: discord.Interaction, user: discord.Member, part_number: int | None = None) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return
            if str(user.id) not in draft["roster"]:
                await interaction.response.send_message("User is not in roster.", ephemeral=True)
                return
            part = part_number or self.service.current_part(draft, interaction.user.id)
            await interaction.response.send_modal(PlayerEditModal(self, draft, part, user.id))

        @player_group.command(name="remove", description="Remove player from roster")
        async def player_remove(interaction: discord.Interaction, user: discord.Member) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return
            self.service.remove_player(draft, user.id)
            self.storage.save_draft(interaction.guild_id, draft)
            await interaction.response.send_message(f"Removed {user.mention} from roster.", ephemeral=True)

        @dm_group.command(name="edit", description="Edit DM rewards")
        async def recap_dm(interaction: discord.Interaction, part_number: int | None = None, apply_to_all_parts: bool = True) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return
            part = part_number or self.service.current_part(draft, interaction.user.id)
            await interaction.response.send_modal(DmEditModal(self, draft, part, apply_to_all_parts, interaction.user.id))

        @recap_group.command(name="narrative", description="Edit story note and summary")
        async def recap_narrative(interaction: discord.Interaction, part_number: int | None = None) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return
            part = part_number or self.service.current_part(draft, interaction.user.id)
            await interaction.response.send_modal(NarrativeModal(self, draft, part))

        def build_output(draft: dict, part_number: int) -> str:
            if part_number == 0:
                blocks = []
                for p in sorted(draft["parts"], key=lambda x: int(x)):
                    blocks.append(format_part_header(int(p)))
                    blocks.append(format_part_recap(draft, int(p), self.service))
                return "\n\n".join(blocks)
            if str(part_number) not in draft["parts"]:
                raise ValueError("Invalid part number")
            return format_part_recap(draft, part_number, self.service)

        @recap_group.command(name="preview", description="Preview recap text")
        async def recap_preview(interaction: discord.Interaction, part_number: int = 0) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return
            try:
                output = build_output(draft, part_number)
            except ValueError:
                await interaction.response.send_message("Invalid part_number.", ephemeral=True)
                return

            chunks = split_discord_messages(output)
            await interaction.response.send_message(chunks[0], ephemeral=True)
            for ch in chunks[1:]:
                await interaction.followup.send(ch, ephemeral=True)

        @recap_group.command(name="export", description="Export recap text as txt file")
        async def recap_export(interaction: discord.Interaction, part_number: int = 0) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return
            try:
                output = build_output(draft, part_number)
            except ValueError:
                await interaction.response.send_message("Invalid part_number.", ephemeral=True)
                return
            payload = BytesIO(output.encode("utf-8"))
            await interaction.response.send_message(
                "Export ready.",
                file=discord.File(payload, filename=f"recap_{draft['id']}.txt"),
                ephemeral=True,
            )

        @recap_group.command(name="publish", description="Publish recap to session log channel")
        async def recap_publish(
            interaction: discord.Interaction,
            part_number: int = 0,
            channel: discord.TextChannel | None = None,
        ) -> None:
            draft = await get_dm_draft(interaction)
            if not draft:
                return

            target = channel
            if target is None:
                target = discord.utils.find(
                    lambda ch: isinstance(ch, discord.TextChannel) and ch.name == self.default_publish_channel,
                    interaction.guild.channels,
                )
            if target is None:
                await interaction.response.send_message(
                    f"Could not find target channel #{self.default_publish_channel}.",
                    ephemeral=True,
                )
                return
            try:
                output = build_output(draft, part_number)
            except ValueError:
                await interaction.response.send_message("Invalid part_number.", ephemeral=True)
                return

            for msg in split_discord_messages(output):
                await target.send(msg)
            await interaction.response.send_message(f"Published to {target.mention}.", ephemeral=True)

        self.tree.add_command(recap_group)

        listing_group = app_commands.Group(name="listing", description="Future listing tools")

        @listing_group.command(name="generate", description="Future listing + ad generator")
        async def listing_generate(interaction: discord.Interaction) -> None:
            await interaction.response.send_message("Not implemented yet.", ephemeral=True)

        self.tree.add_command(listing_group)



def main() -> None:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN is required in .env")

    bot = RecapScribeBot()
    bot.run(token)


if __name__ == "__main__":
    main()
