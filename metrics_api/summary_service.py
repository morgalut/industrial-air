from __future__ import annotations

import json
from typing import Any

from langsmith import traceable

from metrics_api.llm_provider import AbstractLLMProvider

StationRecord = dict[str, Any]


class MetricsSummaryService:
    def __init__(self, llm_provider: AbstractLLMProvider) -> None:
        self.llm_provider = llm_provider

    @traceable(name="generate_metrics_summary", run_type="chain")
    def generate_station_summary(self, station_record: StationRecord) -> StationRecord:
        prompt = self._build_summary_prompt(station_record)
        summary = self.llm_provider.generate(prompt)

        return {
            "station_id": station_record["station_id"],
            "processed_at": station_record["processed_at"],
            "summary": summary,
        }

    @traceable(name="generate_quality_summary", run_type="chain")
    def generate_quality_summary(self, station_record: StationRecord) -> StationRecord:
        prompt = self._build_quality_prompt(station_record)
        summary = self.llm_provider.generate(prompt)

        return {
            "station_id": station_record["station_id"],
            "processed_at": station_record["processed_at"],
            "summary": summary,
        }

    def _build_summary_prompt(self, station_record: StationRecord) -> str:
        safe_payload: StationRecord = {
            "station_id": station_record.get("station_id"),
            "processed_at": station_record.get("processed_at"),
            "metrics": station_record.get("metrics", []),
        }

        return (
            "Create a plain-English operational health summary for this station.\n"
            "Explain uptime, pressure, efficiency, cycle counts, and flow volume.\n"
            "Mention risks only if supported by the data.\n\n"
            f"DATA:\n{json.dumps(safe_payload, indent=2)}"
        )

    def _build_quality_prompt(self, station_record: StationRecord) -> str:
        safe_payload: StationRecord = {
            "station_id": station_record.get("station_id"),
            "processed_at": station_record.get("processed_at"),
            "quality_report": station_record.get("quality_report", {}),
        }

        return (
            "Create a plain-English data quality report for this station.\n"
            "Explain missing values, out-of-range values, flatlines, and whether "
            "the data appears reliable for metrics computation.\n"
            "Do not invent exact timestamps if they are not present.\n\n"
            f"DATA:\n{json.dumps(safe_payload, indent=2)}"
        )