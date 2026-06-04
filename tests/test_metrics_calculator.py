import pandas as pd

from metrics_api.calculator import compute_operational_metrics


def test_metrics_are_generated() -> None:
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2025-01-01",
                periods=10,
                freq="h",
            ),
            "device_id": ["device_1"] * 10,
            "pressure_bar": [7] * 10,
            "flow_m3h": [100] * 10,
            "power_kw": [25] * 10,
            "rpm": [1500] * 10,
            "temperature_c": [70] * 10,
        }
    )

    metrics = compute_operational_metrics(df)

    assert len(metrics) == 1

    assert metrics[0]["peak_pressure_bar"] == 7
    assert metrics[0]["uptime_percent"] == 100.0