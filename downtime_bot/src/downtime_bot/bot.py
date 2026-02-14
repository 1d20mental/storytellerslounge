from __future__ import annotations

import logging
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from downtime_bot.core.activity_engine import ActivityEngine
from downtime_bot.core.allowed_content_loader import AllowedContentError, load_allowed_content
from downtime_bot.core.characters import CharacterService
from downtime_bot.core.config import BotConfig
from downtime_bot.core.ledger import LedgerService
from downtime_bot.core.logging_service import BotLoggingService
from downtime_bot.core.permissions import PermissionService
from downtime_bot.core.projects import ProjectService
from downtime_bot.core.storage import Storage
from downtime_bot.modules import bastions

logging.basicConfig(level=logging.INFO)


class DowntimeBot(commands.Bot):
    def __init__(self, config: BotConfig):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        self.storage = Storage(config.database_path)
        self.storage.migrate()
        self.conn = self.storage.connect()
        self.characters = CharacterService(self.conn)
        self.ledger = LedgerService(self.conn)
        self.projects = ProjectService(self.conn)
        self.activity_engine = ActivityEngine()
        self.allowed_content = None
        self.log_service = BotLoggingService(self, config.staff_log_channel_id, config.downtime_ledger_channel_id)

    async def setup_hook(self) -> None:
        try:
            self.allowed_content = load_allowed_content(self.config.allowed_content_path)
        except (AllowedContentError, FileNotFoundError) as exc:
            await self.log_service.post_staff_log(f"Allowed content load failed: {exc}")
            raise

        bastions.setup({"activity_engine": self.activity_engine})
        guild = discord.Object(id=self.config.guild_id)
        self.tree.add_command(char_group)
        self.tree.add_command(dtp_group)
        self.tree.add_command(downtime_group)
        await self.tree.sync(guild=guild)


bot_config = BotConfig.from_env()
bot = DowntimeBot(bot_config)

char_group = app_commands.Group(name="char", description="Character registry")
dtp_group = app_commands.Group(name="dtp", description="Downtime points")
downtime_group = app_commands.Group(name="downtime", description="Downtime projects")


def _activity_theme(activity: dict[str, Any]) -> tuple[discord.Color, str | None]:
    """Return color and optional emoji label based on activity metadata or key/name hints."""
    color_name = str(activity.get("color", "")).strip().lower()
    color_map = {
        "blue": discord.Color.blue(),
        "green": discord.Color.green(),
        "gold": discord.Color.gold(),
        "orange": discord.Color.orange(),
        "purple": discord.Color.purple(),
        "red": discord.Color.red(),
        "teal": discord.Color.teal(),
    }
    if color_name in color_map:
        return color_map[color_name], None

    identity = f"{activity.get('key', '')} {activity.get('name', '')}".lower()
    if any(token in identity for token in ("research", "lore", "study", "archive")):
        return discord.Color.blue(), "📘"
    if any(token in identity for token in ("craft", "forge", "brew", "smith")):
        return discord.Color.orange(), "🛠️"
    if any(token in identity for token in ("market", "trade", "sell", "buy")):
        return discord.Color.gold(), "💰"
    if any(token in identity for token in ("bastion", "facility", "build")):
        return discord.Color.green(), "🏰"
    return discord.Color.blurple(), "🧭"


@char_group.command(name="register", description="Register a character")
@app_commands.describe(name="Character name", level="Optional level", tier="Optional tier")
async def char_register(interaction: discord.Interaction, name: str, level: int | None = None, tier: int | None = None):
    character_id = bot.characters.register(str(interaction.user.id), name, level, tier)
    await interaction.response.send_message(f"Registered {name} with id {character_id}.", ephemeral=True)


@char_group.command(name="select", description="Select active character")
@app_commands.describe(name="Character name")
async def char_select(interaction: discord.Interaction, name: str):
    character_id = bot.characters.select_active(str(interaction.user.id), name)
    if character_id is None:
        await interaction.response.send_message("Character not found.", ephemeral=True)
        return
    await interaction.response.send_message(f"Selected {name} (id {character_id}) as active.", ephemeral=True)


@dtp_group.command(name="balance", description="Get DTP balance")
async def dtp_balance(interaction: discord.Interaction):
    active = bot.characters.get_active(str(interaction.user.id))
    if not active:
        await interaction.response.send_message("No active character. Use /char select first.", ephemeral=True)
        return
    balance = bot.ledger.get_balance(int(active["id"]))
    await interaction.response.send_message(f"{active['name']} balance: {balance} DTP", ephemeral=True)


@dtp_group.command(name="transactions", description="List DTP transactions")
@app_commands.describe(limit="Max rows")
async def dtp_transactions(interaction: discord.Interaction, limit: int = 10):
    active = bot.characters.get_active(str(interaction.user.id))
    if not active:
        await interaction.response.send_message("No active character.", ephemeral=True)
        return
    txs = bot.ledger.list_transactions(int(active["id"]), limit)
    lines = [f"#{row['id']} {row['type']} {row['amount']} ({row['reason']})" for row in txs]
    await interaction.response.send_message("\n".join(lines) if lines else "No transactions.", ephemeral=True)


@dtp_group.command(name="award", description="Award DTP (staff only)")
@app_commands.describe(character_name="Character name", amount="Positive or negative", reason="Reason")
async def dtp_award(interaction: discord.Interaction, character_name: str, amount: int, reason: str):
    member = interaction.user if isinstance(interaction.user, discord.Member) else None
    if not member or not PermissionService.is_staff(member):
        await interaction.response.send_message("Staff only command.", ephemeral=True)
        return
    character = bot.characters.get_by_name(character_name)
    if not character:
        await interaction.response.send_message("Character not found.", ephemeral=True)
        return
    tx_id = bot.ledger.append_transaction(
        actor_discord_id=str(interaction.user.id),
        character_id=int(character["id"]),
        tx_type="award",
        amount=amount,
        reason=reason,
    )
    await interaction.response.send_message(f"Awarded {amount} DTP. Transaction #{tx_id}", ephemeral=True)


