
"""Tests for order cancellation and lifecycle behavior."""

import pytest

from chronosmatch.core.models import Order, Side
from chronosmatch.core.order_book import OrderBook


def make_order(
    order_id: str,
    side: Side,
    price_ticks: int,
    quantity: int = 1,
) -> Order:
    """Create a test order."""
    return Order(
        order_id=order_id,
        symbol="AAPL",
        side=side,
        price_ticks=price_ticks,
        quantity=quantity,
    )


def test_cancel_active_buy_order() -> None:
    book = OrderBook("AAPL")
    book.submit(make_order("buy-1", Side.BUY, 100))

    assert book.cancel("buy-1") is True
    assert book.best_bid is None
    assert book.active_order_count == 0


def test_cancel_updates_best_bid() -> None:
    book = OrderBook("AAPL")
    book.submit(make_order("buy-1", Side.BUY, 105))
    book.submit(make_order("buy-2", Side.BUY, 103))

    assert book.cancel("buy-1") is True
    assert book.best_bid == 103
    assert book.active_order_count == 1


def test_cancel_updates_best_ask() -> None:
    book = OrderBook("AAPL")
    book.submit(make_order("sell-1", Side.SELL, 99))
    book.submit(make_order("sell-2", Side.SELL, 102))

    assert book.cancel("sell-1") is True
    assert book.best_ask == 102
    assert book.active_order_count == 1


def test_cancel_unknown_order_returns_false() -> None:
    book = OrderBook("AAPL")

    assert book.cancel("unknown-order") is False


def test_cancelling_twice_returns_false_on_second_attempt() -> None:
    book = OrderBook("AAPL")
    book.submit(make_order("buy-1", Side.BUY, 100))

    assert book.cancel("buy-1") is True
    assert book.cancel("buy-1") is False


def test_cancelled_order_does_not_disrupt_fifo() -> None:
    book = OrderBook("AAPL")
    book.submit(make_order("sell-1", Side.SELL, 100, quantity=2))
    book.submit(make_order("sell-2", Side.SELL, 100, quantity=2))

    assert book.cancel("sell-1") is True

    trades = book.submit(
        make_order("buy-1", Side.BUY, 100, quantity=1)
    )

    assert len(trades) == 1
    assert trades[0].maker_order_id == "sell-2"
    assert trades[0].quantity == 1


def test_cancelling_middle_order_preserves_remaining_fifo() -> None:
    book = OrderBook("AAPL")
    book.submit(make_order("sell-1", Side.SELL, 100))
    book.submit(make_order("sell-2", Side.SELL, 100))
    book.submit(make_order("sell-3", Side.SELL, 100))

    assert book.cancel("sell-2") is True

    trades = book.submit(
        make_order("buy-1", Side.BUY, 100, quantity=2)
    )

    assert [trade.maker_order_id for trade in trades] == [
        "sell-1",
        "sell-3",
    ]


def test_partially_filled_order_can_be_cancelled() -> None:
    book = OrderBook("AAPL")
    book.submit(make_order("sell-1", Side.SELL, 100, quantity=5))

    trades = book.submit(
        make_order("buy-1", Side.BUY, 100, quantity=2)
    )

    assert len(trades) == 1
    assert trades[0].quantity == 2
    assert book.active_order_count == 1

    assert book.cancel("sell-1") is True
    assert book.best_ask is None
    assert book.active_order_count == 0


def test_fully_filled_order_cannot_be_cancelled() -> None:
    book = OrderBook("AAPL")
    book.submit(make_order("sell-1", Side.SELL, 100, quantity=2))

    book.submit(make_order("buy-1", Side.BUY, 100, quantity=2))

    assert book.active_order_count == 0
    assert book.cancel("sell-1") is False


def test_cancelled_order_id_cannot_be_reused() -> None:
    book = OrderBook("AAPL")
    order = make_order("buy-1", Side.BUY, 100)
    book.submit(order)

    assert book.cancel("buy-1") is True

    with pytest.raises(ValueError, match="Duplicate order ID"):
        book.submit(order)
