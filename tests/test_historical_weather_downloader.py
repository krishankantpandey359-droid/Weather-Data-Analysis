import json
import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from scripts import download_historical_weather as downloader


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "daily": {
                "time": ["2024-01-01", "2024-01-02"],
                "temperature_2m_mean": [20.0, 21.0],
                "temperature_2m_max": [25.0, 26.0],
                "temperature_2m_min": [15.0, 16.0],
                "relative_humidity_2m_mean": [60.0, 61.0],
                "precipitation_sum": [0.0, 2.0],
                "wind_speed_10m_max": [10.0, 11.0],
            },
            "latitude": 26.8,
            "longitude": 82.7,
            "elevation": 90,
            "timezone": "Asia/Kolkata",
            "daily_units": {"precipitation_sum": "mm"},
        }


def test_fetch_daily_weather_returns_standard_schema_and_metadata(monkeypatch):
    captured = {}

    def fake_get(url, params, timeout):
        captured.update(url=url, params=params, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(downloader.requests, "get", fake_get)
    frame, metadata = downloader.fetch_daily_weather(
        26.8, 82.7, "2024-01-01", "2024-01-02", "Test location"
    )
    assert list(frame.columns) == downloader.OUTPUT_COLUMNS
    assert len(frame) == 2
    assert pd.api.types.is_datetime64_any_dtype(frame["Date"])
    assert metadata["provider"] == "Open-Meteo"
    assert metadata["model"] == "ERA5"
    assert metadata["location_label"] == "Test location"
    assert captured["params"]["models"] == "era5"
    assert captured["params"]["precipitation_unit"] == "mm"
    assert captured["timeout"] == 60


@pytest.mark.parametrize(
    "latitude,longitude,start,end,label",
    [
        (91, 0, "2024-01-01", "2024-01-02", "X"),
        (0, 181, "2024-01-01", "2024-01-02", "X"),
        (0, 0, "2024-01-03", "2024-01-02", "X"),
        (0, 0, "not-a-date", "2024-01-02", "X"),
        (0, 0, "2024-01-01", "2024-01-02", "  "),
    ],
)
def test_fetch_daily_weather_rejects_invalid_request(
    monkeypatch, latitude, longitude, start, end, label
):
    monkeypatch.setattr(
        downloader.requests, "get",
        lambda *args, **kwargs: pytest.fail("API must not be called"),
    )
    with pytest.raises(ValueError):
        downloader.fetch_daily_weather(latitude, longitude, start, end, label)


def test_fetch_daily_weather_rejects_empty_payload(monkeypatch):
    class EmptyResponse(FakeResponse):
        def json(self):
            return {"daily": None}

    monkeypatch.setattr(
        downloader.requests, "get", lambda *args, **kwargs: EmptyResponse()
    )
    with pytest.raises(ValueError, match="did not include daily observations"):
        downloader.fetch_daily_weather(26.8, 82.7, "2024-01-01", "2024-01-02", "Test")


def test_fetch_daily_weather_rejects_inconsistent_api_arrays(monkeypatch):
    class BadResponse(FakeResponse):
        def json(self):
            payload = super().json()
            payload["daily"]["temperature_2m_mean"] = [20.0]
            return payload

    monkeypatch.setattr(
        downloader.requests, "get", lambda *args, **kwargs: BadResponse()
    )
    with pytest.raises(ValueError, match="inconsistent lengths"):
        downloader.fetch_daily_weather(26.8, 82.7, "2024-01-01", "2024-01-02", "Test")


def test_download_weather_writes_csv_and_metadata(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader.requests, "get", lambda *args, **kwargs: FakeResponse())
    output = tmp_path / "nested" / "history.csv"
    frame, metadata, metadata_path = downloader.download_weather(
        26.8, 82.7, "2024-01-01", "2024-01-02", "Test location", output
    )
    assert output.is_file()
    assert metadata_path.is_file()
    saved = pd.read_csv(output)
    assert list(saved.columns) == downloader.OUTPUT_COLUMNS
    sidecar = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert sidecar["records"] == 2
    assert sidecar["csv_file"] == "history.csv"
    assert metadata["model"] == "ERA5"
