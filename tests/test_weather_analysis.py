import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "weather-Data-Analysis.py"
DATA = PROJECT / "weather.csv"


def test_dataset_schema_and_summary_values():
    df = pd.read_csv(DATA)
    assert {"Date", "Temperature", "Humidity", "Rainfall", "Weather"} <= set(df.columns)
    assert len(df) == 7
    assert round(df["Temperature"].mean(), 2) == 25.0
    assert round(df["Humidity"].mean(), 2) == 66.86
    assert df["Rainfall"].sum() == 18


def run_script(data, output):
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--data", str(data), "--output-dir", str(output)],
        cwd=PROJECT, env=env, text=True, capture_output=True,
    )


def test_full_analysis_exports_charts_and_expanded_summary(tmp_path):
    import json
    result = run_script(DATA, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "Average Temperature (°C): 25.0" in result.stdout
    assert "Average Humidity (%): 66.86" in result.stdout
    for name in ("temperature_trend.png", "rainfall_analysis.png", "weather_distribution.png"):
        output = tmp_path / name
        assert output.is_file() and output.stat().st_size > 0
    summary = json.loads((tmp_path / "weather_summary.json").read_text(encoding="utf-8"))
    assert summary["records"] == 7
    assert summary["calendar_day_coverage_percent"] == 100.0
    assert summary["missing_calendar_days"] == []
    assert summary["rainfall_unit"] is None
    assert summary["minimum_temperature_c"] <= summary["average_temperature_c"] <= summary["maximum_temperature_c"]


def test_missing_dataset_fails_with_clear_error(tmp_path):
    result = run_script(tmp_path / "missing.csv", tmp_path / "out")
    assert result.returncode != 0
    assert "Weather dataset not found" in result.stderr


def test_invalid_humidity_is_rejected(tmp_path):
    frame = pd.read_csv(DATA)
    frame.loc[0, "Humidity"] = 101
    invalid = tmp_path / "invalid_humidity.csv"
    frame.to_csv(invalid, index=False)
    result = run_script(invalid, tmp_path / "out")
    assert result.returncode != 0
    assert "Humidity values must be between 0 and 100" in result.stderr


def test_negative_rainfall_is_rejected(tmp_path):
    frame = pd.read_csv(DATA)
    frame.loc[0, "Rainfall"] = -1
    invalid = tmp_path / "negative_rainfall.csv"
    frame.to_csv(invalid, index=False)
    result = run_script(invalid, tmp_path / "out")
    assert result.returncode != 0
    assert "Rainfall values cannot be negative" in result.stderr


def test_duplicate_dates_are_rejected(tmp_path):
    frame = pd.read_csv(DATA)
    frame.loc[1, "Date"] = frame.loc[0, "Date"]
    invalid = tmp_path / "duplicate_dates.csv"
    frame.to_csv(invalid, index=False)
    result = run_script(invalid, tmp_path / "out")
    assert result.returncode != 0
    assert "duplicate calendar dates" in result.stderr


def test_calendar_coverage_detects_missing_days(tmp_path):
    import json
    frame = pd.read_csv(DATA).drop(index=3)
    incomplete = tmp_path / "incomplete.csv"
    frame.to_csv(incomplete, index=False)
    result = run_script(incomplete, tmp_path / "out")
    assert result.returncode == 0, result.stderr
    summary = json.loads((tmp_path / "out" / "weather_summary.json").read_text(encoding="utf-8"))
    assert summary["calendar_span_days"] == 7
    assert summary["observed_calendar_days"] == 6
    assert summary["missing_calendar_days"] == ["2024-01-04"]
    assert summary["calendar_day_coverage_percent"] == round(6 / 7 * 100, 2)


def test_duplicate_calendar_dates_with_different_times_are_rejected(tmp_path):
    frame = pd.read_csv(DATA)
    parsed = pd.to_datetime(frame["Date"])
    frame["Date"] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")
    frame.loc[1, "Date"] = (pd.Timestamp(frame.loc[0, "Date"]) + pd.Timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
    invalid = tmp_path / "duplicate_calendar_dates.csv"
    frame.to_csv(invalid, index=False)
    result = run_script(invalid, tmp_path / "out")
    assert result.returncode != 0
    assert "duplicate calendar dates" in result.stderr
