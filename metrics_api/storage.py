# metrics_api/storage.py

from __future__ import annotations

from datetime import datetime


_METRICS_STORE: dict[str, dict] = {}


def save_station_metrics(
    station_id: str,
    metrics: list[dict],
    quality_report: dict,
) -> dict:
    stored_record = {
        "station_id": station_id,
        "processed_at": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "quality_report": quality_report,
    }

    _METRICS_STORE[station_id] = stored_record

    return stored_record


def get_station_metrics(station_id: str) -> dict | None:
    return _METRICS_STORE.get(station_id)