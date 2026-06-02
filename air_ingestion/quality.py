# air_ingestion/quality.py

from __future__ import annotations

import pandas as pd

from air_ingestion.models import QualityIssue


def calculate_missing_percent(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {}

    return {
        column: round(float(df[column].isna().mean() * 100), 2)
        for column in df.columns
    }


def detect_out_of_range(
    df: pd.DataFrame,
    ranges: dict[str, tuple[float | None, float | None]],
) -> tuple[dict[str, int], list[QualityIssue]]:
    counts: dict[str, int] = {}
    issues: list[QualityIssue] = []

    for column, (min_value, max_value) in ranges.items():
        if column not in df.columns:
            continue

        mask = pd.Series(False, index=df.index)

        if min_value is not None:
            mask = mask | (df[column] < min_value)

        if max_value is not None:
            mask = mask | (df[column] > max_value)

        count = int(mask.sum())
        counts[column] = count

        if count > 0:
            issues.append(
                QualityIssue(
                    column=column,
                    issue_type="out_of_range",
                    count=count,
                    message=f"{column} has {count} values outside allowed range",
                )
            )

    return counts, issues


def detect_flatlines(
    df: pd.DataFrame,
    columns: list[str],
    window: int,
) -> tuple[dict[str, int], list[QualityIssue]]:
    counts: dict[str, int] = {}
    issues: list[QualityIssue] = []

    for column in columns:
        if column not in df.columns:
            continue

        same_as_previous = df[column].eq(df[column].shift())
        flatline_points = same_as_previous.rolling(window=window).sum() >= window - 1
        count = int(flatline_points.fillna(False).sum())

        counts[column] = count

        if count > 0:
            issues.append(
                QualityIssue(
                    column=column,
                    issue_type="flatline",
                    count=count,
                    message=f"{column} has {count} possible flatline points",
                )
            )

    return counts, issues