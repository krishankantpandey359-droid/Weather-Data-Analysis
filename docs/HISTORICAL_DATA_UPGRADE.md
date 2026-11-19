# Historical weather dataset upgrade

The repository's original `weather.csv` remains unchanged. It is a seven-day sample from 1–7 January 2024, with undocumented provider, location, rainfall unit and measurement method. Do not mix it silently with external observations.

## Reproducible historical data source

The optional downloader `scripts/download_open_meteo.py` uses the Open-Meteo Historical Weather API. It requires explicit latitude, longitude, a location label and a date range. It writes a CSV plus a JSON sidecar containing the coordinates, API, retrieval time, dates, variables and units.

Open-Meteo API documentation: https://open-meteo.com/en/docs/historical-weather-api

Open-Meteo attribution and license information: https://open-meteo.com/en/terms

The Historical Weather API provides reanalysis-based historical estimates. It is not a direct record from a local weather station and should not be described as observed station data. Cite Open-Meteo and comply with CC BY 4.0 attribution requirements when reusing the data.

## Example

Choose the coordinates for the location you intend to study. Do not copy the example coordinates without checking the intended place.

```bash
python scripts/download_open_meteo.py \
  --latitude YOUR_LATITUDE \
  --longitude YOUR_LONGITUDE \
  --location-label "Your study location" \
  --start-date 2021-01-01 \
  --end-date 2025-12-31 \
  --output data/external/open_meteo_daily.csv
```

The downloader does not overwrite `weather.csv`. The external series is kept separately under `data/external/`.

## Variables and units

| Output column | API variable | Unit |
|---|---|---|
| Date | time | Local calendar date |
| Temperature_Mean_C | temperature_2m_mean | °C |
| Temperature_Max_C | temperature_2m_max | °C |
| Temperature_Min_C | temperature_2m_min | °C |
| Humidity_Mean_Percent | relative_humidity_2m_mean | % |
| Precipitation_Sum_mm | precipitation_sum | mm |
| Wind_Speed_Max_kmh | wind_speed_10m_max | km/h |

## Analysis questions

1. How do monthly mean and maximum temperatures vary across years?
2. Which months have the highest total precipitation?
3. How many rainy days occur in each month, using a clearly stated precipitation threshold?
4. How does humidity vary with precipitation?
5. Are there missing dates or unusual values in the requested time series?

Avoid climate-trend claims from a short period or a single grid cell. Report the selected coordinates, date range, reanalysis source, units, missing-date coverage and limitations.
