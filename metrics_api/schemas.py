# metrics_api/schemas.py

from __future__ import annotations

from pydantic import BaseModel, Field


class ProcessStationRequest(BaseModel):
    frequency: str = Field(default="5min")
    missing_strategy: str = Field(default="interpolate")
    fill_value: float = Field(default=0.0)
    flatline_window: int = Field(default=5)