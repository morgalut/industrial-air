# metrics_api/main.py

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import Depends, FastAPI, HTTPException

from air_ingestion.engine import IngestionEngine
from air_ingestion.models import ProcessingConfig
from metrics_api.calculator import compute_operational_metrics
from metrics_api.deps import (
    get_ingestion_engine,
    get_summary_service,
)
from metrics_api.schemas import ProcessStationRequest
from metrics_api.storage import (
    get_station_metrics,
    save_station_metrics,
)
from metrics_api.summary_service import MetricsSummaryService

app = FastAPI(
    title="Industrial Air Metrics Service",
)


INGESTION_ENGINE_DEPENDENCY = Depends(
    get_ingestion_engine,
)

SUMMARY_SERVICE_DEPENDENCY = Depends(
    get_summary_service,
)


@app.get("/health")
def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
    }


@app.post("/api/v1/stations/{station_id}/process")
def process_station(
    station_id: str,
    request: ProcessStationRequest,
    engine: IngestionEngine = INGESTION_ENGINE_DEPENDENCY,
) -> dict[str, Any]:
    try:
        result = engine.process_station_data(
            station_id=station_id,
            config=ProcessingConfig(
                frequency=request.frequency,
                missing_strategy=request.missing_strategy,
                fill_value=request.fill_value,
                flatline_window=request.flatline_window,
            ),
        )

        metrics = compute_operational_metrics(
            result.data,
        )

        return save_station_metrics(
            station_id=station_id,
            metrics=metrics,
            quality_report=asdict(
                result.quality_report,
            ),
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Internal processing error",
        ) from error


@app.get("/api/v1/stations/{station_id}/metrics")
def read_station_metrics(
    station_id: str,
) -> dict[str, Any]:
    stored_metrics = get_station_metrics(
        station_id,
    )

    if stored_metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics found for station {station_id}",
        )

    return stored_metrics


@app.get("/api/v1/stations/{station_id}/summary")
def summarize_station_metrics(
    station_id: str,
    summary_service: MetricsSummaryService = SUMMARY_SERVICE_DEPENDENCY,
) -> dict[str, Any]:
    stored_metrics = get_station_metrics(
        station_id,
    )

    if stored_metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics found for station {station_id}",
        )

    try:
        return summary_service.generate_station_summary(
            stored_metrics,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error


@app.get("/api/v1/stations/{station_id}/quality-summary")
def summarize_station_quality(
    station_id: str,
    summary_service: MetricsSummaryService = SUMMARY_SERVICE_DEPENDENCY,
) -> dict[str, Any]:
    stored_metrics = get_station_metrics(
        station_id,
    )

    if stored_metrics is None:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics found for station {station_id}",
        )

    try:
        return summary_service.generate_quality_summary(
            stored_metrics,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error