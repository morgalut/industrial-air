from metrics_api.llm_provider import AbstractLLMProvider
from metrics_api.summary_service import MetricsSummaryService


class MockLLMProvider(AbstractLLMProvider):
    def generate(self, prompt: str) -> str:
        assert "DATA:" in prompt
        return "Mocked station summary."


def test_summary_service_uses_llm_provider() -> None:
    service = MetricsSummaryService(llm_provider=MockLLMProvider())

    result = service.generate_station_summary(
        {
            "station_id": "station_1",
            "processed_at": "2026-06-04T00:00:00",
            "metrics": [
                {
                    "device_id": "device_1",
                    "uptime_percent": 90.0,
                    "average_pressure_bar": 7.5,
                }
            ],
        }
    )

    assert result["station_id"] == "station_1"
    assert result["summary"] == "Mocked station summary."