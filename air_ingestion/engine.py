# air_ingestion/engine.py

from __future__ import annotations

import pandas as pd

from air_ingestion.models import IngestionResult, ProcessingConfig, QualityReport
from air_ingestion.quality import (
    calculate_missing_percent,
    detect_flatlines,
    detect_out_of_range,
)
from air_ingestion.repository import AbstractSensorRepository
from air_ingestion.schema import load_sensor_schema


class IngestionEngine:
    def __init__(
        self,
        repository: AbstractSensorRepository,
        schema_path: str,
    ) -> None:
        self.repository = repository
        self.schema = load_sensor_schema(schema_path)

    def process_station_data(
        self,
        station_id: str,
        config: ProcessingConfig | None = None,
    ) -> IngestionResult:
        config = config or ProcessingConfig()

        raw_df = self.repository.fetch_station_data(station_id)
        row_count_before = len(raw_df)

        self._validate_required_columns(raw_df)

        missing_percent = calculate_missing_percent(raw_df)

        ranges = {
            rule.name: (rule.min_value, rule.max_value)
            for rule in self.schema.columns
            if rule.min_value is not None or rule.max_value is not None
        }

        out_of_range_counts, range_issues = detect_out_of_range(raw_df, ranges)

        numeric_columns = [
            "pressure_bar",
            "flow_m3h",
            "power_kw",
            "rpm",
            "temperature_c",
        ]

        flatline_counts, flatline_issues = detect_flatlines(
            raw_df,
            columns=numeric_columns,
            window=config.flatline_window,
        )

        clean_df = self._clean(raw_df, config)
        clean_df = self._resample(clean_df, config.frequency)

        report = QualityReport(
            row_count_before=row_count_before,
            row_count_after=len(clean_df),
            missing_percent_by_column=missing_percent,
            out_of_range_counts=out_of_range_counts,
            flatline_counts=flatline_counts,
            issues=[*range_issues, *flatline_issues],
        )

        return IngestionResult(data=clean_df, quality_report=report)

    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        required_columns = {
            rule.name
            for rule in self.schema.columns
            if rule.required
        }

        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    def _clean(
        self,
        df: pd.DataFrame,
        config: ProcessingConfig,
    ) -> pd.DataFrame:
        clean_df = df.copy()

        clean_df["timestamp"] = pd.to_datetime(clean_df["timestamp"], errors="coerce")
        clean_df = clean_df.dropna(subset=["timestamp"])
        clean_df = clean_df.sort_values("timestamp")

        numeric_columns = [
            "pressure_bar",
            "flow_m3h",
            "power_kw",
            "rpm",
            "temperature_c",
        ]

        for column in numeric_columns:
            clean_df[column] = pd.to_numeric(clean_df[column], errors="coerce")

        if config.missing_strategy == "drop":
            clean_df = clean_df.dropna()

        elif config.missing_strategy == "fill":
            clean_df[numeric_columns] = clean_df[numeric_columns].fillna(config.fill_value)

        elif config.missing_strategy == "interpolate":
            clean_df[numeric_columns] = clean_df[numeric_columns].interpolate(
                method="linear",
                limit_direction="both",
            )

        return clean_df

    def _resample(
        self,
        df: pd.DataFrame,
        frequency: str,
    ) -> pd.DataFrame:
        if df.empty:
            return df

        df = df.set_index("timestamp")

        grouped = (
            df.groupby(["station_id", "device_id"])
            .resample(frequency)
            .agg(
                {
                    "pressure_bar": "mean",
                    "flow_m3h": "mean",
                    "power_kw": "mean",
                    "rpm": "mean",
                    "temperature_c": "mean",
                }
            )
            .reset_index()
        )

        return grouped