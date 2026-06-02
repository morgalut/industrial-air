# air_ingestion/repository.py

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class AbstractSensorRepository(ABC):
    @abstractmethod
    def fetch_station_data(self, station_id: str) -> pd.DataFrame:
        raise NotImplementedError


class SQLiteSensorRepository(AbstractSensorRepository):
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def fetch_station_data(self, station_id: str) -> pd.DataFrame:
        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {self.db_path}")

        query = """
        SELECT
            timestamp,
            station_id,
            device_id,
            pressure_bar,
            flow_m3h,
            power_kw,
            rpm,
            temperature_c
        FROM sensor_readings
        WHERE station_id = ?
        ORDER BY timestamp ASC
        """

        with sqlite3.connect(self.db_path) as connection:
            return pd.read_sql_query(
                query,
                connection,
                params=(station_id,),
                parse_dates=["timestamp"],
            )