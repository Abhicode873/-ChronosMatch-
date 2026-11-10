
"""FastAPI application for ChronosMatch."""

import asyncio
from tempfile import TemporaryDirectory
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from chronosmatch.api.schemas import SimulationRunRequest
from chronosmatch.simulator.market_simulator import AsyncMarketSimulator
from chronosmatch.simulator.pipeline import (
    PipelineEvent,
    PipelineResult,
    run_market_pipeline,
)

app = FastAPI(
    title="ChronosMatch API",
    description="REST and WebSocket API for the ChronosMatch trading simulator.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "project": "ChronosMatch",
        "message": "ChronosMatch API is running",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ChronosMatch API",
    }


def serialize_result(result: PipelineResult) -> dict[str, Any]:
    """Convert a completed pipeline result into an API response."""

    return {
        "status": "completed",
        "summary": {
            "orders_generated": result.orders_generated,
            "orders_processed": result.orders_processed,
            "trade_count": result.trade_count,
            "buffer_high_watermark": result.buffer_high_watermark,
        },
        "trades": [
            {
                "symbol": trade.symbol,
                "maker_order_id": trade.maker_order_id,
                "taker_order_id": trade.taker_order_id,
                "price_ticks": trade.price_ticks,
                "quantity": trade.quantity,
            }
            for trade in result.trades
        ],
        "order_books": [
            {
                "symbol": book.symbol,
                "active_order_count": book.active_order_count,
                "best_bid": book.best_bid,
                "best_ask": book.best_ask,
            }
            for book in result.books
        ],
        "performance": {
            "orders_processed": result.metrics.orders_processed,
            "trades_executed": result.metrics.trades_executed,
            "throughput_orders_per_second": (
                result.metrics.throughput_orders_per_second
            ),
            "elapsed_ns": result.metrics.elapsed_ns,
            "latency_min_ns": result.metrics.latency_min_ns,
            "latency_max_ns": result.metrics.latency_max_ns,
            "latency_p50_ns": result.metrics.latency_p50_ns,
            "latency_p95_ns": result.metrics.latency_p95_ns,
            "latency_p99_ns": result.metrics.latency_p99_ns,
        },
    }


@app.post("/api/v1/simulator/run")
async def run_simulation(request: SimulationRunRequest):
    """Run a finite simulation through the existing matching pipeline."""

    try:
        simulator = AsyncMarketSimulator(
            seed=request.seed,
            interval_seconds=request.interval_seconds,
        )

        with TemporaryDirectory(prefix="chronosmatch-") as temp_dir:
            result = await run_market_pipeline(
                simulator=simulator,
                order_count=request.order_count,
                buffer_path=f"{temp_dir}/orders.mmap",
                buffer_capacity=request.buffer_capacity,
            )

        return serialize_result(result)

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Simulation failed. Check the API server logs.",
        ) from exc


@app.websocket("/ws/simulator")
async def websocket_simulator(websocket: WebSocket):
    """Stream simulation events and monitor client disconnections."""

    await websocket.accept()

    pipeline_task: asyncio.Task | None = None
    disconnect_task: asyncio.Task | None = None

    async def monitor_disconnect() -> None:
        """Wait for the client to disconnect."""

        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                raise WebSocketDisconnect(
                    code=message.get("code", 1000)
                )

    try:
        raw_request = await websocket.receive_json()

        try:
            request = SimulationRunRequest.model_validate(raw_request)
        except ValidationError as exc:
            await websocket.send_json(
                {
                    "event": "error",
                    "data": {
                        "message": "Invalid simulation configuration.",
                        "details": exc.errors(
                            include_input=False,
                            include_url=False,
                        ),
                    },
                }
            )
            await websocket.close(code=1008)
            return

        await websocket.send_json(
            {
                "event": "started",
                "data": {
                    "order_count": request.order_count,
                    "seed": request.seed,
                    "interval_seconds": request.interval_seconds,
                    "buffer_capacity": request.buffer_capacity,
                },
            }
        )

        async def send_event(event: PipelineEvent) -> None:
            await websocket.send_json(event)

        simulator = AsyncMarketSimulator(
            seed=request.seed,
            interval_seconds=request.interval_seconds,
        )

        with TemporaryDirectory(prefix="chronosmatch-ws-") as temp_dir:
            pipeline_task = asyncio.create_task(
                run_market_pipeline(
                    simulator=simulator,
                    order_count=request.order_count,
                    buffer_path=f"{temp_dir}/orders.mmap",
                    buffer_capacity=request.buffer_capacity,
                    event_callback=send_event,
                ),
                name="chronosmatch-websocket-pipeline",
            )

            disconnect_task = asyncio.create_task(
                monitor_disconnect(),
                name="chronosmatch-websocket-disconnect-monitor",
            )

            done, _ = await asyncio.wait(
                {pipeline_task, disconnect_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            if disconnect_task in done:
                await disconnect_task

            result = await pipeline_task

        await websocket.send_json(
            {
                "event": "completed",
                "data": serialize_result(result),
            }
        )

        await websocket.close(code=1000)

    except WebSocketDisconnect:
        # A disconnected client should not leave a simulation running.
        return

    except asyncio.CancelledError:
        raise

    except (ValueError, TypeError, OSError):
        try:
            await websocket.send_json(
                {
                    "event": "error",
                    "data": {
                        "message": (
                            "Simulation failed. Check the API server logs."
                        ),
                    },
                }
            )
            await websocket.close(code=1011)
        except (WebSocketDisconnect, RuntimeError):
            pass

    finally:
        tasks = [
            task
            for task in (pipeline_task, disconnect_task)
            if task is not None and not task.done()
        ]

        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
