
"""Run the ChronosMatch asynchronous market simulator."""

import argparse
import asyncio
import math
import time
from collections import Counter

from chronosmatch.simulator.market_simulator import AsyncMarketSimulator


def positive_int(value: str) -> int:
    """Validate a positive integer argument."""
    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Value must be a positive integer"
        ) from exc

    if result <= 0:
        raise argparse.ArgumentTypeError(
            "Value must be greater than zero"
        )

    return result


def non_negative_float(value: str) -> float:
    """Validate a finite, non-negative floating-point argument."""
    try:
        result = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Value must be a number"
        ) from exc

    if not math.isfinite(result) or result < 0:
        raise argparse.ArgumentTypeError(
            "Value must be finite and non-negative"
        )

    return result


async def run_simulation(
    order_count: int,
    seed: int,
    interval_ms: float,
) -> None:
    """Generate orders and display a summary of market activity."""
    simulator = AsyncMarketSimulator(
        seed=seed,
        interval_seconds=interval_ms / 1_000,
    )

    symbol_counts: Counter[str] = Counter()
    side_counts: Counter[str] = Counter()
    samples = []

    start = time.perf_counter()

    async for order in simulator.stream_orders(order_count):
        symbol_counts[order.symbol] += 1
        side_counts[order.side.value] += 1

        if len(samples) < 10:
            samples.append(order)

    elapsed = time.perf_counter() - start

    print("\nChronosMatch — Async Market Simulator")
    print("=" * 48)
    print(f"Random seed: {seed}")
    print(f"Requested orders: {order_count:,}")
    print(f"Generated orders: {simulator.generated_count:,}")
    print(f"Configured interval: {interval_ms:.3f} ms")
    print(f"Execution time: {elapsed:.6f} seconds")

    if elapsed > 0:
        print(f"Generation rate: {order_count / elapsed:,.0f} orders/sec")

    print("\nOrders by symbol:")
    for symbol, count in sorted(symbol_counts.items()):
        print(f"  {symbol}: {count:,}")

    print("\nOrders by side:")
    for side, count in sorted(side_counts.items()):
        print(f"  {side}: {count:,}")

    print("\nFirst 10 generated orders:")
    for order in samples:
        print(
            f"  {order.order_id} | {order.symbol} | "
            f"{order.side.value} | "
            f"Price: {order.price_ticks} | "
            f"Quantity: {order.quantity}"
        )

    print("\nSimulation completed successfully.")


def main() -> None:
    """Parse arguments and start the asynchronous simulation."""
    parser = argparse.ArgumentParser(
        description="Run the ChronosMatch market simulator."
    )

    parser.add_argument(
        "--orders",
        type=positive_int,
        default=100,
        help="Number of orders to generate.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible order generation.",
    )

    parser.add_argument(
        "--interval-ms",
        type=non_negative_float,
        default=0,
        help="Delay between orders in milliseconds.",
    )

    args = parser.parse_args()

    asyncio.run(
        run_simulation(
            order_count=args.orders,
            seed=args.seed,
            interval_ms=args.interval_ms,
        )
    )


if __name__ == "__main__":
    main()
