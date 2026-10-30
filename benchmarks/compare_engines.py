
"""Compare the Python and Cython ChronosMatch matching engines."""

import argparse
import math
import platform
import time
from statistics import median

from chronosmatch.core.cython_order_book import (
    BUY,
    SELL,
    CythonOrderBook,
)

from chronosmatch.core.models import Order, Side
from chronosmatch.core.order_book import OrderBook


def positive_int(value: str) -> int:
    """Parse a positive integer argument."""
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


def build_workload(order_count: int):
    """Create equivalent pre-built orders for both engines.

    Every buy rests first. The following sell crosses it, producing
    one trade per pair. Order preparation is outside timed sections.
    """
    if order_count <= 0 or order_count % 2 != 0:
        raise ValueError("order_count must be a positive even integer")

    workload = []
    python_id_map = {}

    for index in range(order_count // 2):
        buy_id = f"bench-buy-{index:08d}"
        sell_id = f"bench-sell-{index:08d}"

        buy_numeric_id = index * 2 + 1
        sell_numeric_id = index * 2 + 2

        buy_order = Order(
            order_id=buy_id,
            symbol="AAPL",
            side=Side.BUY,
            price_ticks=101,
            quantity=1,
        )
        sell_order = Order(
            order_id=sell_id,
            symbol="AAPL",
            side=Side.SELL,
            price_ticks=100,
            quantity=1,
        )

        workload.append(
            (
                buy_order,
                (buy_numeric_id, BUY, 101, 1),
            )
        )
        workload.append(
            (
                sell_order,
                (sell_numeric_id, SELL, 100, 1),
            )
        )

        python_id_map[buy_id] = buy_numeric_id
        python_id_map[sell_id] = sell_numeric_id

    return workload, python_id_map


def verify_book(book, trade_count: int, order_count: int) -> None:
    """Check the final state of a completed benchmark run."""
    expected_trades = order_count // 2

    if trade_count != expected_trades:
        raise RuntimeError(
            f"Expected {expected_trades} trades, got {trade_count}"
        )

    if book.active_order_count != 0:
        raise RuntimeError(
            f"Expected empty book, got {book.active_order_count} "
            "active orders"
        )


def verify_equivalent_results(workload, python_id_map) -> None:
    """Compare the complete trade sequences from both implementations."""
    python_book = OrderBook("AAPL")
    cython_book = CythonOrderBook(capacity=1024)

    python_trades = []
    cython_trades = []

    for python_order, cython_order in workload:
        for trade in python_book.submit(python_order):
            python_trades.append(
                (
                    python_id_map[trade.maker_order_id],
                    python_id_map[trade.taker_order_id],
                    trade.price_ticks,
                    trade.quantity,
                )
            )

        cython_trades.extend(cython_book.submit(*cython_order))

    if python_trades != cython_trades:
        raise RuntimeError(
            "Python and Cython produced different trade sequences"
        )

    expected_trades = len(workload) // 2

    verify_book(
        python_book,
        len(python_trades),
        len(workload),
    )
    verify_book(
        cython_book,
        len(cython_trades),
        len(workload),
    )

    if len(python_trades) != expected_trades:
        raise RuntimeError("Unexpected trade count")

    print(
        f"Correctness: PASSED ({expected_trades:,} identical trades)"
    )


def run_python_throughput(workload):
    """Measure Python engine throughput without per-order timers."""
    book = OrderBook("AAPL")
    trade_count = 0

    start_ns = time.perf_counter_ns()

    for python_order, _ in workload:
        trade_count += len(book.submit(python_order))

    elapsed_ns = time.perf_counter_ns() - start_ns

    verify_book(book, trade_count, len(workload))

    return elapsed_ns


def run_cython_throughput(workload):
    """Measure Cython engine throughput without per-order timers."""
    book = CythonOrderBook(capacity=1024)
    trade_count = 0

    start_ns = time.perf_counter_ns()

    for _, cython_order in workload:
        trade_count += len(book.submit(*cython_order))

    elapsed_ns = time.perf_counter_ns() - start_ns

    verify_book(book, trade_count, len(workload))

    return elapsed_ns


def run_python_latency(workload):
    """Collect separately instrumented Python submission latencies."""
    book = OrderBook("AAPL")
    latencies = []
    trade_count = 0

    for python_order, _ in workload:
        start_ns = time.perf_counter_ns()
        trades = book.submit(python_order)
        elapsed_ns = time.perf_counter_ns() - start_ns

        latencies.append(elapsed_ns)
        trade_count += len(trades)

    verify_book(book, trade_count, len(workload))

    return latencies


def run_cython_latency(workload):
    """Collect separately instrumented Cython submission latencies."""
    book = CythonOrderBook(capacity=1024)
    latencies = []
    trade_count = 0

    for _, cython_order in workload:
        start_ns = time.perf_counter_ns()
        trades = book.submit(*cython_order)
        elapsed_ns = time.perf_counter_ns() - start_ns

        latencies.append(elapsed_ns)
        trade_count += len(trades)

    verify_book(book, trade_count, len(workload))

    return latencies


def percentile(values, percent: float) -> int:
    """Calculate a nearest-rank percentile."""
    sorted_values = sorted(values)
    rank = math.ceil(percent / 100 * len(sorted_values))

    return sorted_values[max(0, rank - 1)]


def calculate_throughput(order_count: int, elapsed_ns: int) -> float:
    """Convert execution time to orders per second."""
    if elapsed_ns <= 0:
        raise ValueError("Elapsed time must be positive")

    return order_count / (elapsed_ns / 1_000_000_000)


def print_latency_results(label: str, latencies: list[int]) -> None:
    """Print latency percentiles in microseconds."""
    print(f"\n{label}:")

    for name, value in (
        ("p50", percentile(latencies, 50)),
        ("p95", percentile(latencies, 95)),
        ("p99", percentile(latencies, 99)),
    ):
        print(f"  {name}: {value / 1_000:.3f} us")


def main() -> None:
    """Run correctness checks and performance comparisons."""
    parser = argparse.ArgumentParser(
        description="Compare ChronosMatch Python and Cython engines."
    )

    parser.add_argument(
        "--orders",
        type=positive_int,
        default=20_000,
        help="Number of measured orders; must be even.",
    )

    parser.add_argument(
        "--warmup-orders",
        type=positive_int,
        default=2_000,
        help="Number of warm-up orders; must be even.",
    )

    parser.add_argument(
        "--trials",
        type=positive_int,
        default=5,
        help="Number of throughput and latency trials.",
    )

    args = parser.parse_args()

    if args.orders % 2 != 0:
        parser.error("--orders must be even")

    if args.warmup_orders % 2 != 0:
        parser.error("--warmup-orders must be even")

    warmup, _ = build_workload(args.warmup_orders)
    workload, python_id_map = build_workload(args.orders)

    print("\nChronosMatch — Python vs Cython")
    print("=" * 52)
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"Measured orders: {args.orders:,}")
    print(f"Warm-up orders: {args.warmup_orders:,}")
    print(f"Trials: {args.trials}")
    print("Cython book capacity: 1,024")

    # Validate semantics before collecting performance measurements.
    verify_equivalent_results(workload, python_id_map)

    # Warm up both implementations.
    run_python_throughput(warmup)
    run_cython_throughput(warmup)

    python_rates = []
    cython_rates = []

    print("\nRunning throughput trials...")

    # Alternate execution order to reduce systematic ordering bias.
    for trial in range(args.trials):
        if trial % 2 == 0:
            python_ns = run_python_throughput(workload)
            cython_ns = run_cython_throughput(workload)
        else:
            cython_ns = run_cython_throughput(workload)
            python_ns = run_python_throughput(workload)

        python_rates.append(
            calculate_throughput(args.orders, python_ns)
        )
        cython_rates.append(
            calculate_throughput(args.orders, cython_ns)
        )

        print(
            f"Trial {trial + 1}: "
            f"Python {python_rates[-1]:,.0f} orders/sec | "
            f"Cython {cython_rates[-1]:,.0f} orders/sec"
        )

    python_median = median(python_rates)
    cython_median = median(cython_rates)

    print("\nMedian throughput")
    print(f"Python: {python_median:,.0f} orders/sec")
    print(f"Cython: {cython_median:,.0f} orders/sec")
    print(f"Cython/Python ratio: {cython_median / python_median:.2f}x")

    # Measure latency separately from the throughput experiment.
    print("\nRunning separately instrumented latency trials...")

    python_latencies = []
    cython_latencies = []

    for _ in range(args.trials):
        python_latencies.extend(run_python_latency(workload))
        cython_latencies.extend(run_cython_latency(workload))

    print_latency_results("Python latency", python_latencies)
    print_latency_results("Cython latency", cython_latencies)

    print("\nBenchmark notes:")
    print("- Orders are generated before timed execution.")
    print("- Both engines process equivalent order flows.")
    print("- Throughput and per-order latency use separate runs.")
    print("- Results are local microbenchmarks, not exchange latency.")
    print("- Cython accepts integer IDs and primitive order fields.")


if __name__ == "__main__":
    main()
