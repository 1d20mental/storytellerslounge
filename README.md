# Recap Scribe

Recap Scribe is a Discord slash-command bot for Dungeon Masters to draft, preview, export, and publish D&D session recap logs.


## Downtime Bot (Hetzner)

Downtime bot lives under `downtime_bot/` and deploys as a separate systemd service (`downtime_bot.service`).

```bash
cd /opt/storytellerslounge
git fetch --all --prune
git checkout main
git pull
ls -la downtime_bot || REPO_URL=git@github.com:<ORG>/<REPO>.git REF=main bash scripts/pull_downtime_from_github.sh
cp downtime_bot/.env.example downtime_bot/.env
nano downtime_bot/.env
bash downtime_bot/scripts/bootstrap_hetzner.sh
journalctl -u downtime_bot -f
```

If `downtime_bot/` is missing, use the root helper `scripts/pull_downtime_from_github.sh` first.

## Features

- Slash-commands only (`discord.py` app commands).
- Draft-first DM workflow in `#dm-drafts`.
- Multi-part session splitting with spreadsheet-equivalent rules.
- Player mention support through Discord user picker.
- JSON storage abstraction (`data/guild_<guild_id>.json`) ready for SQLite backend later.
- `/audit` self-tool for XP and DTP only.
- Auto split of long output into multiple Discord messages (2000 char limit safe).
- `/admin sync` for on-demand slash command resync.

## Requirements

- Python 3.12+
- Discord bot token

## Install (Windows 11)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with your bot values.

## Discord Developer Portal setup

1. Create an application + bot user.
2. Enable **Server Members Intent**.
3. Do **not** enable Message Content Intent (not required).
4. OAuth2 URL scopes:
   - `bot`
   - `applications.commands`
5. Grant needed bot permissions to send messages and use slash commands.

## Run

```bash
python bot.py
```

Expected startup log:

- `Commands synced to guild <id>` (default dev mode when `DISCORD_GUILD_ID` is set)
- or `Commands synced globally`

## Sync modes

- Default: `SYNC_MODE=guild` with `DISCORD_GUILD_ID` set for instant command updates.
- Optional: set `SYNC_MODE=global` (or unset `DISCORD_GUILD_ID`) for global sync.
- Admins can run `/admin sync` to force resync.

## DM permissions and channel constraints

DM tools are restricted to:

- Users with role named exactly `DM`.
- Channel named exactly `dm-drafts`.

Fallback if role `DM` does not exist:

- Server owner and users with **Manage Server** can use DM tools.

You can change names via `.env`.

## Commands

### Diagnostics

- `/ping` → `Pong` (ephemeral)
- `/admin sync` → admin-only slash command resync

### Player-facing

- `/audit level:<1-20> hours:<0.5-17.5>`
  - Shows per-part and total XP + DTP.

### DM workflow (`#dm-drafts` only)

- `/recap start`
- `/recap list`
- `/recap use`
- `/recap delete`
- `/recap part list`
- `/recap part set`
- `/recap player add`
- `/recap player edit` (modal)
- `/recap player remove`
- `/recap dm edit` (modal)
- `/recap narrative` (modal)
- `/recap preview`
- `/recap export`
- `/recap publish`

### Future stub

- `/listing generate` → "Not implemented yet"

## Rules and configuration tables

- `config/rules.example.json` holds:
  - `xp_per_hour`
  - `max_gp_by_level` (player GP hint table)
  - `dm_gp_suggestion_per_hour_by_level` (editable DM GP suggestion model)

To customize in production, copy to `config/rules.json` and edit values.

## Storage format

Each guild file:

- `data/guild_<guild_id>.json`
- Stores drafts, active draft pointers, per-part rewards, DM rewards, and narrative.

## Troubleshooting slash commands not appearing

1. Confirm startup log shows sync mode result.
2. Ensure bot invited with `applications.commands` scope.
3. Use `SYNC_MODE=guild` + `DISCORD_GUILD_ID` for instant test iteration.
4. Run `/admin sync` as admin.
5. Re-invite bot if scopes were changed after initial invite.
6. Confirm bot has access to target server/channel.

## Manual acceptance checklist

1. Start bot and verify `Commands synced to guild` (or global) in console.
2. In Discord, verify `/ping` appears and returns `Pong`.
3. In `#dm-drafts` as DM, `/recap start` creates draft with parts.
4. `/recap player add` stores member mention + player info; `/recap preview` computes XP and DTP.
5. `/audit` matches XP/hour table and DTP formula.
6. `/recap preview` splits long output across multiple messages when needed.
