import pandas as pd
import pytest

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
                "rain_sum": [0.0, 2.0],
                "wind_speed_10m_max": [10.0, 11.0],
            },
            "latitude": 26.8,
            "longitude": 82.7,
            "elevation": 90,
            "timezone": "Asia/Kolkata",
            "daily_units": {"precipitation_sum": "mm"},
        }


def test_fetch_daily_weather_maps_api_schema_and_metadata(monkeypatch):
    captured = {}

    def fake_get(url, params, timeout):
        captured.update(url=url, params=params, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(downloader.requests, "get", fake_get)
    frame, metadata = downloader.fetch_daily_weather(
        26.8, 82.7, "2024-01-01", "2024-01-02"
    )

    assert list(frame.columns) == [
        "Date", "Temperature", "Temperature_Max", "Temperature_Min",
        "Humidity", "Rainfall", "Rain", "Wind_Speed_Max",
    ]
    assert len(frame) == 2
    assert pd.api.types.is_datetime64_any_dtype(frame["Date"])
    assert metadata["provider"] == "Open-Meteo"
    assert metadata["model"] == "ERA5"
    assert metadata["daily_units"]["precipitation_sum"] == "mm"
    assert captured["params"]["models"] == "era5"
    assert captured["timeout"] == 60


@pytest.mark.parametrize(
    "latitude,longitude,start,end",
    [
        (91, 0, "2024-01-01", "2024-01-02"),
        (0, 181, "2024-01-01", "2024-01-02"),
        (0, 0, "2024-01-03", "2024-01-02"),
    ],
)
def test_fetch_daily_weather_rejects_invalid_request(
    monkeypatch, latitude, longitude, start, end
):
    def unexpected_request(*args, **kwargs):
        pytest.fail("API should not be called for invalid inputs")

    monkeypatch.setattr(downloader.requests, "get", unexpected_request)
    with pytest.raises(ValueError):
        downloader.fetch_daily_weather(latitude, longitude, start, end)


def test_fetch_daily_weather_rejects_empty_api_payload(monkeypatch):
    class EmptyResponse(FakeResponse):
        def json(self):
            return {"daily": None}

    monkeypatch.setattr(
        downloader.requests, "get", lambda *args, **kwargs: EmptyResponse()
    )
    with pytest.raises(ValueError, match="did not include daily observations"):
        downloader.fetch_daily_weather(26.8, 82.7, "2024-01-01", "2024-01-02")
