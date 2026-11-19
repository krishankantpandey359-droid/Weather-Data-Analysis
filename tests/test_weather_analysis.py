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


def test_full_analysis_runs_and_creates_all_charts(tmp_path):
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--data", str(DATA), "--output-dir", str(tmp_path)],
        cwd=PROJECT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "Average Temperature: 25.0" in result.stdout
    assert "Average Humidity: 66.86" in result.stdout
    assert "Total Rainfall: 18.0" in result.stdout
    for name in ("temperature_trend.png", "rainfall_analysis.png", "weather_distribution.png"):
        output = tmp_path / name
        assert output.is_file()
        assert output.stat().st_size > 0


def test_missing_dataset_fails_with_clear_error(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--data", str(tmp_path / "missing.csv")],
        cwd=PROJECT,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "Weather dataset not found" in result.stderr


def test_invalid_humidity_is_rejected(tmp_path):
    frame = pd.read_csv(DATA)
    frame.loc[0, "Humidity"] = 101
    invalid = tmp_path / "invalid_humidity.csv"
    frame.to_csv(invalid, index=False)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--data", str(invalid), "--output-dir", str(tmp_path / "out")],
        cwd=PROJECT, text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert "Humidity values must be between 0 and 100" in result.stderr


def test_negative_rainfall_is_rejected(tmp_path):
    frame = pd.read_csv(DATA)
    frame.loc[0, "Rainfall"] = -1
    invalid = tmp_path / "negative_rainfall.csv"
    frame.to_csv(invalid, index=False)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--data", str(invalid), "--output-dir", str(tmp_path / "out")],
        cwd=PROJECT, text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert "Rainfall values cannot be negative" in result.stderr


def test_duplicate_dates_are_rejected(tmp_path):
    frame = pd.read_csv(DATA)
    frame.loc[1, "Date"] = frame.loc[0, "Date"]
    invalid = tmp_path / "duplicate_dates.csv"
    frame.to_csv(invalid, index=False)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--data", str(invalid), "--output-dir", str(tmp_path / "out")],
        cwd=PROJECT, text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert "duplicate calendar dates" in result.stderr


def test_summary_reports_observed_date_coverage(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("weather_analysis", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    summary = module.run_analysis(DATA, tmp_path)
    assert summary["date_start"] == "2024-01-01"
    assert summary["date_end"] == "2024-01-07"
    assert summary["calendar_span_days"] == 7
    assert summary["calendar_day_coverage_percent"] == 100.0


def test_duplicate_calendar_dates_with_different_times_are_rejected(tmp_path):
    frame = pd.read_csv(DATA)
    parsed_dates = pd.to_datetime(frame["Date"])
    frame["Date"] = parsed_dates.dt.strftime("%Y-%m-%d %H:%M:%S")
    frame.loc[1, "Date"] = (
        pd.Timestamp(frame.loc[0, "Date"]) + pd.Timedelta(hours=12)
    ).strftime("%Y-%m-%d %H:%M:%S")
    invalid = tmp_path / "duplicate_calendar_dates.csv"
    frame.to_csv(invalid, index=False)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--data", str(invalid),
         "--output-dir", str(tmp_path / "out")],
        cwd=PROJECT, text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert "duplicate calendar dates" in result.stderr

def test_analysis_exports_machine_readable_summary(tmp_path):
    import json
    import importlib.util

    spec = importlib.util.spec_from_file_location("weather_analysis", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    summary = module.run_analysis(DATA, tmp_path)

    output = tmp_path / "weather_summary.json"
    assert output.is_file()
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved == summary
    assert saved["records"] == 7
    assert saved["calendar_day_coverage_percent"] == 100.0


def test_summary_records_dataset_fingerprint_and_unknown_provenance(tmp_path):
    import hashlib
    import importlib.util
    import json

    spec = importlib.util.spec_from_file_location("weather_analysis", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    summary = module.run_analysis(DATA, tmp_path)

    assert summary["dataset_file"] == DATA.name
    assert summary["dataset_sha256"] == hashlib.sha256(DATA.read_bytes()).hexdigest()
    assert summary["source_provider"] is None
    assert summary["location"] is None
    assert summary["measurement_method"] is None
    assert summary["provenance_status"] == "not_documented_in_repository"
    saved = json.loads((tmp_path / "weather_summary.json").read_text(encoding="utf-8"))
    assert saved == summary
