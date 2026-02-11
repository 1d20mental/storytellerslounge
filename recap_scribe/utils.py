from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP


def round_half_step(hours: float) -> float:
    rounded = round(hours * 2) / 2
    return clamp_hours(rounded)


def clamp_hours(hours: float) -> float:
    return max(0.5, min(17.5, hours))


def excel_round(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def split_hours(total_hours: float) -> list[float]:
    h = round_half_step(total_hours)
    if h < 6.0:
        return [h]
    if h < 9.0:
        return [3.0, h - 3.0]
    if h < 12.0:
        return [3.0, 3.0, h - 6.0]
    if h < 15.0:
        return [3.0, 3.0, 3.0, h - 9.0]
    return [3.0, 3.0, 3.0, 3.0, h - 12.0]


def apl_and_tier(levels: list[int]) -> tuple[int, int]:
    if not levels:
        return 1, 1
    apl = excel_round(sum(levels) / len(levels))
    if apl <= 4:
        return apl, 1
    if apl <= 10:
        return apl, 2
    if apl <= 16:
        return apl, 3
    return apl, 4


def dtp_for_hours(hours: float) -> int:
    return math.floor(hours * 5)


def split_discord_messages(text: str, limit: int = 2000) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(line) <= limit:
                current = line
            else:
                for i in range(0, len(line), limit):
                    chunks.append(line[i : i + limit])
                current = ""
    if current:
        chunks.append(current)
    return chunks
