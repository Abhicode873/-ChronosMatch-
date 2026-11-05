
"""End-to-end asynchronous market pipeline for ChronosMatch."""

import asyncio
import math
from dataclasses import dataclass
from pathlib import Path
from time import monotonic_ns, perf_counter_ns

from chronosmatch.core.cython_order_book import (
    BUY,
    SELL,
    CythonOrderBook,
)
from chronosmatch.ipc.ring_buffer import RingBuffer
from chronosmatch.monitoring.metrics import (
    MetricsCollector,
    MetricsSnapshot,
)
from chronosmatch.simulator.market_simulator import AsyncMarketSimulator


@dataclass(frozen=True, slots=True)
class ExecutedTrade:
    """Trade produced by the Cython matching engine."""

    symbol: str
    maker_order_id: str
    taker_order_id: str
    price_ticks: int
    quantity: int


@dataclass(frozen=True, slots=True)
class BookSummary:
    """Final state of one symbol's order book."""

    symbol: str
    active_order_count: int
    best_bid: int | None
    best_ask: int | None


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Summary of one completed market simulation."""

    orders_generated: int
    orders_processed: int
    trades: tuple[ExecutedTrade, ...]
    books: tuple[BookSummary, ...]
    buffer_high_watermark: int
    metrics: MetricsSnapshot

    @property
    def trade_count(self) -> int:
        """Return the number of executions."""
        return len(self.trades)


async def run_market_pipeline(
    simulator: AsyncMarketSimulator,
    order_count: int,
    buffer_path: str | Path,
    *,
    buffer_capacity: int = 64,
    book_capacity: int = 1024,
    poll_interval_seconds: float = 0.0001,
) -> PipelineResult:
    """Generate, transfer, and match simulated orders asynchronously.

    The producer generates orders and writes them to the memory-mapped
    ring buffer. The consumer reads, decodes, and submits them to a
    separate Cython order book for each trading symbol.

    Metrics include:
    - End-to-end order processing latency.
    - Total processed orders and executed trades.
    - Pipeline throughput.
    - Ring-buffer high-watermark.
    """
    if not isinstance(simulator, AsyncMarketSimulator):
        raise TypeError("simulator must be an AsyncMarketSimulator")

    if type(order_count) is not int:
        raise TypeError("order_count must be an integer")

    if order_count <= 0:
        raise ValueError("order_count must be greater than zero")

    if type(buffer_capacity) is not int or buffer_capacity <= 0:
        raise ValueError("buffer_capacity must be a positive integer")

    if type(book_capacity) is not int or book_capacity <= 0:
        raise ValueError("book_capacity must be a positive integer")

    if isinstance(poll_interval_seconds, bool) or not isinstance(
        poll_interval_seconds, (int, float)
    ):
        raise TypeError("poll_interval_seconds must be a number")

    if (
        not math.isfinite(poll_interval_seconds)
        or poll_interval_seconds < 0
    ):
        raise ValueError(
            "poll_interval_seconds must be finite and non-negative"
        )

    generated_count = 0
    processed_count = 0
    next_engine_id = 0

    books: dict[str, CythonOrderBook] = {}
    engine_id_to_order_id: dict[int, str] = {}
    executions: list[ExecutedTrade] = []

    metrics_collector = MetricsCollector()
    pipeline_started_ns = perf_counter_ns()

    with RingBuffer(buffer_path, buffer_capacity) as buffer:
        if buffer.size != 0:
            raise ValueError(
                "Pipeline requires an empty ring buffer"
            )

        async def producer() -> None:
            """Generate orders and publish them to shared memory."""
            nonlocal generated_count

            async for order in simulator.stream_orders(order_count):
                while True:
                    written, buffer_size = buffer.write_with_size(order)

                    if written:
                        break

                    await asyncio.sleep(poll_interval_seconds)

                generated_count += 1

                # Record occupancy returned from the existing write lock.
                metrics_collector.record_buffer_size(buffer_size)

        async def consumer() -> None:
            """Read orders and execute them in symbol-specific books."""
            nonlocal processed_count, next_engine_id

            while processed_count < order_count:
                order = buffer.read()

                if order is None:
                    await asyncio.sleep(poll_interval_seconds)
                    continue

                # Assign an internal numeric ID for the Cython engine.
                next_engine_id += 1
                engine_id = next_engine_id

                engine_id_to_order_id[engine_id] = order.order_id

                # Each trading symbol gets its own independent book.
                book = books.get(order.symbol)

                if book is None:
                    book = CythonOrderBook(capacity=book_capacity)
                    books[order.symbol] = book

                side_code = BUY if order.side.value == "BUY" else SELL

                # Submit the decoded order to the matching engine.
                trades = book.submit(
                    engine_id,
                    side_code,
                    order.price_ticks,
                    order.quantity,
                )

                for maker_id, taker_id, price, quantity in trades:
                    executions.append(
                        ExecutedTrade(
                            symbol=order.symbol,
                            maker_order_id=engine_id_to_order_id[maker_id],
                            taker_order_id=engine_id_to_order_id[taker_id],
                            price_ticks=price,
                            quantity=quantity,
                        )
                    )

                # Measure from simulator order creation to completed matching.
                latency_ns = max(
                    0,
                    monotonic_ns() - order.timestamp_ns,
                )

                metrics_collector.record_order(
                    latency_ns=latency_ns,
                    trades=len(trades),
                )

                processed_count += 1

        # If either task fails, TaskGroup cancels the other task.
        async with asyncio.TaskGroup() as task_group:
            task_group.create_task(producer())
            task_group.create_task(consumer())

        book_summaries = tuple(
            BookSummary(
                symbol=symbol,
                active_order_count=book.active_order_count,
                best_bid=book.best_bid,
                best_ask=book.best_ask,
            )
            for symbol, book in sorted(books.items())
        )

    # Capture complete pipeline execution time.
    elapsed_ns = perf_counter_ns() - pipeline_started_ns

    metrics_snapshot = metrics_collector.snapshot(
        elapsed_ns=elapsed_ns,
    )

    return PipelineResult(
        orders_generated=generated_count,
        orders_processed=processed_count,
        trades=tuple(executions),
        books=book_summaries,
        buffer_high_watermark=metrics_snapshot.buffer_high_watermark,
        metrics=metrics_snapshot,
    )
