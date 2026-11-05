
"""End-to-end integration tests for the ChronosMatch pipeline."""

import asyncio

import pytest

from chronosmatch.core.models import Order, Side
from chronosmatch.ipc.ring_buffer import RingBuffer
from chronosmatch.simulator.market_simulator import AsyncMarketSimulator
from chronosmatch.simulator.pipeline import run_market_pipeline


def test_pipeline_generates_transfers_and_executes_orders(tmp_path) -> None:
    """Verify simulator-to-IPC-to-Cython execution."""
    simulator = AsyncMarketSimulator(
        base_prices={"AAPL": 100_000},
        seed=42,
        price_variation_ticks=0,
    )

    buffer_path = tmp_path / "pipeline.mmap"
    order_count = 200
    capacity = 4

    result = asyncio.run(
        run_market_pipeline(
            simulator,
            order_count,
            buffer_path,
            buffer_capacity=capacity,
            book_capacity=256,
        )
    )

    assert result.orders_generated == order_count
    assert result.orders_processed == order_count
    assert simulator.generated_count == order_count

        # Verify pipeline performance metrics.
    metrics = result.metrics

    assert metrics.orders_processed == order_count
    assert metrics.trades_executed == result.trade_count

    assert metrics.elapsed_ns > 0
    assert metrics.throughput_orders_per_second > 0

    assert metrics.latency_min_ns is not None
    assert metrics.latency_max_ns is not None
    assert metrics.latency_p50_ns is not None
    assert metrics.latency_p95_ns is not None
    assert metrics.latency_p99_ns is not None

    assert metrics.latency_min_ns <= metrics.latency_p50_ns
    assert metrics.latency_p50_ns <= metrics.latency_p95_ns
    assert metrics.latency_p95_ns <= metrics.latency_p99_ns
    assert metrics.latency_p99_ns <= metrics.latency_max_ns

    assert metrics.buffer_high_watermark == result.buffer_high_watermark

    assert result.trade_count > 0
    assert all(trade.symbol == "AAPL" for trade in result.trades)
    assert all(trade.price_ticks > 0 for trade in result.trades)
    assert all(trade.quantity > 0 for trade in result.trades)

    assert all(
        trade.maker_order_id.startswith("SIM-")
        and trade.taker_order_id.startswith("SIM-")
        for trade in result.trades
    )

    assert len(result.books) == 1
    assert result.books[0].symbol == "AAPL"

    assert 0 < result.buffer_high_watermark <= capacity

    # The pipeline should have consumed every published record.
    with RingBuffer(buffer_path, capacity) as buffer:
        assert buffer.is_empty


def test_pipeline_keeps_symbols_in_separate_order_books(tmp_path) -> None:
    """Verify trades never match orders belonging to different symbols."""
    base_prices = {
        "AAPL": 100_000,
        "MSFT": 200_000,
    }

    seed = 42
    order_count = 200

    # Reproduce the generated order IDs and their corresponding symbols.
    reference_simulator = AsyncMarketSimulator(
        base_prices=base_prices,
        seed=seed,
        price_variation_ticks=0,
    )

    async def collect_reference_orders():
        return [
            order
            async for order in reference_simulator.stream_orders(order_count)
        ]

    reference_orders = asyncio.run(collect_reference_orders())

    symbol_by_order_id = {
        order.order_id: order.symbol
        for order in reference_orders
    }

    simulator = AsyncMarketSimulator(
        base_prices=base_prices,
        seed=seed,
        price_variation_ticks=0,
    )

    result = asyncio.run(
        run_market_pipeline(
            simulator,
            order_count,
            tmp_path / "multi-symbol.mmap",
            buffer_capacity=5,
            book_capacity=256,
        )
    )

    assert result.orders_processed == order_count
    assert {book.symbol for book in result.books} == {
        "AAPL",
        "MSFT",
    }

    assert result.trade_count > 0

    for trade in result.trades:
        maker_symbol = symbol_by_order_id[trade.maker_order_id]
        taker_symbol = symbol_by_order_id[trade.taker_order_id]

        assert maker_symbol == trade.symbol
        assert taker_symbol == trade.symbol


def test_pipeline_rejects_nonempty_ring_buffer(tmp_path) -> None:
    """Prevent accidentally processing stale orders from an old run."""
    buffer_path = tmp_path / "nonempty.mmap"
    capacity = 4

    stale_order = Order(
        order_id="old-order",
        symbol="AAPL",
        side=Side.BUY,
        price_ticks=100_000,
        quantity=1,
    )

    with RingBuffer(buffer_path, capacity) as buffer:
        assert buffer.write(stale_order) is True

    simulator = AsyncMarketSimulator(seed=42)

    with pytest.raises(ValueError, match="empty ring buffer"):
        asyncio.run(
            run_market_pipeline(
                simulator,
                10,
                buffer_path,
                buffer_capacity=capacity,
            )
        )


