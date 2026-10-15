
"""Tests for the ChronosMatch limit order book."""

import pytest

from chronosmatch.core.models import Order, Side
from chronosmatch.core.order_book import OrderBook


def make_order(
    order_id: str,
    side: Side,
    price_ticks: int,
    quantity: int = 1,
    symbol: str = "AAPL",
) -> Order:
    """Create an order for use in tests."""
    return Order(
        order_id=order_id,
        symbol=symbol,
        side=side,
        price_ticks=price_ticks,
        quantity=quantity,
    )


def test_empty_book_has_no_best_prices() -> None:
    book = OrderBook("AAPL")

    assert book.best_bid is None
    assert book.best_ask is None
    assert book.active_order_count == 0


def test_book_normalizes_its_symbol() -> None:
    book = OrderBook(" aapl ")

    assert book.symbol == "AAPL"


def test_best_bid_and_ask_are_selected_correctly() -> None:
    book = OrderBook("AAPL")

    book.submit(make_order("buy-1", Side.BUY, 101))
    book.submit(make_order("buy-2", Side.BUY, 105))
    book.submit(make_order("sell-1", Side.SELL, 110))
    book.submit(make_order("sell-2", Side.SELL, 108))

    assert book.best_bid == 105
    assert book.best_ask == 108


def test_non_crossing_orders_remain_in_the_book() -> None:
    book = OrderBook("AAPL")

    book.submit(make_order("sell-1", Side.SELL, 101))
    trades = book.submit(make_order("buy-1", Side.BUY, 100))

    assert trades == []
    assert book.best_bid == 100
    assert book.best_ask == 101
    assert book.active_order_count == 2


def test_buy_matches_at_the_resting_sell_price() -> None:
    book = OrderBook("AAPL")

    book.submit(
        make_order("sell-1", Side.SELL, 100, quantity=3)
    )
    trades = book.submit(
        make_order("buy-1", Side.BUY, 105, quantity=2)
    )

    assert len(trades) == 1

    trade = trades[0]
    assert trade.symbol == "AAPL"
    assert trade.maker_order_id == "sell-1"
    assert trade.taker_order_id == "buy-1"
    assert trade.price_ticks == 100
    assert trade.quantity == 2

    # One unit remains on the resting sell order.
    assert book.best_ask == 100
    assert book.best_bid is None
    assert book.active_order_count == 1


def test_same_price_orders_follow_fifo_priority() -> None:
    book = OrderBook("AAPL")

    book.submit(make_order("sell-1", Side.SELL, 100, quantity=3))
    book.submit(make_order("sell-2", Side.SELL, 100, quantity=2))

    trades = book.submit(
        make_order("buy-1", Side.BUY, 100, quantity=4)
    )

    assert [trade.maker_order_id for trade in trades] == [
        "sell-1",
        "sell-2",
    ]
    assert [trade.quantity for trade in trades] == [3, 1]
    assert [trade.price_ticks for trade in trades] == [100, 100]

    # The second sell order has one unit remaining.
    assert book.best_ask == 100
    assert book.active_order_count == 1


def test_sell_matches_highest_bid_first() -> None:
    book = OrderBook("AAPL")

    book.submit(make_order("buy-low", Side.BUY, 99, quantity=3))
    book.submit(make_order("buy-high", Side.BUY, 100, quantity=2))

    trades = book.submit(
        make_order("sell-1", Side.SELL, 99, quantity=4)
    )

    assert [trade.maker_order_id for trade in trades] == [
        "buy-high",
        "buy-low",
    ]
    assert [trade.price_ticks for trade in trades] == [100, 99]
    assert [trade.quantity for trade in trades] == [2, 2]

    # One unit remains on the lower-priced bid.
    assert book.best_bid == 99
    assert book.best_ask is None
    assert book.active_order_count == 1


def test_book_rejects_an_order_for_another_symbol() -> None:
    book = OrderBook("AAPL")

    with pytest.raises(ValueError):
        book.submit(
            make_order(
                "buy-1",
                Side.BUY,
                100,
                symbol="MSFT",
            )
        )

    assert book.active_order_count == 0


def test_duplicate_order_ids_are_rejected() -> None:
    book = OrderBook("AAPL")
    order = make_order("order-1", Side.BUY, 100)

    book.submit(order)

    with pytest.raises(ValueError):
        book.submit(order)


def test_non_order_input_is_rejected() -> None:
    book = OrderBook("AAPL")

    with pytest.raises(TypeError):
        book.submit("not an order")  # type: ignore[arg-type]
