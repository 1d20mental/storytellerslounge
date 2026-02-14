#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/opt/storytellerslounge"
cd "$REPO_ROOT"

python3 -m venv downtime_bot/.venv
source downtime_bot/.venv/bin/activate
pip install --upgrade pip
pip install -r downtime_bot/requirements.txt

if [ ! -f downtime_bot/.env ]; then
  cp downtime_bot/.env.example downtime_bot/.env
  echo "Created downtime_bot/.env from template. Fill in DISCORD_TOKEN before starting service."
fi

install -m 644 downtime_bot/deploy/downtime_bot.service /etc/systemd/system/downtime_bot.service
systemctl daemon-reload
systemctl enable downtime_bot

echo "Bootstrap complete. Review downtime_bot/.env then run: systemctl restart downtime_bot"
