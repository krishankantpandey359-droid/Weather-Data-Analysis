# Weather Data Analysis and Visualization

A Python project that summarizes a small daily weather dataset and generates charts plus a machine-readable JSON report.

## Dataset

The committed `weather.csv` contains seven daily records from 1 to 7 January 2024. Its columns are Date, Temperature, Humidity, Rainfall and Weather.

The sample has an average temperature of 25.0°C, average humidity of 66.86%, and total rainfall of 18 dataset units. These values describe only the supplied observations. The rainfall unit is not documented, so the project deliberately labels it as a dataset unit rather than assuming millimetres.

## Analysis and validation

The script:
1. Loads the CSV using a path relative to the script by default.
2. Checks required columns, missing/invalid/non-finite values and unique calendar dates.
3. Validates humidity to the 0–100% range and rejects negative rainfall.
4. Calculates temperature and humidity ranges, rainfall summaries, weather-category counts and date coverage.
5. Lists missing calendar dates instead of silently treating an incomplete series as complete.
6. Exports three charts and `weather_summary.json`.
7. Records the input filename and SHA-256 fingerprint for reproducibility.

## Run locally

```bash
python -m pip install pandas matplotlib numpy pytest
python weather-Data-Analysis.py
pytest -q
```

To choose a CSV and output folder:

```bash
python weather-Data-Analysis.py --data weather.csv --output-dir outputs
```

Add `--show` to display charts interactively. The default uses a non-interactive Matplotlib backend for CI.

## Outputs

- `temperature_trend.png`
- `rainfall_analysis.png`
- `weather_distribution.png`
- `weather_summary.json`

## Limitations

The dataset contains only seven days from January 2024. The repository does not document a weather station, geographic location, source provider, rainfall unit or measurement methodology. The exported summary records unknown provenance as null. Do not interpret this sample as representative of a city, region, season or long-term climate, and do not treat it as a forecast.

## Tools

Python, pandas, NumPy, Matplotlib and pytest.
