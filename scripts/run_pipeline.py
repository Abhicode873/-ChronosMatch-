
"""Run the complete ChronosMatch asynchronous execution pipeline."""

import argparse
import asyncio
import math
import tempfile
import time
from collections import Counter
from pathlib import Path

from chronosmatch.simulator.market_simulator import AsyncMarketSimulator
from chronosmatch.simulator.pipeline import run_market_pipeline


def positive_int(value: str) -> int:
    """Parse a positive integer."""
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
    """Parse a finite, non-negative floating-point value."""
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


async def run_demo(
    order_count: int,
    seed: int,
    buffer_capacity: int,
    interval_ms: float,
) -> None:
    """Execute the integrated market pipeline and print its results."""
    simulator = AsyncMarketSimulator(
        seed=seed,
        interval_seconds=interval_ms / 1_000,
    )

    # Use a temporary file so each demonstration starts with a fresh buffer.
    with tempfile.TemporaryDirectory(
        prefix="chronosmatch-"
    ) as directory:
        buffer_path = Path(directory) / "market.mmap"

        start = time.perf_counter()

        result = await run_market_pipeline(
            simulator,
            order_count,
            buffer_path,
            buffer_capacity=buffer_capacity,
        )

        elapsed = time.perf_counter() - start

    # Recover per-symbol order totals from generated and processed counts
    # is not possible from the summary alone; trade totals are reported below.
    symbol_trades = Counter(
        trade.symbol for trade in result.trades
    )

    print("\nChronosMatch — End-to-End Backend Pipeline")
    print("=" * 52)
    print(f"Random seed: {seed}")
    print(f"Orders generated: {result.orders_generated:,}")
    print(f"Orders processed: {result.orders_processed:,}")
    print(f"Trades executed: {result.trade_count:,}")
    print(f"Execution time: {elapsed:.6f} seconds")
    print(f"Pipeline rate: {order_count / elapsed:,.0f} orders/sec")
    print(f"Ring-buffer capacity: {buffer_capacity}")
    print(f"Buffer high-watermark: {result.buffer_high_watermark}")

    print("\nTrades by symbol:")
    if symbol_trades:
        for symbol, count in sorted(symbol_trades.items()):
            print(f"  {symbol}: {count:,}")
    else:
        print("  No trades in this run.")

    print("\nFinal order-book state:")
    for book in result.books:
        print(
            f"  {book.symbol}: active={book.active_order_count}, "
            f"best_bid={book.best_bid}, best_ask={book.best_ask}"
        )

    print("\nFirst 10 executed trades:")
    for trade in result.trades[:10]:
        print(
            f"  {trade.symbol} | "
            f"Maker: {trade.maker_order_id} | "
            f"Taker: {trade.taker_order_id} | "
            f"Price: {trade.price_ticks} | "
            f"Quantity: {trade.quantity}"
        )

    if result.orders_processed != order_count:
        raise RuntimeError("Not all generated orders were processed")

    print("\nEnd-to-end pipeline completed successfully.")


def main() -> None:
    """Parse command-line arguments and run the demo."""
    parser = argparse.ArgumentParser(
        description="Run the ChronosMatch end-to-end backend pipeline."
    )

    parser.add_argument(
        "--orders",
        type=positive_int,
        default=1_000,
        help="Number of simulated orders.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )

    parser.add_argument(
        "--buffer-capacity",
        type=positive_int,
        default=16,
        help="Memory-mapped ring-buffer capacity.",
    )

    parser.add_argument(
        "--interval-ms",
        type=non_negative_float,
        default=0,
        help="Delay between generated orders in milliseconds.",
    )

    args = parser.parse_args()

    asyncio.run(
        run_demo(
            args.orders,
            args.seed,
            args.buffer_capacity,
            args.interval_ms,
        )
    )


if __name__ == "__main__":
    main()
