"""Sustained-load tests for ring-buffer producer-consumer communication."""

import multiprocessing
import queue
import time
from typing import Any

from chronosmatch.core.models import Order, Side
from chronosmatch.ipc.ring_buffer import RingBuffer


def _make_sustained_order(index: int) -> Order:
    """Create a deterministic order for sustained-load testing."""
    return Order(
        order_id=f"sustained-{index:06d}",
        symbol="AAPL",
        side=Side.BUY if index % 2 == 0 else Side.SELL,
        price_ticks=100_000 + index,
        quantity=(index % 5) + 1,
        timestamp_ns=index + 1,
    )


def _sustained_producer(
    path: str,
    capacity: int,
    lock: Any,
    order_count: int,
    result_queue: Any,
) -> None:
    """Continuously publish orders and count full-buffer events."""
    try:
        full_events = 0
        deadline = time.monotonic() + 120.0

        with RingBuffer(path, capacity, lock=lock) as buffer:
            for index in range(order_count):
                order = _make_sustained_order(index)

                while not buffer.write(order):
                    full_events += 1

                    if time.monotonic() >= deadline:
                        raise TimeoutError("Producer timed out")

                    time.sleep(0.0001)

        result_queue.put(("producer_done", order_count, full_events))

    except Exception as exc:  # noqa: BLE001
        result_queue.put(("producer_error", repr(exc)))


def _sustained_consumer(
    path: str,
    capacity: int,
    lock: Any,
    order_count: int,
    result_queue: Any,
) -> None:
    """Continuously consume and validate orders."""
    try:
        received_count = 0
        empty_events = 0
        deadline = time.monotonic() + 120.0

        with RingBuffer(path, capacity, lock=lock) as buffer:
            while received_count < order_count:
                order = buffer.read()

                if order is None:
                    empty_events += 1

                    if time.monotonic() >= deadline:
                        raise TimeoutError("Consumer timed out")

                    time.sleep(0.0001)
                    continue

                expected = _make_sustained_order(received_count)

                if order != expected:
                    raise AssertionError(
                        f"Order mismatch at index {received_count}"
                    )

                received_count += 1

        result_queue.put(
            ("consumer_done", received_count, empty_events)
        )

    except Exception as exc:  # noqa: BLE001
        result_queue.put(("consumer_error", repr(exc)))


def test_ring_buffer_sustained_load_100000_orders(
    tmp_path,
) -> None:
    """Verify sustained cross-process delivery of 100,000 orders."""
    context = multiprocessing.get_context("spawn")

    path = tmp_path / "sustained-orders.mmap"
    capacity = 32
    order_count = 100_000

    result_queue = context.Queue()
    shared_lock = context.Lock()

    with RingBuffer(path, capacity):
        pass

    processes = [
        context.Process(
            target=_sustained_consumer,
            args=(
                str(path),
                capacity,
                shared_lock,
                order_count,
                result_queue,
            ),
        ),
        context.Process(
            target=_sustained_producer,
            args=(
                str(path),
                capacity,
                shared_lock,
                order_count,
                result_queue,
            ),
        ),
    ]

    start_time = time.perf_counter()

    try:
        for process in processes:
            process.start()

        messages = []
        deadline = time.monotonic() + 130.0

        while len(messages) < 2 and time.monotonic() < deadline:
            try:
                messages.append(result_queue.get(timeout=0.25))
            except queue.Empty:
                if all(not process.is_alive() for process in processes):
                    break

        for process in processes:
            process.join(timeout=5.0)

        elapsed = time.perf_counter() - start_time

        errors = [
            message for message in messages
            if message[0].endswith("_error")
        ]

        assert not errors, f"Worker errors: {errors}"
        assert len(messages) == 2, f"Missing worker results: {messages}"
        assert all(not process.is_alive() for process in processes)
        assert all(process.exitcode == 0 for process in processes)

        results = {
            message[0]: message[1:]
            for message in messages
        }

        assert results["producer_done"][0] == order_count
        assert results["consumer_done"][0] == order_count

        full_events = results["producer_done"][1]
        empty_events = results["consumer_done"][1]

        throughput = order_count / elapsed

        print(f"\nOrders transferred: {order_count:,}")
        print(f"Buffer capacity: {capacity}")
        print(f"Elapsed time: {elapsed:.4f} seconds")
        print(f"End-to-end throughput: {throughput:,.0f} orders/sec")
        print(f"Producer full-buffer events: {full_events:,}")
        print(f"Consumer empty-buffer events: {empty_events:,}")

    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5.0)

        result_queue.close()