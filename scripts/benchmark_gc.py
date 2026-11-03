
"""Compare ChronosMatch pipeline performance with GC enabled and disabled."""

import argparse
import asyncio
import gc
import statistics
import tempfile
import tracemalloc
from dataclasses import dataclass
from pathlib import Path

from chronosmatch.simulator.market_simulator import AsyncMarketSimulator
from chronosmatch.simulator.pipeline import run_market_pipeline


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """Measurements from one garbage-collection experiment."""

    elapsed_ns: int
    throughput: float
    trades: int
    p50_ns: int
    p95_ns: int
    p99_ns: int
    gc_collections: int
    current_memory_bytes: int | None = None
    peak_memory_bytes: int | None = None


def positive_int(value: str) -> int:
    """Parse a positive integer argument."""
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


async def execute_pipeline(
    order_count: int,
    seed: int,
    buffer_capacity: int,
):
    """Execute one pipeline run using a fresh temporary buffer."""
    simulator = AsyncMarketSimulator(seed=seed)

    with tempfile.TemporaryDirectory(
        prefix="chronosmatch-gc-"
    ) as directory:
        buffer_path = Path(directory) / "market.mmap"

        result = await run_market_pipeline(
            simulator,
            order_count,
            buffer_path,
            buffer_capacity=buffer_capacity,
            book_capacity=order_count,
        )

    return result


def run_experiment(
    order_count: int,
    seed: int,
    buffer_capacity: int,
    *,
    gc_enabled: bool,
    measure_memory: bool = False,
) -> ExperimentResult:
    """Run one controlled experiment and restore the original GC state."""
    original_gc_state = gc.isenabled()
    tracing_started = False

    # Start each experiment after a clean collection.
    gc.collect()

    if gc_enabled:
        gc.enable()
    else:
        gc.disable()

    collections_before = sum(
        generation["collections"] for generation in gc.get_stats()
    )

    try:
        # Memory tracing runs separately from timing experiments.
        if measure_memory:
            if tracemalloc.is_tracing():
                raise RuntimeError(
                    "Another memory-tracing session is already active"
                )

            tracemalloc.start()
            tracing_started = True

        result = asyncio.run(
            execute_pipeline(
                order_count,
                seed,
                buffer_capacity,
            )
        )

        metrics = result.metrics

        if (
            metrics.latency_p50_ns is None
            or metrics.latency_p95_ns is None
            or metrics.latency_p99_ns is None
        ):
            raise RuntimeError("Pipeline returned incomplete latency metrics")

        collections_after = sum(
            generation["collections"] for generation in gc.get_stats()
        )

        current_memory = None
        peak_memory = None

        if measure_memory:
            current_memory, peak_memory = tracemalloc.get_traced_memory()

        if result.orders_processed != order_count:
            raise RuntimeError("Not all orders were processed")

        return ExperimentResult(
            elapsed_ns=metrics.elapsed_ns,
            throughput=metrics.throughput_orders_per_second,
            trades=result.trade_count,
            p50_ns=metrics.latency_p50_ns,
            p95_ns=metrics.latency_p95_ns,
            p99_ns=metrics.latency_p99_ns,
            gc_collections=collections_after - collections_before,
            current_memory_bytes=current_memory,
            peak_memory_bytes=peak_memory,
        )

    finally:
        if tracing_started and tracemalloc.is_tracing():
            tracemalloc.stop()

        # Never leave the caller's garbage-collection setting changed.
        if original_gc_state:
            gc.enable()
        else:
            gc.disable()


def print_condition(
    label: str,
    results: list[ExperimentResult],
) -> None:
    """Print median results for one GC configuration."""
    print(f"\n{label}")
    print("-" * 42)

    print(
        "Median pipeline time: "
        f"{statistics.median(r.elapsed_ns for r in results) / 1e6:.3f} ms"
    )
    print(
        "Median throughput: "
        f"{statistics.median(r.throughput for r in results):,.0f} orders/sec"
    )
    print(
        "Median p50 latency: "
        f"{statistics.median(r.p50_ns for r in results) / 1_000:.3f} us"
    )
    print(
        "Median p95 latency: "
        f"{statistics.median(r.p95_ns for r in results) / 1_000:.3f} us"
    )
    print(
        "Median p99 latency: "
        f"{statistics.median(r.p99_ns for r in results) / 1_000:.3f} us"
    )
    print(
        "Median GC collections: "
        f"{statistics.median(r.gc_collections for r in results):.1f}"
    )


def main() -> None:
    """Run GC timing and separate memory experiments."""
    parser = argparse.ArgumentParser(
        description="Compare ChronosMatch with automatic GC enabled/disabled."
    )

    parser.add_argument(
        "--orders",
        type=positive_int,
        default=5_000,
        help="Number of simulated orders per trial.",
    )

    parser.add_argument(
        "--trials",
        type=positive_int,
        default=3,
        help="Number of timing trials for each GC configuration.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for reproducible workloads.",
    )

    args = parser.parse_args()
    buffer_capacity = 32

    print("\nChronosMatch — Garbage Collection Experiment")
    print("=" * 52)
    print(f"Orders per trial: {args.orders:,}")
    print(f"Timing trials per condition: {args.trials}")
    print(f"Random seed: {args.seed}")
    print(f"Ring-buffer capacity: {buffer_capacity}")

    print("\nWarming up both configurations...")

    warmup_orders = min(args.orders, 1_000)

    run_experiment(
        warmup_orders,
        args.seed,
        buffer_capacity,
        gc_enabled=True,
    )
    run_experiment(
        warmup_orders,
        args.seed,
        buffer_capacity,
        gc_enabled=False,
    )

    enabled_results = []
    disabled_results = []

    print("\nRunning timing experiments...")

    # Alternate the order of conditions to reduce systematic bias.
    for trial in range(args.trials):
        conditions = (
            (True, False) if trial % 2 == 0 else (False, True)
        )

        for enabled in conditions:
            result = run_experiment(
                args.orders,
                args.seed,
                buffer_capacity,
                gc_enabled=enabled,
            )

            target = enabled_results if enabled else disabled_results
            target.append(result)

        print(f"Completed timing trial {trial + 1}/{args.trials}")

    print_condition("Automatic GC ENABLED", enabled_results)
    print_condition("Automatic GC DISABLED", disabled_results)

    # Compare memory in separate traced runs so tracemalloc overhead
    # does not distort the throughput measurements.
    print("\nRunning separate memory experiments...")

    enabled_memory = run_experiment(
        args.orders,
        args.seed,
        buffer_capacity,
        gc_enabled=True,
        measure_memory=True,
    )

    disabled_memory = run_experiment(
        args.orders,
        args.seed,
        buffer_capacity,
        gc_enabled=False,
        measure_memory=True,
    )

    print("\nTraced memory usage")
    print("-" * 42)
    print(
        "GC enabled peak: "
        f"{enabled_memory.peak_memory_bytes / (1024 * 1024):.3f} MB"
    )
    print(
        "GC disabled peak: "
        f"{disabled_memory.peak_memory_bytes / (1024 * 1024):.3f} MB"
    )

    print("\nExperiment notes:")
    print("- Both conditions use identical order-generation seeds.")
    print("- Each trial starts with a garbage-collection pass.")
    print("- Memory tracing is separate from timing measurements.")
    print("- Disabling cyclic GC does not disable reference counting.")
    print("- Results are workload- and machine-dependent.")
    print("- The original GC state is restored after every experiment.")

    print("\nGarbage-collection experiment completed successfully.")


if __name__ == "__main__":
    main()
