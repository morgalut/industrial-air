from fastapi.testclient import TestClient

from metrics_api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy"
    }

def test_unknown_station() -> None:
    response = client.post(
        "/api/v1/stations/unknown/process",
        json={
            "frequency": "5min",
            "missing_strategy": "interpolate",
            "fill_value": 0,
            "flatline_window": 5,
        },
    )

    assert response.status_code == 404
    assert "No sensor data found" in response.json()["detail"]