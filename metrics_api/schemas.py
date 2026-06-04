from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProcessStationRequest(BaseModel):
    frequency: str = Field(default="5min")
    missing_strategy: Literal["drop", "fill", "interpolate"] = Field(
        default="interpolate"
    )
    fill_value: float = Field(default=0.0)
    flatline_window: int | None = Field(default=5, ge=2)