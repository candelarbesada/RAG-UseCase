from agent import tools


def test_truncate_content_leaves_short_text_unchanged():
    assert tools.truncate_content("short", max_length=10) == "short"


def test_truncate_content_adds_ellipsis_at_limit():
    assert tools.truncate_content("  abcdef  ", max_length=5) == "  abc..."


def test_get_weather_formats_mocked_forecast(monkeypatch):
    responses = [
        {
            "results": [
                {
                    "latitude": 48.8566,
                    "longitude": 2.3522,
                    "name": "Paris",
                    "country": "France",
                }
            ]
        },
        {
            "current": {
                "temperature_2m": 18,
                "apparent_temperature": 17,
                "relative_humidity_2m": 60,
                "wind_speed_10m": 8,
            }
        },
    ]

    class MockResponse:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    calls = []

    def mock_get(url, **kwargs):
        calls.append(url)
        return MockResponse(responses.pop(0))

    monkeypatch.setattr(tools.requests, "get", mock_get)

    result = tools.get_weather.invoke({"location": "Paris", "when": "tonight"})

    assert "Weather in Paris, France (tonight): 18°C" in result
    assert len(calls) == 2
