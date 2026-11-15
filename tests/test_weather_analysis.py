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
