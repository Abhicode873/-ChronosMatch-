
"""Repeatable baseline benchmark for the ChronosMatch Python order book."""

import argparse
import math
import platform
import time

from chronosmatch.core.models import Order, Side
from chronosmatch.core.order_book import OrderBook


def positive_int(value: str) -> int:
    """Parse a positive integer from the command line."""
    try:
        result = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "value must be a positive integer"
        ) from exc

    if result <= 0:
        raise argparse.ArgumentTypeError(
            "value must be greater than zero"
        )

    return result


def build_workload(order_count: int, prefix: str) -> list[Order]:
    """Build deterministic alternating buy/sell orders.

    Each buy rests briefly in the book, then the next sell crosses it.
    This creates one trade per pair and leaves the book empty at the end.
    Order construction is excluded from the timed benchmark.
    """
    if order_count <= 0 or order_count % 2 != 0:
        raise ValueError("order_count must be a positive even integer")

    orders: list[Order] = []

    for index in range(order_count // 2):
        orders.append(
            Order(
                order_id=f"{prefix}-buy-{index:08d}",
                symbol="AAPL",
                side=Side.BUY,
                price_ticks=101,
                quantity=1,
            )
        )
        orders.append(
            Order(
                order_id=f"{prefix}-sell-{index:08d}",
                symbol="AAPL",
                side=Side.SELL,
                price_ticks=100,
                quantity=1,
            )
        )

    return orders


def verify_result(
    book: OrderBook,
    orders: list[Order],
    trade_count: int,
) -> None:
    """Verify the benchmark workload completed as expected."""
    expected_trades = len(orders) // 2

    if trade_count != expected_trades:
        raise RuntimeError(
            f"Expected {expected_trades} trades, got {trade_count}"
        )

    if book.active_order_count != 0:
        raise RuntimeError(
            f"Expected an empty book, got {book.active_order_count} "
            "active orders"
        )


def run_throughput(orders: list[Order]) -> tuple[int, int]:
    """Measure total processing time without per-order timing calls."""
    book = OrderBook("AAPL")
    trade_count = 0

    start_ns = time.perf_counter_ns()

    for order in orders:
        trade_count += len(book.submit(order))

    elapsed_ns = time.perf_counter_ns() - start_ns
    verify_result(book, orders, trade_count)

    return elapsed_ns, trade_count


def run_latency(orders: list[Order]) -> list[int]:
    """Measure each submission separately, in nanoseconds."""
    book = OrderBook("AAPL")
    latencies_ns: list[int] = []
    trade_count = 0

    for order in orders:
        start_ns = time.perf_counter_ns()
        trades = book.submit(order)
        elapsed_ns = time.perf_counter_ns() - start_ns

        latencies_ns.append(elapsed_ns)
        trade_count += len(trades)

    verify_result(book, orders, trade_count)

    return latencies_ns


def percentile(sorted_values: list[int], percent: float) -> int:
    """Return a nearest-rank percentile from sorted integer values."""
    rank = math.ceil(percent / 100 * len(sorted_values))
    return sorted_values[max(0, rank - 1)]


def main() -> None:
    """Run the benchmark and print reproducible summary metrics."""
    parser = argparse.ArgumentParser(
        description="Benchmark the ChronosMatch Python order book."
    )
    parser.add_argument(
        "--orders",
        type=positive_int,
        default=20_000,
        help="Number of measured orders (must be even).",
    )
    parser.add_argument(
        "--warmup-orders",
        type=positive_int,
        default=2_000,
        help="Number of warm-up orders (must be even).",
    )

    args = parser.parse_args()

    if args.orders % 2 != 0:
        parser.error("--orders must be even")
    if args.warmup_orders % 2 != 0:
        parser.error("--warmup-orders must be even")

    warmup_orders = build_workload(
        args.warmup_orders,
        prefix="warmup",
    )
    run_throughput(warmup_orders)

    orders = build_workload(args.orders, prefix="baseline")

    # Measure throughput separately so per-order timing does not distort it.
    throughput_ns, trade_count = run_throughput(orders)

    # Run the same workload against a fresh book for latency measurements.
    latencies_ns = sorted(run_latency(orders))

    print("\nChronosMatch — Python Order Book Baseline")
    print("=" * 48)
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"Measured orders: {args.orders:,}")
    print(f"Trades executed: {trade_count:,}")
    print(f"Warm-up orders: {args.warmup_orders:,}")
    print()
    print(f"Throughput run time: {throughput_ns / 1e9:.6f} seconds")
    print(f"Throughput: {args.orders / (throughput_ns / 1e9):,.0f} orders/sec")
    print()
    print("Per-submission latency (separate instrumented run):")
    for label, quantile in (
        ("p50", 50),
        ("p95", 95),
        ("p99", 99),
        ("max", 100),
    ):
        latency_ns = percentile(latencies_ns, quantile)
        print(f"  {label:>3}: {latency_ns / 1_000:.3f} µs")

    print("\nWorkload: alternating AAPL buy/sell orders at fixed prices.")
    print("These are local microbenchmark results, not exchange latency.")


if __name__ == "__main__":
    main()
