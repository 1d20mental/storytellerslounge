from __future__ import annotations

import json
import os
from pathlib import Path

path = Path(
    os.getenv(
        "ALLOWED_CONTENT_PATH",
        "data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json",
    )
)

if not path.exists():
    print(f"allowed content file not found: {path}")
    raise SystemExit(0)

with path.open("r", encoding="utf-8") as handle:
    data = json.load(handle)

if isinstance(data, dict):
    print(f"allowed content loaded: {len(data)} top-level keys")
else:
    print("allowed content loaded")
