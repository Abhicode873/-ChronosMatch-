
"""Tests for the ChronosMatch asynchronous market simulator."""

import asyncio

import pytest

from chronosmatch.core.models import Order, Side
from chronosmatch.simulator.market_simulator import AsyncMarketSimulator


def collect_orders(
    simulator: AsyncMarketSimulator,
    count: int,
) -> list[Order]:
    """Collect orders from the asynchronous generator."""

    async def collect() -> list[Order]:
        return [
            order
            async for order in simulator.stream_orders(count)
        ]

    return asyncio.run(collect())


def test_simulator_generates_valid_orders() -> None:
    simulator = AsyncMarketSimulator(seed=42)

    orders = collect_orders(simulator, 100)

    assert len(orders) == 100
    assert all(isinstance(order, Order) for order in orders)
    assert all(isinstance(order.side, Side) for order in orders)
    assert all(order.price_ticks > 0 for order in orders)
    assert all(order.quantity > 0 for order in orders)

    assert len({order.order_id for order in orders}) == 100
    assert simulator.generated_count == 100


def test_simulator_generates_multiple_symbols() -> None:
    simulator = AsyncMarketSimulator(seed=42)

    orders = collect_orders(simulator, 100)

    symbols = {order.symbol for order in orders}

    assert symbols.issubset({"AAPL", "MSFT", "GOOGL"})
    assert len(symbols) > 1


def test_simulator_generates_both_order_sides() -> None:
    simulator = AsyncMarketSimulator(seed=42)

    orders = collect_orders(simulator, 100)

    sides = {order.side for order in orders}

    assert Side.BUY in sides
    assert Side.SELL in sides


def test_same_seed_produces_reproducible_orders() -> None:
    first = AsyncMarketSimulator(seed=123)
    second = AsyncMarketSimulator(seed=123)

    first_orders = collect_orders(first, 50)
    second_orders = collect_orders(second, 50)

    first_data = [
        (
            order.order_id,
            order.symbol,
            order.side,
            order.price_ticks,
            order.quantity,
        )
        for order in first_orders
    ]

    second_data = [
        (
            order.order_id,
            order.symbol,
            order.side,
            order.price_ticks,
            order.quantity,
        )
        for order in second_orders
    ]

    assert first_data == second_data


def test_order_ids_remain_unique_across_multiple_streams() -> None:
    simulator = AsyncMarketSimulator(seed=42)

    first_batch = collect_orders(simulator, 5)
    second_batch = collect_orders(simulator, 5)

    all_ids = [
        order.order_id
        for order in first_batch + second_batch
    ]

    assert len(set(all_ids)) == 10
    assert simulator.generated_count == 10


def test_custom_simulator_configuration() -> None:
    simulator = AsyncMarketSimulator(
        base_prices={"TSLA": 250_000},
        seed=10,
        min_quantity=2,
        max_quantity=5,
        price_variation_ticks=3,
    )

    orders = collect_orders(simulator, 30)

    assert all(order.symbol == "TSLA" for order in orders)
    assert all(2 <= order.quantity <= 5 for order in orders)
    assert all(
        249_997 <= order.price_ticks <= 250_003
        for order in orders
    )


@pytest.mark.parametrize("count", [0, -1, True, 1.5])
def test_invalid_order_count_is_rejected(count: object) -> None:
    simulator = AsyncMarketSimulator(seed=42)

    async def collect() -> list[Order]:
        return [
            order
            async for order in simulator.stream_orders(count)  # type: ignore[arg-type]
        ]

    with pytest.raises(
        (TypeError, ValueError),
        match="count must be|count must be greater",
    ):
        asyncio.run(collect())


def test_invalid_base_price_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        AsyncMarketSimulator(base_prices={"AAPL": 0})


def test_invalid_quantity_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="quantity range"):
        AsyncMarketSimulator(
            min_quantity=10,
            max_quantity=5,
        )


def test_negative_price_variation_is_rejected() -> None:
    with pytest.raises(ValueError, match="variation"):
        AsyncMarketSimulator(price_variation_ticks=-1)


def test_negative_interval_is_rejected() -> None:
    with pytest.raises(ValueError, match="interval_seconds"):
        AsyncMarketSimulator(interval_seconds=-0.1)


def test_stream_allows_other_async_tasks_to_run() -> None:
    """Verify that order generation cooperatively yields to the event loop."""

    async def run_test() -> None:
        simulator = AsyncMarketSimulator(seed=42)
        observer_ran = asyncio.Event()
        observed_during_stream = False
        generated_orders: list[Order] = []

        async def observer() -> None:
            await asyncio.sleep(0)
            observer_ran.set()

        observer_task = asyncio.create_task(observer())

        async for order in simulator.stream_orders(3):
            generated_orders.append(order)

            if observer_ran.is_set():
                observed_during_stream = True

        await observer_task

        assert len(generated_orders) == 3
        assert observed_during_stream is True

    asyncio.run(run_test())
