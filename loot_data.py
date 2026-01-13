import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


REQUIRED_BASE_COLUMNS = {"item_id", "name", "category", "subtype"}
REQUIRED_LOOT_COLUMNS = {"item_id", "rarity"}


@dataclass
class LootItem:
    item_id: str
    name: str
    category: str
    subtype: str
    rarity: str
    tags: List[str]

    @property
    def category_norm(self) -> str:
        return self.category.strip().lower()

    @property
    def rarity_norm(self) -> str:
        return self.rarity.strip().lower()

    @property
    def subtype_norm(self) -> str:
        return self.subtype.strip().lower()


class LootDataError(RuntimeError):
    pass


class LootDataStore:
    def __init__(self, base_path: Path, loot_path: Path) -> None:
        self.base_path = base_path
        self.loot_path = loot_path
        self.items: List[LootItem] = []
        self.has_tags: bool = False

    def load(self) -> None:
        base_rows = self._read_csv(self.base_path)
        loot_rows = self._read_csv(self.loot_path)

        self._validate_columns(self.base_path, base_rows, REQUIRED_BASE_COLUMNS)
        self._validate_columns(self.loot_path, loot_rows, REQUIRED_LOOT_COLUMNS)

        base_by_id = {row["item_id"]: row for row in base_rows}
        tags_column = self._find_tags_column(base_rows, loot_rows)
        self.has_tags = tags_column is not None

        items: List[LootItem] = []
        missing_ids = []
        for row in loot_rows:
            item_id = row["item_id"]
            base_row = base_by_id.get(item_id)
            if not base_row:
                missing_ids.append(item_id)
                continue
            if tags_column and tags_column in base_row:
                raw_tags = base_row.get(tags_column)
            elif tags_column:
                raw_tags = row.get(tags_column)
            else:
                raw_tags = None
            tags = self._parse_tags(raw_tags)
            items.append(
                LootItem(
                    item_id=item_id,
                    name=base_row["name"],
                    category=base_row["category"],
                    subtype=base_row.get("subtype", ""),
                    rarity=row.get("rarity", ""),
                    tags=tags,
                )
            )

        if missing_ids:
            preview = ", ".join(missing_ids[:5])
            raise LootDataError(
                "Items_loot.csv contains item_id values that do not appear in Items_base.csv: "
                f"{preview}"
                + ("..." if len(missing_ids) > 5 else "")
            )

        self.items = items

    def _read_csv(self, path: Path) -> List[Dict[str, str]]:
        if not path.exists():
            raise LootDataError(f"Missing required file: {path}")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise LootDataError(f"CSV file has no header row: {path}")
            return list(reader)

    def _validate_columns(
        self,
        path: Path,
        rows: List[Dict[str, str]],
        required: Iterable[str],
    ) -> None:
        if not rows:
            raise LootDataError(f"CSV file is empty: {path}")
        available = set(rows[0].keys())
        missing = set(required) - available
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise LootDataError(
                f"CSV file {path} is missing required columns: {missing_list}"
            )

    def _find_tags_column(
        self,
        base_rows: List[Dict[str, str]],
        loot_rows: List[Dict[str, str]],
    ) -> Optional[str]:
        candidate_columns = ["tags", "tag", "item_tags"]
        available = set(base_rows[0].keys()) | set(loot_rows[0].keys())
        for column in candidate_columns:
            if column in available:
                return column
        return None

    def _parse_tags(self, raw_value: Optional[str]) -> List[str]:
        if not raw_value:
            return []
        return [tag.strip().lower() for tag in raw_value.split(",") if tag.strip()]
