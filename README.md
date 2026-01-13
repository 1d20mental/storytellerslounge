# Storytellers Lounge Loot Bot

A Discord bot that loads the CSV data in this repo and provides a `/loot` slash command
for filtering magic items.

## Setup

1. **Create a Discord application + bot**
   - Enable **Message Content Intent** is not required for slash commands.
   - Copy the bot token.
2. **Set the token**
   - Export the token in your shell:
     ```bash
     export DISCORD_TOKEN="your-token-here"
     ```
3. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Run the bot**
   ```bash
   python bot.py
   ```

## Commands

### `/loot`
Filters items loaded from `data/Items_base.csv` and `data/Items_loot.csv`.

**Filters**
- `rarity`: Common / Uncommon / Rare / Very Rare / Legendary
- `category`: Armor / Weapon / Wondrous Item / etc.
- `subtype`: partial match on subtype text
- `tag`: comma-separated tags (only if a tags column exists in the CSVs)
- `limit`: number of results to show (default 10, max 50)

### `/loot_reload`
Reloads the CSV data without restarting the bot. (This is the reload companion to `/loot`.)

## Data expectations

The bot joins on `item_id` and expects:
- `data/Items_base.csv` to include `item_id`, `name`, `category`, `subtype`.
- `data/Items_loot.csv` to include `item_id` and `rarity`.

If either file is missing or required columns are absent, the bot returns clear error
messages when commands are invoked.
