"""Download a documented daily historical weather series from Open-Meteo.

The user must supply coordinates and dates. The script never guesses a location.
Open-Meteo Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api
The Open-Meteo historical dataset is published under CC BY 4.0; cite Open-Meteo
and include the API request details with any reused data.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

API_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "relative_humidity_2m_mean",
    "precipitation_sum",
    "wind_speed_10m_max",
]


def download_weather(latitude: float, longitude: float, start_date: str, end_date: str,
                     output_csv: str | Path, location_label: str) -> dict:
    """Fetch daily observations and save CSV plus a provenance JSON sidecar."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if start > end:
        raise ValueError("start_date must be on or before end_date")
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    if not location_label.strip():
        raise ValueError("Provide a non-empty location label")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": "Asia/Kolkata",
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }
    url = f"{API_URL}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "weather-data-analysis-portfolio/1.0"})
    with urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if payload.get("error"):
        raise RuntimeError(payload.get("reason", "Open-Meteo returned an error"))
    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    if not dates:
        raise RuntimeError("The API returned no daily observations for this request")
    frame = pd.DataFrame({
        "Date": dates,
        "Temperature_Mean_C": daily["temperature_2m_mean"],
        "Temperature_Max_C": daily["temperature_2m_max"],
        "Temperature_Min_C": daily["temperature_2m_min"],
        "Humidity_Mean_Percent": daily["relative_humidity_2m_mean"],
        "Precipitation_Sum_mm": daily["precipitation_sum"],
        "Wind_Speed_Max_kmh": daily["wind_speed_10m_max"],
    })
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)

    metadata = {
        "provider": "Open-Meteo",
        "api": API_URL,
        "dataset": "Historical Weather API (reanalysis-based historical data)",
        "license": "CC BY 4.0",
        "attribution": "Data sourced from Open-Meteo.com",
        "location_label": location_label.strip(),
        "latitude": latitude,
        "longitude": longitude,
        "timezone": payload.get("timezone", "Asia/Kolkata"),
        "requested_start_date": start.isoformat(),
        "requested_end_date": end.isoformat(),
        "returned_start_date": dates[0],
        "returned_end_date": dates[-1],
        "units": {
            "Temperature_Mean_C": "°C",
            "Temperature_Max_C": "°C",
            "Temperature_Min_C": "°C",
            "Humidity_Mean_Percent": "%",
            "Precipitation_Sum_mm": "mm",
            "Wind_Speed_Max_kmh": "km/h",
        },
        "daily_variables": DAILY_VARIABLES,
        "api_elevation_m": payload.get("elevation"),
        "csv_file": output_path.name,
        "records": len(frame),
        "retrieved_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
    }
    metadata_path = output_path.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Saved {len(frame)} daily records to {output_path}")
    print(f"Saved provenance metadata to {metadata_path}")
    print(f"Source: {API_URL}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--location-label", required=True, help="Human-readable label for these coordinates")
    parser.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--output", default="data/external/open_meteo_daily.csv")
    args = parser.parse_args()
    download_weather(args.latitude, args.longitude, args.start_date, args.end_date,
                     args.output, args.location_label)


if __name__ == "__main__":
    main()
