"""Download documented daily historical weather observations from Open-Meteo."""
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
    "rain_sum",
    "wind_speed_10m_max",
]


def fetch_daily_weather(latitude: float, longitude: float, start_date: str, end_date: str):
    """Fetch and normalize daily observations plus source metadata."""
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
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
    }
    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise ValueError(payload.get("reason", "Open-Meteo returned an error"))
    daily = payload.get("daily")
    if not daily or "time" not in daily:
        raise ValueError("Open-Meteo response did not include daily observations")

    frame = pd.DataFrame({
        "Date": daily["time"],
        "Temperature": daily["temperature_2m_mean"],
        "Temperature_Max": daily["temperature_2m_max"],
        "Temperature_Min": daily["temperature_2m_min"],
        "Humidity": daily["relative_humidity_2m_mean"],
        "Rainfall": daily["precipitation_sum"],
        "Rain": daily["rain_sum"],
        "Wind_Speed_Max": daily["wind_speed_10m_max"],
    })
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise")
    metadata = {
        "provider": "Open-Meteo",
        "api": API_URL,
        "source_documentation": "https://open-meteo.com/en/docs/historical-weather-api",
        "latitude_requested": latitude,
        "longitude_requested": longitude,
        "latitude_returned": payload.get("latitude"),
        "longitude_returned": payload.get("longitude"),
        "elevation_m": payload.get("elevation"),
        "timezone": payload.get("timezone"),
        "start_date": start.date().isoformat(),
        "end_date": end.date().isoformat(),
        "daily_units": payload.get("daily_units", {}),
        "variables": DAILY_VARIABLES,
        "model_note": "Open-Meteo historical reanalysis. Values are model-based estimates, not direct measurements at a personal weather station.",
        "license": "CC BY 4.0 for non-commercial use; commercial use requires a suitable Open-Meteo plan. Verify current terms before redistribution.",
        "attribution": "Weather data by Open-Meteo.com",
    }
    return frame, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latitude", type=float, default=26.78817)
    parser.add_argument("--longitude", type=float, default=82.71617)
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--output", default="data/processed/basti_weather_2021_2025.csv")
    args = parser.parse_args()

    frame, metadata = fetch_daily_weather(args.latitude, args.longitude, args.start, args.end)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    metadata_path = output.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    print(f"Saved {len(frame)} daily records to {output}")
    print(f"Saved source metadata to {metadata_path}")
    print(f"Source: {metadata['provider']}, timezone: {metadata['timezone']}, units: {metadata['daily_units']}")


if __name__ == "__main__":
    main()
