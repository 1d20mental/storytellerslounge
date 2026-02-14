from __future__ import annotations

import logging

import discord


class BotLoggingService:
    def __init__(self, bot: discord.Client, staff_log_channel_id: int | None, ledger_channel_id: int | None):
        self.bot = bot
        self.staff_log_channel_id = staff_log_channel_id
        self.ledger_channel_id = ledger_channel_id
        self.logger = logging.getLogger("downtime_bot")

    async def post_staff_log(self, message: str) -> None:
        self.logger.error(message)
        if not self.staff_log_channel_id:
            return
        channel = self.bot.get_channel(self.staff_log_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(f"⚠️ {message}")

    async def post_downtime_result_embed(self, embed: discord.Embed) -> None:
        if not self.ledger_channel_id:
            self.logger.warning("No DOWNTIME_LEDGER_CHANNEL_ID configured")
            return
        channel = self.bot.get_channel(self.ledger_channel_id)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed)
