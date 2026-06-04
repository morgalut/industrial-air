# air_ingestion/schema.py

from __future__ import annotations

import json
from pathlib import Path

from air_ingestion.models import ColumnRule, SensorSchema, SensorTypeRule

COLUMN_ALIASES = {
    "timestamp": "timestamp",
    "station_id": "station_id",
    "device_id": "device_id",
    "discharge_pressure": "pressure_bar",
    "air_flow_rate": "flow_m3h",
    "power_consumption": "power_kw",
    "motor_speed": "rpm",
    "discharge_temp": "temperature_c",
}


def load_sensor_schema(schema_path: str | Path) -> SensorSchema:
    path = Path(schema_path)

    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw_schema = json.load(file)

    sensor_readings = raw_schema["tables"]["sensor_readings"]
    raw_columns = sensor_readings["columns"]

    columns: list[ColumnRule] = []

    for source_name, rules in raw_columns.items():
        valid_range = rules.get("valid_range", {})

        columns.append(
            ColumnRule(
                source_name=source_name,
                canonical_name=COLUMN_ALIASES.get(source_name, source_name),
                dtype=rules.get("type", "string"),
                required=rules.get("required", True),
                unit=rules.get("unit"),
                min_value=valid_range.get("min"),
                max_value=valid_range.get("max"),
            )
        )

    sensor_types: dict[str, SensorTypeRule] = {}

    for source_name, rules in raw_schema.get("sensor_types", {}).items():
        typical_range = rules.get("typical_operating_range", {})

        canonical_name = COLUMN_ALIASES.get(source_name, source_name)

        sensor_types[canonical_name] = SensorTypeRule(
            source_name=source_name,
            canonical_name=canonical_name,
            category=rules.get("category"),
            typical_min=typical_range.get("min"),
            typical_max=typical_range.get("max"),
            flatline_threshold_minutes=rules.get("flatline_threshold_minutes"),
            description=rules.get("description"),
        )

    return SensorSchema(
        version=raw_schema.get("version", "unknown"),
        columns=columns,
        sensor_types=sensor_types,
    )