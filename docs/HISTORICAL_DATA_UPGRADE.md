# Historical weather analysis upgrade

The historical weather workflow is now standardized around one downloader and one analysis script.

## Supported scripts

- Downloader: `scripts/download_historical_weather.py`
- Analysis: `scripts/analyze_historical_weather.py`

The older alternative downloader `scripts/download_open_meteo.py` has been retired. Do not use the old `download_weather.py` command examples from earlier versions of this document.

## End-to-end example

Choose and verify the coordinates for the location you intend to study.

```bash
python -m pip install pandas numpy matplotlib requests pytest
python scripts/download_historical_weather.py \
  --latitude YOUR_LATITUDE \
  --longitude YOUR_LONGITUDE \
  --location-label "Your study location" \
  --start-date 2021-01-01 \
  --end-date 2025-12-31 \
  --output data/external/era5_daily.csv

python scripts/analyze_historical_weather.py \
  --data data/external/era5_daily.csv \
  --output-dir outputs/historical
```

The download produces a CSV and provenance JSON. The analysis validates the unit-labelled schema and produces daily charts, a monthly summary and a machine-readable report.

## Analysis questions

1. How do monthly mean and maximum temperatures vary across years?
2. Which months have the highest total precipitation?
3. How many days per month receive at least 1 mm precipitation?
4. How does mean humidity vary across the selected period?
5. Are there missing dates or unusual values in the requested time series?

The current script reports these descriptive measures. It does not perform causal analysis or a weather forecast.

## Source limitations

Open-Meteo Historical Weather API data requested here uses ERA5 reanalysis. It is a gridded model-based estimate, not direct station data. Preserve the returned coordinates, elevation, timezone, units, requested dates and metadata sidecar with every analysis. Cite Open-Meteo and comply with its current CC BY 4.0 and API-use terms.

The original seven-row `weather.csv` remains a separate teaching example. Do not combine it with the historical ERA5 dataset.
