# metrics_api/storage.py

from __future__ import annotations

from datetime import datetime
from typing import Any

MetricsRecord = dict[str, Any]

_METRICS_STORE: dict[str, MetricsRecord] = {}


def save_station_metrics(
    station_id: str,
    metrics: list[dict[str, Any]],
    quality_report: dict[str, Any],
) -> MetricsRecord:
    stored_record: MetricsRecord = {
        "station_id": station_id,
        "processed_at": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "quality_report": quality_report,
    }

    _METRICS_STORE[station_id] = stored_record

    return stored_record


def get_station_metrics(station_id: str) -> MetricsRecord | None:
    return _METRICS_STORE.get(station_id)