
"""Tests for synchronized access through multiple ring-buffer handles."""

import multiprocessing

from chronosmatch.core.models import Order, Side
from chronosmatch.ipc.ring_buffer import RingBuffer


def make_order(order_id: str, price_ticks: int = 100) -> Order:
    """Create a deterministic order for synchronization tests."""
    return Order(
        order_id=order_id,
        symbol="AAPL",
        side=Side.BUY,
        price_ticks=price_ticks,
        quantity=1,
        timestamp_ns=123456789,
    )


def test_two_handles_observe_shared_records(tmp_path) -> None:
    path = tmp_path / "shared.mmap"
    lock = multiprocessing.get_context("spawn").Lock()
    first = make_order("order-1")
    second = make_order("order-2", price_ticks=101)

    # Initialize the file before opening two handles.
    with RingBuffer(path, capacity=2):
        pass

    with (
        RingBuffer(path, capacity=2, lock=lock) as writer,
        RingBuffer(path, capacity=2, lock=lock) as reader,
    ):
        assert writer.write(first) is True

        # The second handle must refresh its view of shared metadata.
        assert reader.size == 1
        assert reader.read() == first
        assert writer.size == 0

        assert writer.write(second) is True
        assert reader.read() == second
        assert reader.is_empty is True


def test_full_state_stays_consistent_between_handles(tmp_path) -> None:
    path = tmp_path / "shared-full.mmap"
    lock = multiprocessing.get_context("spawn").Lock()

    first = make_order("order-1")
    second = make_order("order-2")
    third = make_order("order-3")

    with RingBuffer(path, capacity=2):
        pass

    with (
        RingBuffer(path, capacity=2, lock=lock) as writer,
        RingBuffer(path, capacity=2, lock=lock) as reader,
    ):
        assert writer.write(first) is True
        assert writer.write(second) is True

        assert reader.is_full is True
        assert writer.write(third) is False

        assert reader.read() == first
        assert writer.is_full is False

        assert writer.write(third) is True
        assert reader.read() == second
        assert reader.read() == third
        assert reader.is_empty is True
