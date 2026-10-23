"""Integration tests for ring-buffer communication across processes."""

import multiprocessing
import queue
import time
from typing import Any

from chronosmatch.core.models import Order, Side
from chronosmatch.ipc.ring_buffer import RingBuffer


def _make_order(index: int) -> Order:
    """Build a deterministic order for integration testing."""
    return Order(
        order_id=f"process-order-{index:04d}",
        symbol="AAPL",
        side=Side.BUY if index % 2 == 0 else Side.SELL,
        price_ticks=100_000 + index,
        quantity=(index % 5) + 1,
        timestamp_ns=index + 1,
    )


def _producer_worker(
    path: str,
    capacity: int,
    lock: Any,
    order_count: int,
    result_queue: Any,
) -> None:
    """Publish orders into the shared ring buffer."""
    try:
        with RingBuffer(path, capacity, lock=lock) as buffer:
            deadline = time.monotonic() + 15.0

            for index in range(order_count):
                order = _make_order(index)

                while not buffer.write(order):
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            "Producer timed out waiting for buffer space"
                        )
                    time.sleep(0.0005)

        result_queue.put(("producer_done", order_count))

    # Forward unexpected worker failures to the parent test process.
    except Exception as exc:  # noqa: BLE001
        result_queue.put(("producer_error", repr(exc)))


def _consumer_worker(
    path: str,
    capacity: int,
    lock: Any,
    order_count: int,
    result_queue: Any,
) -> None:
    """Consume records and verify their contents and FIFO order."""
    try:
        received: list[Order] = []

        with RingBuffer(path, capacity, lock=lock) as buffer:
            deadline = time.monotonic() + 15.0

            while len(received) < order_count:
                order = buffer.read()

                if order is None:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            "Consumer timed out waiting for an order"
                        )
                    time.sleep(0.0005)
                    continue

                received.append(order)

        expected = [
            _make_order(index) for index in range(order_count)
        ]
        result_queue.put(("consumer_done", received == expected))

    # Forward unexpected worker failures to the parent test process.
    except Exception as exc:  # noqa: BLE001
        result_queue.put(("consumer_error", repr(exc)))


def test_separate_processes_exchange_orders_without_corruption(
    tmp_path,
) -> None:
    """Verify cross-process sharing, integrity, and FIFO order."""
    context = multiprocessing.get_context("spawn")
    path = tmp_path / "process-shared.mmap"
    capacity = 7
    order_count = 250

    result_queue = context.Queue()
    shared_lock = context.Lock()

    # Create the backing file before either process starts.
    with RingBuffer(path, capacity):
        pass

    consumer = context.Process(
        target=_consumer_worker,
        args=(
            str(path),
            capacity,
            shared_lock,
            order_count,
            result_queue,
        ),
        name="chronosmatch-consumer",
    )
    producer = context.Process(
        target=_producer_worker,
        args=(
            str(path),
            capacity,
            shared_lock,
            order_count,
            result_queue,
        ),
        name="chronosmatch-producer",
    )
    processes = [consumer, producer]

    try:
        for process in processes:
            process.start()

        messages = []
        deadline = time.monotonic() + 20.0

        # Read results while workers run, avoiding queue shutdown deadlocks.
        while (
            len(messages) < len(processes)
            and time.monotonic() < deadline
        ):
            try:
                messages.append(result_queue.get(timeout=0.25))
            except queue.Empty:
                if all(not process.is_alive() for process in processes):
                    break

        worker_errors = [
            message
            for message in messages
            if message[0].endswith("_error")
        ]
        assert not worker_errors, f"Worker errors: {worker_errors}"

        assert len(messages) == len(processes), (
            f"Expected results from both workers; got {messages}; "
            f"exit codes: {[process.exitcode for process in processes]}"
        )

        for process in processes:
            process.join(timeout=5.0)

        assert all(
            not process.is_alive() for process in processes
        ), "A worker did not exit after reporting its result"

        assert all(
            process.exitcode == 0 for process in processes
        ), f"Unexpected worker exit codes: {[p.exitcode for p in processes]}"

        results = {
            message[0]: message[1]
            for message in messages
        }

        assert results.get("producer_done") == order_count
        assert results.get("consumer_done") is True

    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5.0)

        result_queue.close()