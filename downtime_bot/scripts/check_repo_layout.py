#!/usr/bin/env python3
"""Validate downtime bot file placement and required authoritative JSON path."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOWNTIME_DIR = REPO_ROOT / "downtime_bot"
ALLOWED_CONTENT_FILE = (
    REPO_ROOT
    / "data"
    / "allowed_content"
    / "allowed_content_downtime_bastions_2025-12-28.json"
)


def git_tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [Path(line) for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    if not DOWNTIME_DIR.exists():
        print("ERROR: downtime_bot/ directory is missing from this revision.")
        return 1

    files = git_tracked_files()
    misplaced = [
        path
        for path in files
        if "downtime_bot" in path.as_posix().split("/") and not path.as_posix().startswith("downtime_bot/")
    ]

    if misplaced:
        print("ERROR: Found downtime bot package files outside downtime_bot/:")
        for path in misplaced:
            print(f"  - {path}")
        return 1

    if not ALLOWED_CONTENT_FILE.exists():
        print(f"ERROR: Missing authoritative allowed content file: {ALLOWED_CONTENT_FILE}")
        return 1

    print("Downtime bot layout check passed.")
    print("- downtime_bot/ exists")
    print("- no downtime_bot package files are mixed outside downtime_bot/")
    print(f"- authoritative JSON exists at {ALLOWED_CONTENT_FILE.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
