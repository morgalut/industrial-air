# air_ingestion/schema.py

from __future__ import annotations

import json
from pathlib import Path

from air_ingestion.models import ColumnRule, SensorSchema


def load_sensor_schema(schema_path: str | Path) -> SensorSchema:
    path = Path(schema_path)

    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw_schema = json.load(file)

    columns: list[ColumnRule] = []

    for column_name, rules in raw_schema.get("columns", {}).items():
        columns.append(
            ColumnRule(
                name=column_name,
                dtype=rules.get("type", "string"),
                required=rules.get("required", True),
                min_value=rules.get("min"),
                max_value=rules.get("max"),
            )
        )

    return SensorSchema(columns=columns)