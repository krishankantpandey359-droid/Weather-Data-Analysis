from pathlib import Path
import argparse
import csv
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"Date", "Temperature", "Humidity", "Rainfall", "Weather"}


def run_analysis(data_path=None, output_dir=None, show=False):
    """Load weather observations, validate them, and export charts and summary."""
    project_dir = Path(__file__).resolve().parent
    csv_path = Path(data_path) if data_path else project_dir / "weather.csv"
    destination = Path(output_dir) if output_dir else project_dir

    if not csv_path.is_file():
        raise FileNotFoundError(f"Weather dataset not found: {csv_path}")

    # Check the raw header before pandas silently renames duplicate columns.
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source_file:
        try:
            raw_header = next(csv.reader(source_file))
        except StopIteration as exc:
            raise ValueError("Weather dataset is empty") from exc
    normalized_header = [str(name).strip() for name in raw_header]
    if not normalized_header or any(not name for name in normalized_header):
        raise ValueError("Weather dataset contains blank column names")
    if len(normalized_header) != len(set(normalized_header)):
        duplicates = sorted({name for name in normalized_header if normalized_header.count(name) > 1})
        raise ValueError(f"Weather dataset contains duplicate column names: {duplicates}")

    df = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")
    if df.empty:
        raise ValueError("Weather dataset is empty")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for column in ("Temperature", "Humidity", "Rainfall"):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    required = ["Date", "Temperature", "Humidity", "Rainfall", "Weather"]
    if df[required].isna().any().any():
        raise ValueError("Weather dataset contains missing or invalid required values")
    numeric = df[["Temperature", "Humidity", "Rainfall"]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("Weather dataset contains infinite numeric values")
    if not df["Humidity"].between(0, 100).all():
        raise ValueError("Humidity values must be between 0 and 100 percent")
    if (df["Rainfall"] < 0).any():
        raise ValueError("Rainfall values cannot be negative")
    df["Weather"] = df["Weather"].astype(str).str.strip().str.title()
    if df["Weather"].eq("").any():
        raise ValueError("Weather descriptions must not be blank")
    if df["Date"].dt.normalize().duplicated().any():
        raise ValueError("Weather dataset contains duplicate calendar dates")

    df = df.sort_values("Date").reset_index(drop=True)
    destination.mkdir(parents=True, exist_ok=True)
    date_range = pd.date_range(df["Date"].min().normalize(), df["Date"].max().normalize(), freq="D")
    observed_dates = pd.DatetimeIndex(df["Date"].dt.normalize().unique())
    missing_dates = date_range.difference(observed_dates)
    rainy_days = int(df["Rainfall"].gt(0).sum())
    weather_days = {
        str(key): int(value)
        for key, value in df["Weather"].value_counts().sort_index().items()
    }

    summary = {
        "records": int(len(df)),
        "date_start": df["Date"].min().date().isoformat(),
        "date_end": df["Date"].max().date().isoformat(),
        "average_temperature_c": round(float(df["Temperature"].mean()), 2),
        "median_temperature_c": round(float(df["Temperature"].median()), 2),
        "minimum_temperature_c": round(float(df["Temperature"].min()), 2),
        "maximum_temperature_c": round(float(df["Temperature"].max()), 2),
        "average_humidity_percent": round(float(df["Humidity"].mean()), 2),
        "minimum_humidity_percent": round(float(df["Humidity"].min()), 2),
        "maximum_humidity_percent": round(float(df["Humidity"].max()), 2),
        "total_rainfall_dataset_units": round(float(df["Rainfall"].sum()), 2),
        "average_daily_rainfall_dataset_units": round(float(df["Rainfall"].mean()), 2),
        "rainy_days": rainy_days,
        "rainy_day_share_percent": round(rainy_days / len(df) * 100, 2),
        "weather_category_counts": weather_days,
        "calendar_span_days": int(len(date_range)),
        "observed_calendar_days": int(len(observed_dates)),
        "missing_calendar_days": [day.date().isoformat() for day in missing_dates],
        "calendar_day_coverage_percent": round(len(observed_dates) / len(date_range) * 100, 2),
        "dataset_file": csv_path.name,
        "dataset_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "temperature_unit": "degrees Celsius, as labelled in the source column",
        "humidity_unit": "percent, validated to [0, 100]",
        "rainfall_unit": None,
        "source_provider": None,
        "location": None,
        "measurement_method": None,
        "provenance_status": "not_documented_in_repository",
        "interpretation_note": (
            "Describes only the supplied observations. The rainfall unit, provider, "
            "location and measurement method are undocumented. This is not a forecast "
            "or a climate conclusion."
        ),
    }
    with (destination / "weather_summary.json").open("w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2, ensure_ascii=False)
        summary_file.write("\n")

    print("WEATHER DATA SUMMARY")
    print("-" * 30)
    print(f"Date Range: {summary['date_start']} to {summary['date_end']}")
    print(f"Records: {summary['records']}")
    print(f"Average Temperature (°C): {summary['average_temperature_c']}")
    print(f"Median Temperature (°C): {summary['median_temperature_c']}")
    print(f"Temperature Range (°C): {summary['minimum_temperature_c']} to {summary['maximum_temperature_c']}")
    print(f"Average Humidity (%): {summary['average_humidity_percent']}")
    print(f"Total Rainfall (dataset units): {summary['total_rainfall_dataset_units']}")
    print(f"Average Daily Rainfall (dataset units): {summary['average_daily_rainfall_dataset_units']}")
    print(f"Rainy Days: {summary['rainy_days']} ({summary['rainy_day_share_percent']}%)")
    print(f"Weather Categories: {summary['weather_category_counts']}")
    print(f"Calendar coverage: {summary['calendar_day_coverage_percent']}%")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["Date"], df["Temperature"], marker="o", linewidth=2)
    ax.set(title="Temperature Trend Over Time", xlabel="Date", ylabel="Temperature (°C)")
    ax.tick_params(axis="x", labelrotation=45)
    ax.grid(True)
    fig.tight_layout()
    fig.savefig(destination / "temperature_trend.png")
    if show:
        plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(df["Date"], df["Rainfall"])
    ax.set(title="Daily Rainfall (source unit undocumented)", xlabel="Date", ylabel="Rainfall (dataset units)")
    ax.tick_params(axis="x", labelrotation=45)
    fig.tight_layout()
    fig.savefig(destination / "rainfall_analysis.png")
    if show:
        plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 6))
    df["Weather"].value_counts().plot(kind="pie", autopct="%1.1f%%", ax=ax)
    ax.set(title="Weather Distribution", ylabel="")
    fig.tight_layout()
    fig.savefig(destination / "weather_distribution.png")
    if show:
        plt.show()
    plt.close(fig)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze the supplied weather dataset.")
    parser.add_argument("--data", help="Optional path to a weather CSV file.")
    parser.add_argument("--output-dir", help="Directory for generated charts and JSON.")
    parser.add_argument("--show", action="store_true", help="Display charts after saving.")
    args = parser.parse_args()
    run_analysis(args.data, args.output_dir, args.show)
