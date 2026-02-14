#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=${REPO_DIR:-/opt/storytellerslounge}
SERVICE_NAME=${SERVICE_NAME:-downtime_bot}
VENV_DIR=${VENV_DIR:-$REPO_DIR/downtime_bot/.venv}

cd "$REPO_DIR"

if [ ! -d "downtime_bot" ]; then
  echo "ERROR: downtime_bot folder not found in $REPO_DIR" >&2
  echo "Recover it first with scripts/pull_downtime_from_github.sh" >&2
  exit 1
fi

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install -r downtime_bot/requirements.txt

if [ ! -f "downtime_bot/.env" ]; then
  cp downtime_bot/.env.example downtime_bot/.env
  echo "Created downtime_bot/.env from template. Fill required values before starting service."
fi

PYTHONPATH=downtime_bot/src python -m compileall downtime_bot/src
python downtime_bot/scripts/check_repo_layout.py
PYTHONPATH=downtime_bot/src python downtime_bot/scripts/inspect_allowed_content.py

sudo cp downtime_bot/deploy/downtime_bot.service "/etc/systemd/system/${SERVICE_NAME}.service"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl --no-pager --full status "$SERVICE_NAME"

echo "Tail logs with: journalctl -u ${SERVICE_NAME} -f"
