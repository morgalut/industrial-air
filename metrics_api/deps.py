# metrics_api/deps.py

from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv

from air_ingestion.engine import IngestionEngine
from air_ingestion.repository import SQLiteSensorRepository
from metrics_api.llm_provider import AbstractLLMProvider, OpenAILLMProvider
from metrics_api.summary_service import MetricsSummaryService

load_dotenv()


@lru_cache
def get_ingestion_engine() -> IngestionEngine:
    repository = SQLiteSensorRepository("data/sensor_data.db")

    return IngestionEngine(
        repository=repository,
        schema_path="data/sensor_schema.json",
    )


@lru_cache
def get_llm_provider() -> AbstractLLMProvider:
    return OpenAILLMProvider()


@lru_cache
def get_summary_service() -> MetricsSummaryService:
    return MetricsSummaryService(llm_provider=get_llm_provider())