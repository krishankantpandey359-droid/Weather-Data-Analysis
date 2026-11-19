import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from scripts.analyze_historical_weather import analyze_historical_weather

COLUMNS = [
    "Date", "Temperature_Mean_C", "Temperature_Max_C", "Temperature_Min_C",
    "Humidity_Mean_Percent", "Precipitation_Sum_mm", "Wind_Speed_Max_kmh",
]


def sample_frame():
    return pd.DataFrame([
        ["2024-01-01", 20, 25, 15, 60, 0, 10],
        ["2024-01-02", 21, 26, 16, 61, 2, 11],
        ["2024-01-03", 22, 27, 17, 62, 1, 12],
    ], columns=COLUMNS)


def test_historical_analysis_writes_summary_monthly_table_and_charts(tmp_path):
    source = tmp_path / "historical.csv"
    sample_frame().to_csv(source, index=False)
    output = tmp_path / "outputs"
    summary = analyze_historical_weather(source, output)
    assert summary["records"] == 3
    assert summary["total_precipitation_mm"] == 3.0
    assert summary["rainy_days_at_least_1mm"] == 2
    assert summary["calendar_coverage_percent"] == 100.0
    assert (output / "monthly_weather_summary.csv").is_file()
    assert (output / "historical_weather_summary.json").is_file()
    for filename in [
        "historical_temperature_trend.png",
        "historical_precipitation.png",
        "monthly_precipitation.png",
    ]:
        assert (output / filename).stat().st_size > 0


@pytest.mark.parametrize("column,value", [
    ("Humidity_Mean_Percent", 120),
    ("Precipitation_Sum_mm", -1),
    ("Wind_Speed_Max_kmh", -2),
    ("Temperature_Min_C", 30),
])
def test_historical_analysis_rejects_invalid_values(tmp_path, column, value):
    frame = sample_frame()
    frame.loc[0, column] = value
    source = tmp_path / "invalid.csv"
    frame.to_csv(source, index=False)
    with pytest.raises(ValueError):
        analyze_historical_weather(source, tmp_path / "out")


def test_historical_analysis_rejects_missing_columns(tmp_path):
    source = tmp_path / "missing.csv"
    sample_frame().drop(columns=["Wind_Speed_Max_kmh"]).to_csv(source, index=False)
    with pytest.raises(ValueError, match="missing columns"):
        analyze_historical_weather(source, tmp_path / "out")
