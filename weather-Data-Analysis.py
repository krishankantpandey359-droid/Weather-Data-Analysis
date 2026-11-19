from pathlib import Path
import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"Date", "Temperature", "Humidity", "Rainfall", "Weather"}


def run_analysis(data_path=None, output_dir=None, show=False):
    """Load the bundled weather CSV, summarize it, and save three charts."""
    project_dir = Path(__file__).resolve().parent
    csv_path = Path(data_path) if data_path else project_dir / "weather.csv"
    destination = Path(output_dir) if output_dir else project_dir

    if not csv_path.is_file():
        raise FileNotFoundError(f"Weather dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")
    if df.empty:
        raise ValueError("Weather dataset is empty")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for column in ("Temperature", "Humidity", "Rainfall"):
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if df[["Date", "Temperature", "Humidity", "Rainfall", "Weather"]].isna().any().any():
        raise ValueError("Weather dataset contains missing or invalid required values")
    numeric = df[["Temperature", "Humidity", "Rainfall"]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("Weather dataset contains infinite numeric values")
    if not df["Humidity"].between(0, 100).all():
        raise ValueError("Humidity values must be between 0 and 100 percent")
    if (df["Rainfall"] < 0).any():
        raise ValueError("Rainfall values cannot be negative")
    if df["Weather"].astype(str).str.strip().eq("").any():
        raise ValueError("Weather descriptions must not be blank")
    if df["Date"].dt.normalize().duplicated().any():
        raise ValueError("Weather dataset contains duplicate calendar dates")

    df = df.sort_values("Date")
    destination.mkdir(parents=True, exist_ok=True)

    summary = {
        "average_temperature": round(float(df["Temperature"].mean()), 2),
        "average_humidity": round(float(df["Humidity"].mean()), 2),
        "total_rainfall": float(df["Rainfall"].sum()),
        "records": int(len(df)),
        "date_start": df["Date"].min().date().isoformat(),
        "date_end": df["Date"].max().date().isoformat(),
        "calendar_span_days": int((df["Date"].max() - df["Date"].min()).days + 1),
        "calendar_day_coverage_percent": round(
            len(df) / ((df["Date"].max() - df["Date"].min()).days + 1) * 100, 2
        ),
    }
    with (destination / "weather_summary.json").open("w", encoding="utf-8") as summary_file:
        json.dump(summary, summary_file, indent=2, ensure_ascii=False)
        summary_file.write("\n")

    print("WEATHER DATA SUMMARY")
    print("-" * 30)
    print(f"Average Temperature: {summary['average_temperature']}")
    print(f"Average Humidity: {summary['average_humidity']}")
    print(f"Total Rainfall: {summary['total_rainfall']}")

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
    ax.set(title="Rainfall Analysis", xlabel="Date", ylabel="Rainfall")
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
    parser = argparse.ArgumentParser(description="Analyze the bundled weather dataset.")
    parser.add_argument("--data", help="Optional path to a weather CSV file.")
    parser.add_argument("--output-dir", help="Directory for generated charts.")
    parser.add_argument("--show", action="store_true", help="Display charts after saving.")
    args = parser.parse_args()
    run_analysis(args.data, args.output_dir, args.show)
