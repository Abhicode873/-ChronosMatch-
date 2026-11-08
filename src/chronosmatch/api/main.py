
"""FastAPI application for ChronosMatch."""

from tempfile import TemporaryDirectory

from fastapi import FastAPI, HTTPException

from chronosmatch.api.schemas import SimulationRunRequest
from chronosmatch.simulator.market_simulator import AsyncMarketSimulator
from chronosmatch.simulator.pipeline import run_market_pipeline

app = FastAPI(
    title="ChronosMatch API",
    description="REST API for the ChronosMatch trading simulator.",
    version="0.1.0",
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
