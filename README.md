# Weather Data Analysis and Historical Weather Analytics

This repository contains two deliberately separate analysis paths:

1. The original seven-row `weather.csv` teaching example.
2. A reproducible Open-Meteo ERA5 historical reanalysis download and analysis workflow.

The two datasets are never silently merged. ERA5 values are gridded reanalysis estimates, not direct measurements from a local weather station.

## Path A: Original seven-row sample

The committed `weather.csv` contains seven daily records from 1–7 January 2024. The existing script validates the sample and exports charts plus `weather_summary.json`.

```bash
python -m pip install -r requirements.txt
python weather-Data-Analysis.py
```

The sample reports an average temperature of 25.0°C, average humidity of 66.86%, and rainfall total of 18 dataset units. The rainfall unit, provider and location are undocumented. These figures describe only the seven supplied rows.

## Path B: Historical ERA5 workflow

### 1. Download data

There is one supported downloader: `scripts/download_historical_weather.py`.

Supply the coordinates and date range for the location you intend to study. Do not assume the example values represent a weather station.

```bash
python scripts/download_historical_weather.py \
  --latitude YOUR_LATITUDE \
  --longitude YOUR_LONGITUDE \
  --location-label "Your study location" \
  --start-date 2021-01-01 \
  --end-date 2025-12-31 \
  --output data/external/era5_daily.csv
```

The downloader writes:
- `data/external/era5_daily.csv`
- `data/external/era5_daily.metadata.json`

The metadata records requested and returned coordinates, elevation, dates, timezone, ERA5 model, units, API variables and attribution.

### 2. Analyze the downloaded data

```bash
python scripts/analyze_historical_weather.py \
  --data data/external/era5_daily.csv \
  --output-dir outputs/historical
```

The historical analysis validates the canonical schema, date uniqueness, finite numeric values, humidity range, non-negative precipitation and wind speed, and temperature min/mean/max ordering. It exports a JSON summary, monthly summary CSV, daily temperature chart, daily precipitation chart and monthly precipitation chart.

### Historical CSV schema

| Column | Unit |
|---|---|
| Date | Asia/Kolkata local calendar date |
| Temperature_Mean_C | °C |
| Temperature_Max_C | °C |
| Temperature_Min_C | °C |
| Humidity_Mean_Percent | % |
| Precipitation_Sum_mm | mm |
| Wind_Speed_Max_kmh | km/h |

## Source, attribution and limitations

- Provider: Open-Meteo Historical Weather API.
- API documentation: https://open-meteo.com/en/docs/historical-weather-api
- Endpoint: https://archive-api.open-meteo.com/v1/archive
- Model requested: ERA5.
- Attribution: Weather data by Open-Meteo.com.
- Open-Meteo historical data is published under CC BY 4.0; attribution is required. The free API service has non-commercial restrictions. Verify current terms before redistribution or commercial use.
- ERA5 is a gridded reanalysis product. Returned grid coordinates can differ from requested coordinates. It is not a personal weather station measurement.
- Report the location label, requested and returned coordinates, time period, units and missing-date coverage.
- Avoid climate-trend conclusions from a short period or a single grid cell.

## Tests and CI

```bash
python -m pytest -q
```

GitHub Actions compiles the analysis and scripts and runs both the original sample tests and mocked historical downloader/analysis tests. Tests do not make live API requests.

## Repository structure

- `weather.csv`: preserved seven-row teaching sample.
- `weather-Data-Analysis.py`: analysis of the original sample.
- `scripts/download_historical_weather.py`: sole supported historical downloader.
- `scripts/analyze_historical_weather.py`: historical CSV validation and analysis.
- `tests/`: automated tests for both paths.
- `docs/`: historical data workflow and source notes.

## Latest GitHub Actions validation

Latest successful main-branch workflow run checked on 26 November 2026: [GitHub Actions run #45795540922](https://github.com/krishankantpandey359-droid/Weather-Data-Analysis/actions/runs/45795540922). This confirms only the checks configured in the workflow, not manual validation of every feature.
