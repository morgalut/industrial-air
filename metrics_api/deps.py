# metrics_api/deps.py

from __future__ import annotations

from functools import lru_cache

from air_ingestion.engine import IngestionEngine
from air_ingestion.repository import SQLiteSensorRepository


@lru_cache
def get_ingestion_engine() -> IngestionEngine:
    repository = SQLiteSensorRepository("data/sensor_data.db")

    return IngestionEngine(
        repository=repository,
        schema_path="data/sensor_schema.json",
    )