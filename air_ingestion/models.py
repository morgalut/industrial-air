# air_ingestion/models.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field


MissingStrategy = Literal["drop", "fill", "interpolate"]


class ProcessingConfig(BaseModel):
    frequency: str = Field(default="5min")
    missing_strategy: MissingStrategy = Field(default="interpolate")
    fill_value: float = Field(default=0.0)
    flatline_window: int = Field(default=5)


class ColumnRule(BaseModel):
    name: str
    dtype: str
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None


class SensorSchema(BaseModel):
    columns: list[ColumnRule]


@dataclass(frozen=True)
class QualityIssue:
    column: str
    issue_type: str
    count: int
    message: str


@dataclass(frozen=True)
class QualityReport:
    row_count_before: int
    row_count_after: int
    missing_percent_by_column: dict[str, float]
    out_of_range_counts: dict[str, int]
    flatline_counts: dict[str, int]
    issues: list[QualityIssue]


@dataclass(frozen=True)
class IngestionResult:
    data: pd.DataFrame
    quality_report: QualityReport