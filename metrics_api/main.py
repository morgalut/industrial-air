# metrics_api/main.py

from __future__ import annotations

from dataclasses import asdict

from fastapi import Depends, FastAPI, HTTPException

from air_ingestion.engine import IngestionEngine
from air_ingestion.models import ProcessingConfig
from metrics_api.calculator import compute_operational_metrics
from metrics_api.deps import get_ingestion_engine
from metrics_api.schemas import ProcessStationRequest
from metrics_api.storage import get_station_metrics, save_station_metrics


app = FastAPI(title="Industrial Air Metrics Service")


@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy"}


@app.post("/api/v1/stations/{station_id}/process")
def process_station(
    station_id: str,
    request: ProcessStationRequest,
    engine: IngestionEngine = Depends(get_ingestion_engine),
) -> dict:
    try:
        result = engine.process_station_data(
            station_id=station_id,
            config=ProcessingConfig(
                frequency=request.frequency,
                missing_strategy=request.missing_strategy,  # type: ignore[arg-type]
                fill_value=request.fill_value,
                flatline_window=request.flatline_window,
            ),
        )

        metrics = compute_operational_metrics(result.data)

        return save_station_metrics(
            station_id=station_id,
            metrics=metrics,
            quality_report=asdict(result.quality_report),
        )

    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/v1/stations/{station_id}/metrics")
def read_station_metrics(station_id: str) -> dict:
    stored_metrics = get_station_metrics(station_id)

    if stored_metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics found for station {station_id}",
        )

    return stored_metrics