
"""Tests for the ChronosMatch memory-mapped ring buffer."""

import pytest

from chronosmatch.core.models import Order, Side
from chronosmatch.ipc.ring_buffer import RingBuffer


def make_order(
    order_id: str,
    side: Side = Side.BUY,
    price_ticks: int = 100,
    quantity: int = 1,
) -> Order:
    """Create a deterministic test order."""
    return Order(
        order_id=order_id,
        symbol="AAPL",
        side=side,
        price_ticks=price_ticks,
        quantity=quantity,
        timestamp_ns=123456789,
    )


def test_new_buffer_starts_empty(tmp_path) -> None:
    with RingBuffer(tmp_path / "orders.mmap", capacity=2) as ring:
        assert ring.capacity == 2
        assert ring.is_empty is True
        assert ring.is_full is False
        assert ring.size == 0
        assert ring.read() is None


def test_write_and_read_round_trip(tmp_path) -> None:
    order = make_order("order-1")

    with RingBuffer(tmp_path / "orders.mmap", capacity=2) as ring:
        assert ring.write(order) is True
        assert ring.read() == order
        assert ring.is_empty is True


def test_records_are_read_in_fifo_order(tmp_path) -> None:
    first = make_order("order-1")
    second = make_order("order-2", Side.SELL)
    third = make_order("order-3", price_ticks=105)

    with RingBuffer(tmp_path / "orders.mmap", capacity=3) as ring:
        assert ring.write(first) is True
        assert ring.write(second) is True
        assert ring.write(third) is True

        assert ring.read() == first
        assert ring.read() == second
        assert ring.read() == third
        assert ring.read() is None


def test_full_buffer_rejects_write_without_overwriting(tmp_path) -> None:
    first = make_order("order-1")
    second = make_order("order-2")
    third = make_order("order-3")

    with RingBuffer(tmp_path / "orders.mmap", capacity=2) as ring:
        assert ring.write(first) is True
        assert ring.write(second) is True
        assert ring.is_full is True

        assert ring.write(third) is False
        assert ring.size == 2
        assert ring.read() == first
        assert ring.read() == second


def test_buffer_wraps_around_and_reuses_slots(tmp_path) -> None:
    first = make_order("order-1")
    second = make_order("order-2")
    third = make_order("order-3")

    with RingBuffer(tmp_path / "orders.mmap", capacity=2) as ring:
        assert ring.write(first) is True
        assert ring.write(second) is True
        assert ring.read() == first

        assert ring.write(third) is True

        assert ring.read() == second
        assert ring.read() == third
        assert ring.is_empty is True


@pytest.mark.parametrize(
    "capacity",
    [0, -1],
)
def test_nonpositive_capacity_is_rejected(
    tmp_path,
    capacity: int,
) -> None:
    with pytest.raises(ValueError):
        RingBuffer(tmp_path / "orders.mmap", capacity=capacity)


def test_unread_records_survive_reopening(tmp_path) -> None:
    path = tmp_path / "orders.mmap"
    first = make_order("order-1")
    second = make_order("order-2", Side.SELL)

    with RingBuffer(path, capacity=2) as ring:
        assert ring.write(first) is True
        assert ring.write(second) is True

    with RingBuffer(path, capacity=2) as ring:
        assert ring.read() == first
        assert ring.read() == second
        assert ring.is_empty is True


def test_reopening_with_different_capacity_is_rejected(tmp_path) -> None:
    path = tmp_path / "orders.mmap"

    with RingBuffer(path, capacity=2):
        pass

    with pytest.raises(ValueError):
        RingBuffer(path, capacity=3)


def test_corrupted_existing_buffer_is_rejected(tmp_path) -> None:
    path = tmp_path / "orders.mmap"
    path.write_bytes(b"invalid buffer header")

    with pytest.raises(ValueError):
        RingBuffer(path, capacity=2)


def test_non_order_input_is_rejected(tmp_path) -> None:
    with (
        RingBuffer(tmp_path / "orders.mmap", capacity=2) as ring,
        pytest.raises(TypeError),
    ):
        ring.write("not an order")  # type: ignore[arg-type]
