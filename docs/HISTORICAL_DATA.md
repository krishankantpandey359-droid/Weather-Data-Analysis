# Historical weather dataset acquisition

The repository's original seven-row `weather.csv` is preserved as the small teaching example. It is not silently replaced.

## Reproducible historical dataset

Use the downloader to fetch daily historical reanalysis data for a documented location and period:

```bash
python -m pip install pandas requests
python scripts/download_historical_weather.py --latitude 26.78817 --longitude 82.71617 --start 2021-01-01 --end 2025-12-31
```

The default coordinates are a Basti-area reference point. The returned coordinates and elevation are saved in the metadata file, because the API selects a grid cell and its returned coordinates can differ from the requested coordinates.

Outputs:
- `data/processed/basti_weather_2021_2025.csv`
- `data/processed/basti_weather_2021_2025.metadata.json`

The CSV contains daily mean, maximum and minimum temperature (°C), mean relative humidity (%), precipitation and rain sum (mm), and maximum 10 m wind speed (km/h). The JSON records source, requested and returned coordinates, timezone, units, dates, variables, and attribution.

## Source and model limitations

- Provider: Open-Meteo Historical Weather API.
- API documentation: https://open-meteo.com/en/docs/historical-weather-api
- Endpoint: https://archive-api.open-meteo.com/v1/archive
- The API uses reanalysis products such as ERA5 and ERA5-Land. These are gridded, model-based historical estimates, not guaranteed observations from a weather station at the requested point.
- Open-Meteo describes historical coverage from 1940 onward, with different models and spatial resolutions by period.
- Daily precipitation sum is measured in millimetres when requested with `precipitation_unit=mm`.
- Timezone is set to Asia/Kolkata for daily aggregation.
- Open-Meteo's documentation states CC BY 4.0 for non-commercial use. Commercial use requires a suitable paid plan. Review the current provider terms before redistribution or commercial use.
- Attribution: Weather data by Open-Meteo.com.

## Important analysis rule

Do not combine the seven-row sample with the historical series as if they share one source or measurement method. Analyze them separately. Update the main analysis to accept the new CSV explicitly and retain the source metadata alongside the output.
