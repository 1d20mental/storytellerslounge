import logging
import os
from pathlib import Path
from typing import List, Optional

import discord
from discord import app_commands

from loot_data import LootDataError, LootDataStore, LootItem


DATA_BASE_PATH = Path("data/Items_base.csv")
DATA_LOOT_PATH = Path("data/Items_loot.csv")
DEFAULT_LIMIT = 10
MAX_LIMIT = 50
RARITY_CHOICES = [
    "Common",
    "Uncommon",
    "Rare",
    "Very Rare",
    "Legendary",
]


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("loot-bot")


class LootBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.data_store = LootDataStore(DATA_BASE_PATH, DATA_LOOT_PATH)
        self.last_load_error: Optional[str] = None

    async def setup_hook(self) -> None:
        await self._load_data()
        await self.tree.sync()

    async def _load_data(self) -> None:
        try:
            self.data_store.load()
            self.last_load_error = None
            logger.info("Loaded %s loot items", len(self.data_store.items))
        except LootDataError as exc:
            self.last_load_error = str(exc)
            logger.error("Failed to load loot data: %s", exc)


bot = LootBot()


def _format_item(item: LootItem) -> str:
    subtype = f" — {item.subtype}" if item.subtype else ""
    return f"• **{item.name}** ({item.category}{subtype}) — {item.rarity}"


def _filter_items(
    items: List[LootItem],
    rarity: Optional[str],
    category: Optional[str],
    subtype: Optional[str],
    tags: Optional[List[str]],
) -> List[LootItem]:
    filtered = items
    if rarity:
        rarity_norm = rarity.strip().lower()
        filtered = [item for item in filtered if item.rarity_norm == rarity_norm]
    if category:
        category_norm = category.strip().lower()
        filtered = [item for item in filtered if item.category_norm == category_norm]
    if subtype:
        subtype_norm = subtype.strip().lower()
        filtered = [item for item in filtered if subtype_norm in item.subtype_norm]
    if tags:
        filtered = [
            item
            for item in filtered
            if all(tag in item.tags for tag in tags)
        ]
    return filtered


@bot.tree.command(name="loot", description="Find loot items with optional filters.")
@app_commands.describe(
    rarity="Common, Uncommon, Rare, Very Rare, Legendary",
    category="Armor, Weapon, Wondrous Item, etc.",
    subtype="Partial subtype match",
    tag="Comma-separated tags",
    limit="Maximum results to return (default 10)",
)
@app_commands.choices(
    rarity=[app_commands.Choice(name=choice, value=choice) for choice in RARITY_CHOICES]
)
async def loot(
    interaction: discord.Interaction,
    rarity: Optional[app_commands.Choice[str]] = None,
    category: Optional[str] = None,
    subtype: Optional[str] = None,
    tag: Optional[str] = None,
    limit: Optional[int] = None,
) -> None:
    if bot.last_load_error:
        await interaction.response.send_message(
            f"Loot data is unavailable: {bot.last_load_error}", ephemeral=True
        )
        return

    parsed_limit = limit or DEFAULT_LIMIT
    if parsed_limit <= 0:
        await interaction.response.send_message(
            "Limit must be a positive number.", ephemeral=True
        )
        return
    if parsed_limit > MAX_LIMIT:
        parsed_limit = MAX_LIMIT

    tags = None
    if tag:
        if not bot.data_store.has_tags:
            await interaction.response.send_message(
                "Tag filtering is not available because the data has no tags column.",
                ephemeral=True,
            )
            return
        tags = [t.strip().lower() for t in tag.split(",") if t.strip()]
        if not tags:
            await interaction.response.send_message(
                "Tag filter must include at least one tag.", ephemeral=True
            )
            return

    results = _filter_items(
        bot.data_store.items,
        rarity.value if rarity else None,
        category,
        subtype,
        tags,
    )

    if not results:
        await interaction.response.send_message(
            "No items matched your filters.", ephemeral=True
        )
        return

    total = len(results)
    preview = results[:parsed_limit]
    lines = [
        f"Found {total} item(s). Showing {len(preview)}:",
        *(_format_item(item) for item in preview),
    ]
    await interaction.response.send_message("\n".join(lines))


@bot.tree.command(name="loot_reload", description="Reload loot data from CSVs.")
async def loot_reload(interaction: discord.Interaction) -> None:
    await bot._load_data()
    if bot.last_load_error:
        await interaction.response.send_message(
            f"Reload failed: {bot.last_load_error}", ephemeral=True
        )
        return
    await interaction.response.send_message(
        f"Reloaded {len(bot.data_store.items)} items.", ephemeral=True
    )


def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit(
            "DISCORD_TOKEN is not set. Provide your bot token as an environment variable."
        )
    bot.run(token)


if __name__ == "__main__":
    main()
