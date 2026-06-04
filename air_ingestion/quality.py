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
        counts[column] = 0

        if column not in df.columns:
            continue

        numeric_series = pd.to_numeric(df[column], errors="coerce")

        mask = pd.Series(False, index=df.index)

        if min_value is not None:
            mask = mask | (numeric_series < min_value)

        if max_value is not None:
            mask = mask | (numeric_series > max_value)

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

    if df.empty:
        return counts, issues

    for column in columns:
        if column not in df.columns:
            continue

        total_count = 0

        for _, device_df in df.sort_values("timestamp").groupby("device_id"):
            same_as_previous = (
                device_df[column].eq(device_df[column].shift())
                & device_df[column].notna()
                & device_df[column].ne(0)
            )

            flatline_points = (
                same_as_previous
                .rolling(window=window)
                .sum()
                .ge(window - 1)
            )

            total_count += int(flatline_points.fillna(False).sum())

        counts[column] = total_count

        if total_count > 0:
            issues.append(
                QualityIssue(
                    column=column,
                    issue_type="flatline",
                    count=total_count,
                    message=f"{column} has {total_count} possible flatline points",
                )
            )

    return counts, issues