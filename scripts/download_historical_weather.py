"""Download daily ERA5 historical weather data from Open-Meteo.

The downloader writes a unit-labelled CSV and a JSON provenance sidecar.
The original seven-row weather.csv remains a separate teaching example.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import requests

API_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "relative_humidity_2m_mean",
    "precipitation_sum",
    "wind_speed_10m_max",
]
OUTPUT_COLUMNS = [
    "Date",
    "Temperature_Mean_C",
    "Temperature_Max_C",
    "Temperature_Min_C",
    "Humidity_Mean_Percent",
    "Precipitation_Sum_mm",
    "Wind_Speed_Max_kmh",
]


def fetch_daily_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    location_label: str,
):
    """Fetch ERA5 daily values and return a normalized frame and provenance."""
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    if not isinstance(location_label, str) or not location_label.strip():
        raise ValueError("location_label must not be blank")

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if pd.isna(start) or pd.isna(end):
        raise ValueError("start_date and end_date must be valid dates")
    if start > end:
        raise ValueError("start_date must be on or before end_date")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start.date().isoformat(),
        "end_date": end.date().isoformat(),
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "Asia/Kolkata",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "models": "era5",
    }
    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise ValueError(payload.get("reason", "Open-Meteo returned an error"))

    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    if not dates:
        raise ValueError("Open-Meteo response did not include daily observations")

    missing = [name for name in DAILY_VARIABLES if name not in daily]
    if missing:
        raise ValueError(f"Open-Meteo response is missing daily variables: {missing}")
    lengths = {len(daily[name]) for name in DAILY_VARIABLES}
    if len(lengths) != 1 or lengths != {len(dates)}:
        raise ValueError("Open-Meteo daily variables have inconsistent lengths")

    frame = pd.DataFrame({
        "Date": pd.to_datetime(dates, errors="raise"),
        "Temperature_Mean_C": daily["temperature_2m_mean"],
        "Temperature_Max_C": daily["temperature_2m_max"],
        "Temperature_Min_C": daily["temperature_2m_min"],
        "Humidity_Mean_Percent": daily["relative_humidity_2m_mean"],
        "Precipitation_Sum_mm": daily["precipitation_sum"],
        "Wind_Speed_Max_kmh": daily["wind_speed_10m_max"],
    })
    for column in OUTPUT_COLUMNS[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame[OUTPUT_COLUMNS[1:]].isna().any().any():
        raise ValueError("Open-Meteo response contains missing or non-numeric values")
    import numpy as np
    if not np.isfinite(frame[OUTPUT_COLUMNS[1:]].to_numpy(dtype=float)).all():
        raise ValueError("Open-Meteo response contains non-finite numeric values")
    if frame["Date"].duplicated().any():
        raise ValueError("Open-Meteo response contains duplicate dates")

    metadata = {
        "provider": "Open-Meteo",
        "api": API_URL,
        "source_documentation": "https://open-meteo.com/en/docs/historical-weather-api",
        "model": "ERA5",
        "location_label": location_label.strip(),
        "latitude_requested": latitude,
        "longitude_requested": longitude,
        "latitude_returned": payload.get("latitude"),
        "longitude_returned": payload.get("longitude"),
        "elevation_m": payload.get("elevation"),
        "timezone": payload.get("timezone"),
        "requested_start_date": start.date().isoformat(),
        "requested_end_date": end.date().isoformat(),
        "returned_start_date": frame["Date"].min().date().isoformat(),
        "returned_end_date": frame["Date"].max().date().isoformat(),
        "daily_units": payload.get("daily_units", {}),
        "variables": DAILY_VARIABLES,
        "output_columns": OUTPUT_COLUMNS,
        "license": "CC BY 4.0; attribution required. Verify current Open-Meteo terms before reuse.",
        "attribution": "Weather data by Open-Meteo.com",
        "model_note": "ERA5 gridded reanalysis estimates, not direct weather-station measurements.",
    }
    return frame, metadata


def download_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    location_label: str,
    output_csv: str | Path,
):
    """Fetch and persist CSV plus provenance JSON."""
    frame, metadata = fetch_daily_weather(
        latitude, longitude, start_date, end_date, location_label
    )
    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    metadata["csv_file"] = output.name
    metadata["records"] = len(frame)
    metadata_path = output.with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return frame, metadata, metadata_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--location-label", required=True)
    parser.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--output", default="data/external/era5_daily.csv")
    args = parser.parse_args()
    frame, metadata, metadata_path = download_weather(
        args.latitude, args.longitude, args.start_date, args.end_date,
        args.location_label, args.output,
    )
    print(f"Saved {len(frame)} daily records to {args.output}")
    print(f"Saved provenance metadata to {metadata_path}")
    print(f"Source: Open-Meteo ERA5; timezone: {metadata.get('timezone')}")


if __name__ == "__main__":
    main()
