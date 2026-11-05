"""Stress tests for high-volume ring-buffer communication."""

import multiprocessing
import queue
import time
from typing import Any

from chronosmatch.core.models import Order, Side
from chronosmatch.ipc.ring_buffer import RingBuffer


def _make_stress_order(index: int) -> Order:
    """Create a deterministic order for stress testing."""
    return Order(
        order_id=f"stress-order-{index:05d}",
        symbol="AAPL",
        side=Side.BUY if index % 2 == 0 else Side.SELL,
        price_ticks=100_000 + index,
        quantity=(index % 5) + 1,
        timestamp_ns=index + 1,
    )


def _stress_producer(
    path: str,
    capacity: int,
    lock: Any,
    order_count: int,
    result_queue: Any,
) -> None:
    """Publish a high volume of orders."""
    try:
        with RingBuffer(path, capacity, lock=lock) as buffer:
            deadline = time.monotonic() + 60.0

            for index in range(order_count):
                order = _make_stress_order(index)

                while not buffer.write(order):
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Producer timed out")

                    time.sleep(0.0001)

        result_queue.put(("producer_done", order_count))

    except Exception as exc:  # noqa: BLE001
        result_queue.put(("producer_error", repr(exc)))


def _stress_consumer(
    path: str,
    capacity: int,
    lock: Any,
    order_count: int,
    result_queue: Any,
) -> None:
    """Consume and validate every order."""
    try:
        received: list[Order] = []

        with RingBuffer(path, capacity, lock=lock) as buffer:
            deadline = time.monotonic() + 60.0

            while len(received) < order_count:
                order = buffer.read()

                if order is None:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Consumer timed out")

                    time.sleep(0.0001)
                    continue

                received.append(order)

        expected = [
            _make_stress_order(index)
            for index in range(order_count)
        ]

        result_queue.put(
            ("consumer_done", received == expected)
        )

    except Exception as exc:  # noqa: BLE001
        result_queue.put(("consumer_error", repr(exc)))


def test_ring_buffer_handles_10000_orders_across_processes(
    tmp_path,
) -> None:
    """Verify high-volume cross-process order delivery."""
    context = multiprocessing.get_context("spawn")

    path = tmp_path / "stress-orders.mmap"
    capacity = 8
    order_count = 10_000

    result_queue = context.Queue()
    shared_lock = context.Lock()

    with RingBuffer(path, capacity):
        pass

    processes = [
        context.Process(
            target=_stress_consumer,
            args=(
                str(path),
                capacity,
                shared_lock,
                order_count,
                result_queue,
            ),
        ),
        context.Process(
            target=_stress_producer,
            args=(
                str(path),
                capacity,
                shared_lock,
                order_count,
                result_queue,
            ),
        ),
    ]

    try:
        for process in processes:
            process.start()

        messages = []
        deadline = time.monotonic() + 70.0

        while len(messages) < 2 and time.monotonic() < deadline:
            try:
                messages.append(result_queue.get(timeout=0.25))
            except queue.Empty:
                if all(not process.is_alive() for process in processes):
                    break

        errors = [
            message for message in messages
            if message[0].endswith("_error")
        ]

        assert not errors, f"Worker errors: {errors}"
        assert len(messages) == 2, (
            f"Missing worker results: {messages}"
        )

        for process in processes:
            process.join(timeout=5.0)

        assert all(not p.is_alive() for p in processes)
        assert all(p.exitcode == 0 for p in processes)

        results = {
            message[0]: message[1]
            for message in messages
        }

        assert results["producer_done"] == order_count
        assert results["consumer_done"] is True

    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5.0)

        result_queue.close()

def test_ring_buffer_handles_50000_orders_with_timing(
    tmp_path,
) -> None:
    """Measure high-volume cross-process order delivery."""
    context = multiprocessing.get_context("spawn")

    path = tmp_path / "stress-orders-50000.mmap"
    capacity = 64
    order_count = 50_000

    result_queue = context.Queue()
    shared_lock = context.Lock()

    with RingBuffer(path, capacity):
        pass

    processes = [
        context.Process(
            target=_stress_consumer,
            args=(
                str(path),
                capacity,
                shared_lock,
                order_count,
                result_queue,
            ),
        ),
        context.Process(
            target=_stress_producer,
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
        deadline = time.monotonic() + 90.0

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
        assert len(messages) == 2, f"Missing results: {messages}"
        assert all(not p.is_alive() for p in processes)
        assert all(p.exitcode == 0 for p in processes)

        results = {
            message[0]: message[1]
            for message in messages
        }

        assert results["producer_done"] == order_count
        assert results["consumer_done"] is True

        throughput = order_count / elapsed

        print(f"\nOrders transferred: {order_count:,}")
        print(f"Buffer capacity: {capacity}")
        print(f"Total elapsed time: {elapsed:.4f} seconds")
        print(f"End-to-end throughput: {throughput:,.0f} orders/sec")

    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5.0)

        result_queue.close()