def test_pipeline_rejects_invalid_order_count(tmp_path) -> None:
    """Reject invalid pipeline configuration before starting tasks."""
    simulator = AsyncMarketSimulator(seed=42)

    with pytest.raises(ValueError, match="greater than zero"):
        asyncio.run(
            run_market_pipeline(
                simulator,
                0,
                tmp_path / "invalid-count.mmap",
            )
        )


def test_pipeline_closes_ring_buffer_after_consumer_failure(
    tmp_path,
) -> None:
    """Verify the mmap file is released when the consumer fails."""

    class RepeatedBuySimulator(AsyncMarketSimulator):
        async def stream_orders(self, count: int):
            for index in range(count):
                yield Order(
                    order_id=f"cleanup-{index}",
                    symbol="AAPL",
                    side=Side.BUY,
                    price_ticks=100_000,
                    quantity=1,
                )

    simulator = RepeatedBuySimulator(
        base_prices={"AAPL": 100_000},
        seed=42,
        price_variation_ticks=0,
    )

    buffer_path = tmp_path / "pipeline-failure.mmap"

    # Capacity 1 means the second non-crossing buy order
    # causes the Cython order book to raise OverflowError.
    with pytest.raises(ExceptionGroup) as exc_info:
        asyncio.run(
            run_market_pipeline(
                simulator,
                3,
                buffer_path,
                buffer_capacity=2,
                book_capacity=1,
            )
        )

    assert any(
        isinstance(error, OverflowError)
        and "Order book capacity exhausted" in str(error)
        for error in exc_info.value.exceptions
    )

    # Successful rename and deletion verify the mmap file was released.
    renamed_path = tmp_path / "released-buffer.mmap"
    buffer_path.replace(renamed_path)
    renamed_path.unlink()


def test_pipeline_closes_ring_buffer_when_cancelled(tmp_path) -> None:
    """Verify ring-buffer cleanup when the pipeline is cancelled."""

    async def exercise_cancellation() -> None:
        started = asyncio.Event()
        never_resume = asyncio.Event()

        class BlockingSimulator(AsyncMarketSimulator):
            async def stream_orders(self, count: int):
                yield Order(
                    order_id="cancel-order",
                    symbol="AAPL",
                    side=Side.BUY,
                    price_ticks=100_000,
                    quantity=1,
                )

                started.set()
                await never_resume.wait()

        simulator = BlockingSimulator(seed=42)
        buffer_path = tmp_path / "cancelled-pipeline.mmap"

        pipeline_task = asyncio.create_task(
            run_market_pipeline(
                simulator,
                2,
                buffer_path,
                buffer_capacity=2,
                book_capacity=10,
            )
        )

        await asyncio.wait_for(started.wait(), timeout=2)

        pipeline_task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await pipeline_task

    asyncio.run(exercise_cancellation())

    # Verify that cancellation released the memory-mapped file.
    renamed_path = tmp_path / "cancelled-buffer-released.mmap"
    buffer_path = tmp_path / "cancelled-pipeline.mmap"

    buffer_path.replace(renamed_path)
    renamed_path.unlink()


def test_pipeline_closes_ring_buffer_after_producer_failure(
    tmp_path,
) -> None:
    """Verify buffer cleanup when the market simulator fails."""

    class FailingSimulator(AsyncMarketSimulator):
        async def stream_orders(self, count: int):
            yield Order(
                order_id="producer-failure-order",
                symbol="AAPL",
                side=Side.BUY,
                price_ticks=100_000,
                quantity=1,
            )

            raise RuntimeError("simulated producer failure")

    simulator = FailingSimulator(seed=42)
    buffer_path = tmp_path / "producer-failure.mmap"

    with pytest.raises(ExceptionGroup) as exc_info:
        asyncio.run(
            run_market_pipeline(
                simulator,
                2,
                buffer_path,
                buffer_capacity=2,
                book_capacity=10,
            )
        )

    assert any(
        isinstance(error, RuntimeError)
        and "simulated producer failure" in str(error)
        for error in exc_info.value.exceptions
    )

    # Verify that the mmap file is released after producer failure.
    renamed_path = tmp_path / "producer-failure-released.mmap"
    buffer_path.replace(renamed_path)
    renamed_path.unlink()
