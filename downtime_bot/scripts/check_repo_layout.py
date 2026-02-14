from __future__ import annotations

from pathlib import Path

REQUIRED_PATHS = [
    Path("downtime_bot/src/downtime_bot/bot.py"),
    Path("downtime_bot/deploy/downtime_bot.service"),
    Path("downtime_bot/.env.example"),
]

missing = [str(path) for path in REQUIRED_PATHS if not path.exists()]
if missing:
    raise SystemExit("Missing required files: " + ", ".join(missing))

print("downtime_bot layout ok")
