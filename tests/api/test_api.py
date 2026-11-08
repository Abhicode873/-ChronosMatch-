"""Tests for the ChronosMatch REST API."""

from fastapi.testclient import TestClient

from chronosmatch.api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["project"] == "ChronosMatch"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_run_simulation_successfully():
    response = client.post(
        "/api/v1/simulator/run",
        json={
            "order_count": 1000,
            "seed": 42,
            "interval_seconds": 0,
            "buffer_capacity": 64,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert data["summary"]["orders_generated"] == 1000
    assert data["summary"]["orders_processed"] == 1000
    assert data["summary"]["trade_count"] == len(data["trades"])
    assert data["summary"]["buffer_high_watermark"] <= 64

    assert data["performance"]["orders_processed"] == 1000
    assert len(data["order_books"]) == 3


def test_simulation_rejects_invalid_order_count():
    response = client.post(
        "/api/v1/simulator/run",
        json={
            "order_count": 0,
            "seed": 42,
            "interval_seconds": 0,
            "buffer_capacity": 64,
        },
    )

    assert response.status_code == 422