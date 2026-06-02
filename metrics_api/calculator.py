# metrics_api/calculator.py

from __future__ import annotations

import pandas as pd


def compute_operational_metrics(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    results: list[dict] = []

    for device_id, device_df in df.groupby("device_id"):
        active_mask = (device_df["rpm"] > 100) & (device_df["power_kw"] > 0)

        uptime_percent = round(float(active_mask.mean() * 100), 2)
        average_pressure = round(float(device_df["pressure_bar"].mean()), 3)
        peak_pressure = round(float(device_df["pressure_bar"].max()), 3)

        total_power = float(device_df.loc[active_mask, "power_kw"].sum())
        total_flow = float(device_df.loc[active_mask, "flow_m3h"].sum())
        specific_power = round(total_power / total_flow, 6) if total_flow > 0 else None

        cycle_count = int(active_mask.astype(int).diff().eq(1).sum())

        total_flow_volume = _calculate_total_flow_volume(device_df)

        results.append(
            {
                "device_id": str(device_id),
                "uptime_percent": uptime_percent,
                "average_pressure_bar": average_pressure,
                "peak_pressure_bar": peak_pressure,
                "specific_power_kw_per_m3h": specific_power,
                "cycle_count": cycle_count,
                "total_flow_volume_m3": total_flow_volume,
            }
        )

    return results


def _calculate_total_flow_volume(df: pd.DataFrame) -> float:
    sorted_df = df.sort_values("timestamp").copy()

    time_delta_hours = (
        sorted_df["timestamp"]
        .diff()
        .dt.total_seconds()
        .div(3600)
        .fillna(0)
    )

    volume = sorted_df["flow_m3h"] * time_delta_hours

    return round(float(volume.sum()), 3)