@downtime_group.command(name="list", description="List downtime activities")
async def downtime_list(interaction: discord.Interaction):
    items = bot.allowed_content.list_downtime_activities()
    if not items:
        await interaction.response.send_message("No downtime activities found.", ephemeral=True)
        return

    preview_color, _ = _activity_theme(items[0])
    embed = discord.Embed(title="Available Downtime Activities", color=preview_color)
    for activity in items:
        _, icon = _activity_theme(activity)
        label = f"{icon + ' ' if icon else ''}{activity['name']}"
        value = (
            f"Key: `{activity['key']}`\n"
            f"Cost: **{activity.get('dtp_cost', 0)} DTP**, **{activity.get('gp_cost', 0)} GP**\n"
            f"{activity.get('description', 'No description provided.')}"
        )
        embed.add_field(name=label, value=value, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@downtime_group.command(name="start", description="Start a downtime activity")
@app_commands.describe(activity_key="Activity key from /downtime list")
async def downtime_start(interaction: discord.Interaction, activity_key: str):
    active = bot.characters.get_active(str(interaction.user.id))
    if not active:
        await interaction.response.send_message("No active character.", ephemeral=True)
        return
    activity = bot.allowed_content.get_activity(activity_key)
    if not activity:
        await interaction.response.send_message("Unknown activity key.", ephemeral=True)
        return
    project_id = bot.projects.start_project(
        character_id=int(active["id"]),
        activity_key=activity_key,
        dtp_required=int(activity.get("dtp_cost", 0)),
        gp_required=int(activity.get("gp_cost", 0)),
    )
    await interaction.response.send_message(f"Started project #{project_id} for {activity['name']}.", ephemeral=True)


@downtime_group.command(name="commit", description="Commit DTP to project")
@app_commands.describe(project_id="Project ID", dtp_amount="Amount to commit")
async def downtime_commit(interaction: discord.Interaction, project_id: int, dtp_amount: int):
    project = bot.projects.get_project(project_id)
    if not project:
        await interaction.response.send_message("Project not found.", ephemeral=True)
        return
    active = bot.characters.get_active(str(interaction.user.id))
    if not active or int(active["id"]) != int(project["character_id"]):
        await interaction.response.send_message("Project does not belong to your active character.", ephemeral=True)
        return
    bot.projects.commit_dtp(project_id, dtp_amount)
    project = bot.projects.get_project(project_id)
    await interaction.response.send_message(
        f"Project #{project_id}: {project['dtp_committed']}/{project['dtp_required']} DTP committed.",
        ephemeral=True,
    )


@downtime_group.command(name="resolve", description="Resolve downtime project")
@app_commands.describe(project_id="Project ID")
async def downtime_resolve(interaction: discord.Interaction, project_id: int):
    project = bot.projects.get_project(project_id)
    if not project:
        await interaction.response.send_message("Project not found.", ephemeral=True)
        return
    if int(project["dtp_committed"]) < int(project["dtp_required"]):
        await interaction.response.send_message("Not enough DTP committed.", ephemeral=True)
        return

    activity = bot.allowed_content.get_activity(project["activity_key"])
    result = await bot.activity_engine.resolve(project["activity_key"], dict(project), activity)

    dtp_tx_id = bot.ledger.append_transaction(
        actor_discord_id=str(interaction.user.id),
        character_id=int(project["character_id"]),
        tx_type="spend",
        amount=-int(project["dtp_required"]),
        reason=f"Downtime project #{project_id}: {activity['name']}",
        metadata={"project_id": project_id},
    )
    bot.projects.resolve_project(project_id, result)

    character = bot.characters.get_by_id(int(project["character_id"]))
    color, icon = _activity_theme(activity)
    title_prefix = f"{icon} " if icon else ""
    embed = discord.Embed(title=f"{title_prefix}Downtime Result: {activity['name']}", color=color)
    embed.description = (
        f"Project `#{project_id}` resolved successfully.\n"
        f"Activity key: `{project['activity_key']}`"
    )
    embed.add_field(name="Character", value=str(character["name"]), inline=True)
    embed.add_field(name="User", value=interaction.user.mention, inline=True)
    embed.add_field(name="DTP spent", value=str(project["dtp_required"]), inline=True)
    embed.add_field(name="GP spent/earned", value=str(activity.get("gp_cost", 0)), inline=True)
    embed.add_field(name="Status", value="✅ Completed", inline=True)
    embed.add_field(name="Rolls", value=result.get("rolls", "None"), inline=False)
    embed.add_field(name="Outcome", value=result.get("outcome", "Completed."), inline=False)
    embed.add_field(name="Transaction IDs", value=f"{dtp_tx_id}", inline=False)
    embed.add_field(name="Project ID", value=str(project_id), inline=False)

    thumbnail_url = activity.get("thumbnail_url") or activity.get("image_url")
    if isinstance(thumbnail_url, str) and thumbnail_url.strip():
        embed.set_thumbnail(url=thumbnail_url.strip())

    embed.set_footer(text="Storyteller's Lounge • Downtime Ledger")
    await bot.log_service.post_downtime_result_embed(embed)

    await interaction.response.send_message(
        f"Resolved project #{project_id}. Ledger transaction #{dtp_tx_id} created.", ephemeral=True
    )


def main() -> None:
    if not bot_config.token:
        raise RuntimeError("DISCORD_TOKEN is required")
    bot.run(bot_config.token)


if __name__ == "__main__":
    main()
