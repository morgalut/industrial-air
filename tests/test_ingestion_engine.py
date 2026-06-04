import pandas as pd

from air_ingestion.engine import IngestionEngine
from air_ingestion.models import ProcessingConfig
from air_ingestion.repository import AbstractSensorRepository


class MockRepository(AbstractSensorRepository):
    def fetch_station_data(self, station_id: str) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "timestamp": pd.date_range(
                    "2025-01-01",
                    periods=20,
                    freq="min",
                ),
                "station_id": [station_id] * 20,
                "device_id": ["device_1"] * 20,
                "pressure_bar": [7.0] * 20,
                "flow_m3h": [100.0] * 20,
                "power_kw": [25.0] * 20,
                "rpm": [1500] * 20,
                "temperature_c": [70.0] * 20,
            }
        )


def test_engine_processes_data() -> None:
    engine = IngestionEngine(
        repository=MockRepository(),
        schema_path="data/sensor_schema.json",
    )

    result = engine.process_station_data(
        station_id="station",
        config=ProcessingConfig(),
    )

    assert not result.data.empty
    assert result.quality_report.row_count_before == 20