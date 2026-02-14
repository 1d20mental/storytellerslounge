from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

from downtime_bot import __version__
from downtime_bot.config import Config, load_config

COLOR_SUCCESS = discord.Color.green()
COLOR_ERROR = discord.Color.red()
COLOR_INFO = discord.Color.blue()
COLOR_WARNING = discord.Color.orange()


def info_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(title=f"ℹ️ {title}", description=description, color=COLOR_INFO)


def success_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(title=f"✅ {title}", description=description, color=COLOR_SUCCESS)


def error_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(title=f"❌ {title}", description=description, color=COLOR_ERROR)


def warning_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(title=f"⚠️ {title}", description=description, color=COLOR_WARNING)


def chunk_lines(lines: list[str], limit: int = 25) -> list[list[str]]:
    return [lines[i : i + limit] for i in range(0, len(lines), limit)] or [[]]


class DowntimeBot(discord.Client):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.none()
        intents.guilds = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.config = config
        self.allowed_content_loaded = False
        self.allowed_content_error: str | None = None

    async def setup_hook(self) -> None:
        self._init_database()
        self._load_allowed_content()
        self._register_commands()
        await self._sync_commands()

    def _init_database(self) -> None:
        self.config.downtime_db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.config.downtime_db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _load_allowed_content(self) -> None:
        try:
            with self.config.allowed_content_path.open("r", encoding="utf-8") as handle:
                json.load(handle)
            self.allowed_content_loaded = True
        except Exception as exc:  # noqa: BLE001
            self.allowed_content_loaded = False
            self.allowed_content_error = str(exc)

    async def _sync_commands(self) -> None:
        if self.config.sync_mode == "global" or self.config.discord_guild_id is None:
            await self.tree.sync()
            print("Commands synced globally")
            return

        guild = discord.Object(id=self.config.discord_guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"Commands synced to guild {self.config.discord_guild_id}")

    async def on_ready(self) -> None:
        print(f"Downtime bot connected as {self.user}")

    async def post_staff_error(self, message: str) -> None:
        if not self.config.staff_log_channel_id:
            return
        channel = self.get_channel(self.config.staff_log_channel_id)
        if isinstance(channel, discord.abc.Messageable):
            await channel.send(embed=error_embed("Downtime Bot Error", message))

    async def post_ledger_result(self, embed: discord.Embed) -> None:
        if not self.config.downtime_ledger_channel_id:
            return
        channel = self.get_channel(self.config.downtime_ledger_channel_id)
        if isinstance(channel, discord.abc.Messageable):
            await channel.send(embed=embed)

    def _register_commands(self) -> None:
        @self.tree.command(name="ping", description="Diagnostic connectivity check")
        async def ping(interaction: discord.Interaction) -> None:
            await interaction.response.send_message(
                embed=success_embed("Pong", "Bot is responsive."),
                ephemeral=True,
            )

        @self.tree.command(name="about", description="Show bot runtime configuration and health")
        async def about(interaction: discord.Interaction) -> None:
            db_path = self.config.downtime_db_path.resolve()
            allowed_path = self.config.allowed_content_path.resolve()

            if self.config.sync_mode == "global" or self.config.discord_guild_id is None:
                sync_value = "Global"
            else:
                sync_value = f"Guild (`{self.config.discord_guild_id}`)"

            staff_channel = (
                f"`{self.config.staff_log_channel_id}`"
                if self.config.staff_log_channel_id
                else "Not configured"
            )
            ledger_channel = (
                f"`{self.config.downtime_ledger_channel_id}`"
                if self.config.downtime_ledger_channel_id
                else "Not configured"
            )

            perms_summary = "Unknown"
            if isinstance(interaction.channel, discord.abc.GuildChannel) and interaction.guild and interaction.guild.me:
                perms = interaction.channel.permissions_for(interaction.guild.me)
                perms_summary = (
                    f"Send Messages: {'Yes' if perms.send_messages else 'No'} | "
                    f"Embed Links: {'Yes' if perms.embed_links else 'No'}"
                )

            title = "Downtime Bot Status" if self.allowed_content_loaded else "Downtime Bot Status ⚠️"
            embed = discord.Embed(title=title, color=COLOR_INFO)
            embed.add_field(name="Version", value=f"`{__version__}`", inline=False)
            embed.add_field(name="Sync Mode", value=sync_value, inline=False)
            embed.add_field(
                name="Database Path",
                value=f"`{db_path}`\nExists: {'Yes' if db_path.exists() else 'No'}",
                inline=False,
            )
            allowed_status = "Yes" if self.allowed_content_loaded else "No ⚠️"
            allowed_value = f"`{allowed_path}`\nExists: {'Yes' if allowed_path.exists() else 'No'}\nLoaded: {allowed_status}"
            if self.allowed_content_error:
                allowed_value += f"\nError: `{self.allowed_content_error[:120]}`"
            embed.add_field(name="Allowed Content Path", value=allowed_value, inline=False)
            embed.add_field(name="Staff Log Channel", value=staff_channel, inline=True)
            embed.add_field(name="Downtime Ledger Channel", value=ledger_channel, inline=True)
            embed.add_field(name="Bot Permissions Summary", value=perms_summary, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        admin_group = app_commands.Group(name="admin", description="Administrative commands")

        @admin_group.command(name="sync", description="Manually sync slash commands")
        async def admin_sync(interaction: discord.Interaction) -> None:
            if not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message(
                    embed=error_embed("Unauthorized", "Administrator permission is required."),
                    ephemeral=True,
                )
                return
            if self.config.sync_mode == "global" or self.config.discord_guild_id is None:
                synced = await self.tree.sync()
                scope = "globally"
            else:
                guild = discord.Object(id=self.config.discord_guild_id)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                scope = f"to guild `{self.config.discord_guild_id}`"
            await interaction.response.send_message(
                embed=success_embed("Sync complete", f"Synced `{len(synced)}` command(s) {scope}."),
                ephemeral=True,
            )

        self.tree.add_command(admin_group)

        @self.tree.command(name="downtime_log", description="Record a downtime result in the append-only ledger")
        @app_commands.describe(summary="Resolved downtime result summary")
        async def downtime_log(interaction: discord.Interaction, summary: str) -> None:
            if len(summary) > 800:
                await interaction.response.send_message(
                    embed=warning_embed("Input too long", "Keep summary under 800 characters."),
                    ephemeral=True,
                )
                return

            try:
                with sqlite3.connect(self.config.downtime_db_path) as conn:
                    conn.execute(
                        "INSERT INTO ledger (user_id, summary) VALUES (?, ?)",
                        (str(interaction.user.id), summary),
                    )
                base = success_embed("Downtime recorded", "Entry appended to ledger.")
                base.add_field(name="User", value=f"`{interaction.user.id}`", inline=True)
                lines = [f"- {line}" for line in summary.splitlines() if line.strip()] or [f"- {summary}"]
                chunks = chunk_lines(lines)
                base.add_field(name="Summary (part 1)", value="\n".join(chunks[0])[:1000], inline=False)

                await interaction.response.send_message(embed=base, ephemeral=True)
                for idx, chunk in enumerate(chunks[1:], start=2):
                    extra = info_embed("Downtime summary continued", "Additional submitted details.")
                    extra.add_field(name=f"Summary (part {idx})", value="\n".join(chunk)[:1000], inline=False)
                    await interaction.followup.send(embed=extra, ephemeral=True)

                ledger_embed = success_embed("Downtime Result", summary[:3500])
                ledger_embed.add_field(name="Submitted by", value=interaction.user.mention, inline=True)
                await self.post_ledger_result(ledger_embed)
            except Exception as exc:  # noqa: BLE001
                await self.post_staff_error(str(exc))
                await interaction.response.send_message(
                    embed=error_embed("Failed to record downtime", "The error was reported to staff logs."),
                    ephemeral=True,
                )


def main() -> None:
    load_dotenv("downtime_bot/.env")
    config = load_config()
    if not config.discord_token:
        raise RuntimeError("DISCORD_TOKEN is required")
    bot = DowntimeBot(config)
    bot.run(config.discord_token)


if __name__ == "__main__":
    main()
