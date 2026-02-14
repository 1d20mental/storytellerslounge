from __future__ import annotations

import logging
from pathlib import Path

from downtime_bot.core.allowed_content_loader import load_allowed_content


logging.basicConfig(level=logging.INFO)


def main() -> None:
    path = Path("data/allowed_content/allowed_content_downtime_bastions_2025-12-28.json")
    index = load_allowed_content(path)
    print("Loaded allowed content JSON")
    print(f"downtime activities: {len(index.activities_by_key)}")
    print(f"bastion facilities: {len(index.facilities_by_key)}")
    print(f"top-level keys: {', '.join(index.data.keys())}")


if __name__ == "__main__":
    main()
