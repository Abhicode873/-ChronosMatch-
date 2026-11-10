
"""Tests for the ChronosMatch WebSocket API."""

import asyncio
import threading

from fastapi.testclient import TestClient

from chronosmatch.api import main as api_main

client = TestClient(api_main.app)


def test_websocket_simulation_streams_events():
    with client.websocket_connect("/ws/simulator") as websocket:
        websocket.send_json(
            {
                "order_count": 100,
                "seed": 42,
                "interval_seconds": 0,
                "buffer_capacity": 16,
            }
        )

        events = []

        while True:
            message = websocket.receive_json()
            events.append(message)

            if message["event"] in {"completed", "error"}:
                break

    event_types = [event["event"] for event in events]

    assert event_types[0] == "started"
    assert "progress" in event_types
    assert "trade" in event_types
    assert event_types[-1] == "completed"

    completion = events[-1]["data"]

    assert completion["status"] == "completed"
    assert completion["summary"]["orders_processed"] == 100
    assert completion["summary"]["orders_generated"] == 100
    assert completion["summary"]["trade_count"] == len(
        completion["trades"]
    )


def test_websocket_rejects_invalid_configuration():
    with client.websocket_connect("/ws/simulator") as websocket:
        websocket.send_json(
            {
                "order_count": 0,
                "seed": 42,
                "interval_seconds": 0,
                "buffer_capacity": 16,
            }
        )

        message = websocket.receive_json()

        assert message["event"] == "error"
        assert "Invalid simulation configuration" in (
            message["data"]["message"]
        )


def test_websocket_disconnect_cancels_pipeline(monkeypatch):
    pipeline_started = threading.Event()
    pipeline_cancelled = threading.Event()

    async def blocking_pipeline(**kwargs):
        pipeline_started.set()

        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pipeline_cancelled.set()
            raise

    monkeypatch.setattr(
        api_main,
        "run_market_pipeline",
        blocking_pipeline,
    )

    with client.websocket_connect("/ws/simulator") as websocket:
        websocket.send_json(
            {
                "order_count": 100000,
                "seed": 42,
                "interval_seconds": 0.01,
                "buffer_capacity": 16,
            }
        )

        message = websocket.receive_json()
        assert message["event"] == "started"

        assert pipeline_started.wait(timeout=5)

    assert pipeline_cancelled.wait(timeout=5)
