import pandas as pd

from air_ingestion.quality import (
    calculate_missing_percent,
    detect_flatlines,
)


def test_missing_percentage() -> None:
    df = pd.DataFrame(
        {
            "a": [1, None, 3, None],
        }
    )

    result = calculate_missing_percent(df)

    assert result["a"] == 50.0


def test_flatline_detection() -> None:
    df = pd.DataFrame(
        {
            "device_id": ["d1"] * 10,
            "timestamp": pd.date_range(
                "2025-01-01",
                periods=10,
                freq="min",
            ),
            "rpm": [100, 100, 100, 100, 100, 101, 102, 103, 104, 105],
        }
    )

    counts, _ = detect_flatlines(
        df,
        columns=["rpm"],
        window=5,
    )

    assert counts["rpm"] > 0