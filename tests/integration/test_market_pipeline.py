
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
