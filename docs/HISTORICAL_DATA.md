# Historical weather data workflow

This document describes the single supported historical data workflow in this repository.

## Source

- Provider: Open-Meteo Historical Weather API.
- Documentation: https://open-meteo.com/en/docs/historical-weather-api
- Endpoint: https://archive-api.open-meteo.com/v1/archive
- Requested model: ERA5.
- Attribution: Weather data by Open-Meteo.com.
- License: CC BY 4.0 attribution is required. The free API service is for non-commercial use; check current terms before commercial use or redistribution.

ERA5 values are gridded reanalysis estimates, not direct observations from a local weather station.

## Download

Use only `scripts/download_historical_weather.py`. The script requires explicit coordinates, a location label and dates. It does not guess a location.

```bash
python -m pip install pandas requests
python scripts/download_historical_weather.py \
  --latitude YOUR_LATITUDE \
  --longitude YOUR_LONGITUDE \
  --location-label "Your study location" \
  --start-date 2021-01-01 \
  --end-date 2025-12-31 \
  --output data/external/era5_daily.csv
```

The downloader writes a CSV and a matching `.metadata.json` sidecar. The metadata preserves requested and returned coordinates, elevation, date range, timezone, variables, units, model and attribution.

## Analyze

```bash
python scripts/analyze_historical_weather.py \
  --data data/external/era5_daily.csv \
  --output-dir outputs/historical
```

The analysis creates:
- `historical_weather_summary.json`
- `monthly_weather_summary.csv`
- `historical_temperature_trend.png`
- `historical_precipitation.png`
- `monthly_precipitation.png`

## Dataset columns

| Column | API variable | Unit |
|---|---|---|
| Date | time | Asia/Kolkata local calendar date |
| Temperature_Mean_C | temperature_2m_mean | °C |
| Temperature_Max_C | temperature_2m_max | °C |
| Temperature_Min_C | temperature_2m_min | °C |
| Humidity_Mean_Percent | relative_humidity_2m_mean | % |
| Precipitation_Sum_mm | precipitation_sum | mm |
| Wind_Speed_Max_kmh | wind_speed_10m_max | km/h |

## Interpretation rules

- The returned grid-cell coordinates can differ from the requested coordinates. Report both.
- Do not describe reanalysis estimates as direct station observations.
- Do not merge this external series with the original seven-row `weather.csv`; the source and measurement method are not documented for that sample.
- Report missing-date coverage and units.
- Avoid climate-trend claims from a short time period or one grid cell.
