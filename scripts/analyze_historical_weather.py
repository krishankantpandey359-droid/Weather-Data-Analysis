"""Analyze a downloaded Open-Meteo ERA5 daily weather CSV."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "Date", "Temperature_Mean_C", "Temperature_Max_C", "Temperature_Min_C",
    "Humidity_Mean_Percent", "Precipitation_Sum_mm", "Wind_Speed_Max_kmh",
}
NUMERIC_COLUMNS = sorted(REQUIRED_COLUMNS - {"Date"})


def analyze_historical_weather(data_path: str | Path, output_dir: str | Path):
    data_path = Path(data_path)
    output_dir = Path(output_dir)
    if not data_path.is_file():
        raise FileNotFoundError(f"Historical weather CSV not found: {data_path}")
    frame = pd.read_csv(data_path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Historical weather CSV is missing columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Historical weather CSV is empty")

    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Historical weather CSV contains missing or invalid values")
    if not np.isfinite(frame[NUMERIC_COLUMNS].to_numpy(dtype=float)).all():
        raise ValueError("Historical weather CSV contains non-finite numeric values")
    if frame["Date"].duplicated().any():
        raise ValueError("Historical weather CSV contains duplicate dates")
    if not frame["Humidity_Mean_Percent"].between(0, 100).all():
        raise ValueError("Humidity must be between 0 and 100 percent")
    if (frame["Precipitation_Sum_mm"] < 0).any():
        raise ValueError("Precipitation cannot be negative")
    if (frame["Wind_Speed_Max_kmh"] < 0).any():
        raise ValueError("Wind speed cannot be negative")
    if (
        (frame["Temperature_Min_C"] > frame["Temperature_Mean_C"]).any()
        or (frame["Temperature_Mean_C"] > frame["Temperature_Max_C"]).any()
    ):
        raise ValueError("Temperature minimum, mean and maximum values are inconsistent")

    frame = frame.sort_values("Date").reset_index(drop=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    monthly = frame.assign(
        Month=frame["Date"].dt.to_period("M").astype(str)
    ).groupby("Month").agg(
        mean_temperature_c=("Temperature_Mean_C", "mean"),
        max_temperature_c=("Temperature_Max_C", "mean"),
        min_temperature_c=("Temperature_Min_C", "mean"),
        mean_humidity_percent=("Humidity_Mean_Percent", "mean"),
        precipitation_total_mm=("Precipitation_Sum_mm", "sum"),
        mean_wind_speed_max_kmh=("Wind_Speed_Max_kmh", "mean"),
        observed_days=("Date", "count"),
    ).reset_index()
    monthly.to_csv(output_dir / "monthly_weather_summary.csv", index=False)

    date_index = pd.date_range(frame["Date"].min(), frame["Date"].max(), freq="D")
    missing_dates = date_index.difference(pd.DatetimeIndex(frame["Date"]))
    summary = {
        "records": int(len(frame)),
        "date_start": frame["Date"].min().date().isoformat(),
        "date_end": frame["Date"].max().date().isoformat(),
        "calendar_days": int(len(date_index)),
        "missing_calendar_days": [date.date().isoformat() for date in missing_dates],
        "calendar_coverage_percent": round(len(frame) / len(date_index) * 100, 2),
        "mean_temperature_c": round(float(frame["Temperature_Mean_C"].mean()), 2),
        "mean_humidity_percent": round(float(frame["Humidity_Mean_Percent"].mean()), 2),
        "total_precipitation_mm": round(float(frame["Precipitation_Sum_mm"].sum()), 2),
        "mean_max_wind_speed_kmh": round(float(frame["Wind_Speed_Max_kmh"].mean()), 2),
        "rainy_days_at_least_1mm": int(frame["Precipitation_Sum_mm"].ge(1).sum()),
        "analysis_type": "descriptive historical reanalysis summary, not a forecast",
        "source": "Open-Meteo Historical Weather API, ERA5",
        "input_file": data_path.name,
    }
    (output_dir / "historical_weather_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(frame["Date"], frame["Temperature_Mean_C"], label="Daily mean")
    ax.fill_between(
        frame["Date"], frame["Temperature_Min_C"], frame["Temperature_Max_C"],
        alpha=0.2, label="Daily min-max range",
    )
    ax.set(title="Historical Daily Temperature", xlabel="Date", ylabel="Temperature (°C)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / "historical_temperature_trend.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(frame["Date"], frame["Precipitation_Sum_mm"])
    ax.set(title="Daily Precipitation", xlabel="Date", ylabel="Precipitation (mm)")
    fig.tight_layout()
    fig.savefig(output_dir / "historical_precipitation.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(monthly["Month"], monthly["precipitation_total_mm"], marker="o")
    ax.set(title="Monthly Total Precipitation", xlabel="Month", ylabel="Precipitation (mm)")
    ax.tick_params(axis="x", labelrotation=60)
    fig.tight_layout()
    fig.savefig(output_dir / "monthly_precipitation.png")
    plt.close(fig)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="CSV created by download_historical_weather.py")
    parser.add_argument("--output-dir", default="outputs/historical")
    args = parser.parse_args()
    result = analyze_historical_weather(args.data, args.output_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
