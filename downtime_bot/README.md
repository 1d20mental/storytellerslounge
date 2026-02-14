# Downtime Bot MVP

This subfolder contains an isolated Python downtime bot implementation.

## Scope and architecture
- All downtime-bot code lives under `downtime_bot/`.
- Core services are under `downtime_bot/src/downtime_bot/core`.
- Module plugins register via `setup(core)` under `downtime_bot/src/downtime_bot/modules`.
- Ledger is append-only (immutable transaction rows only).
- `1 DTP = 1 work day`.

## Authoritative rules source
The bot reads downtime activity/facility data from:

`data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json`

Bootstrap and validation scripts fail fast if this file is missing/unreadable.

## Hetzner deployment (systemd)

1) Ensure `downtime_bot/` exists in your checkout:
```bash
cd /opt/storytellerslounge
git fetch --all --prune
git checkout main
git pull
ls -la downtime_bot
```

If missing, recover it from GitHub using the **root-level** helper that still works when `downtime_bot/` is absent:
```bash
cd /opt/storytellerslounge
REPO_URL=git@github.com:<ORG>/<REPO>.git REF=main bash scripts/pull_downtime_from_github.sh
ls -la downtime_bot
```

2) Configure env:
```bash
cp downtime_bot/.env.example downtime_bot/.env
nano downtime_bot/.env
```

3) Bootstrap install + service:
```bash
bash downtime_bot/scripts/bootstrap_hetzner.sh
```

4) Follow logs:
```bash
journalctl -u downtime_bot -f
```

## What bootstrap does
`downtime_bot/scripts/bootstrap_hetzner.sh` performs:
- creates venv at `downtime_bot/.venv`
- `pip install -r downtime_bot/requirements.txt`
- `PYTHONPATH=downtime_bot/src python -m compileall downtime_bot/src`
- layout + allowed-content validation
- installs systemd unit to `/etc/systemd/system/downtime_bot.service`
- `daemon-reload`, `enable`, `restart`
- prints the exact `journalctl` tail command

## Minimal command surface
Implemented minimum slash commands include:
- `/char register`
- `/char select`
- `/dtp balance`

Additional MVP commands for transactions/awards and project workflow are also included.
