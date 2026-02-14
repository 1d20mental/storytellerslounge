# Downtime Bot

Downtime Bot is a standalone Discord slash-command service deployed from `/opt/storytellerslounge`. This repo also contains other bots.

## Hetzner deploy (systemd)

1. SSH to server and move to repo root:
   ```bash
   cd /opt/storytellerslounge
   ```
2. If the `downtime_bot/` folder is missing, recover it:
   ```bash
   bash scripts/pull_downtime_from_github.sh
   ```
3. Bootstrap virtualenv and install systemd unit:
   ```bash
   bash downtime_bot/scripts/bootstrap_hetzner.sh
   ```
4. Configure environment values:
   ```bash
   cp downtime_bot/.env.example downtime_bot/.env
   nano downtime_bot/.env
   ```
5. Start service:
   ```bash
   sudo systemctl restart downtime_bot
   sudo systemctl status downtime_bot --no-pager
   ```

## Commands

- `/ping` diagnostic response.
- `/about` runtime configuration and health snapshot.
- `/admin sync` admin-only slash command resync.
- `/downtime_log` append-only ledger entry with embed output.

## Environment

`downtime_bot/.env` supports:

- `DISCORD_TOKEN`
- `DISCORD_GUILD_ID`
- `STAFF_LOG_CHANNEL_ID`
- `DOWNTIME_LEDGER_CHANNEL_ID`
- `DOWNTIME_DB_PATH`
- `ALLOWED_CONTENT_PATH`
- `SYNC_MODE`
