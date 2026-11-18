# Weather Data Analysis and Visualization

A Python project that summarizes a small daily weather dataset and generates three charts.

## Dataset

The committed `weather.csv` contains seven daily records from 1 to 7 January 2024, with:

- Date
- Temperature (°C)
- Humidity (%)
- Rainfall
- Weather description

The supplied sample has an average temperature of 25.0°C, average humidity of 66.86%, and total rainfall of 18 dataset units. These figures describe only the seven supplied records. They are not a forecast or a climate conclusion.

## What the script does

1. Loads the CSV using a path relative to the script by default.
2. Checks required columns and missing or invalid values.
3. Validates finite numeric values, humidity range, non-negative rainfall, non-empty weather descriptions and unique dates.
4. Calculates average temperature, average humidity, total rainfall and record count.
5. Saves temperature trend, rainfall and weather-distribution charts.

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

Add `--show` to display charts interactively. The default execution uses a non-interactive Matplotlib backend, so it also works in CI.

## Output files

- `temperature_trend.png`
- `rainfall_analysis.png`
- `weather_distribution.png`

## Project structure

- `weather-Data-Analysis.py`: validated analysis and chart generation.
- `weather.csv`: seven-row example dataset.
- `tests/test_weather_analysis.py`: dataset summary, chart generation and invalid-input tests.
- `.github/workflows/python-checks.yml`: automated compilation and test checks.

## Limitations

The dataset contains only seven days from January 2024. The repository does not document a weather station, geographic location, source provider or measurement methodology. Do not interpret this sample as representative of a city, region, season or long-term climate.

## Tools

Python, pandas, NumPy, Matplotlib and pytest.
