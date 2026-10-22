
"""Tests for the compiled ChronosMatch order book."""

import pytest
from chronosmatch.core.cython_order_book import (
    BUY,
    SELL,
    CythonOrderBook,
)


def test_empty_book_has_no_best_prices() -> None:
    book = CythonOrderBook(capacity=8)

    assert book.best_bid is None
    assert book.best_ask is None
    assert book.active_order_count == 0


def test_non_crossing_orders_remain_in_book() -> None:
    book = CythonOrderBook(capacity=8)

    assert book.submit(1, BUY, 100, 2) == []
    assert book.submit(2, SELL, 105, 3) == []

    assert book.best_bid == 100
    assert book.best_ask == 105
    assert book.active_order_count == 2


def test_buy_matches_cheapest_ask_first() -> None:
    book = CythonOrderBook(capacity=8)

    book.submit(1, SELL, 101, 2)
    book.submit(2, SELL, 100, 3)

    trades = book.submit(3, BUY, 101, 4)

    assert trades == [
        (2, 3, 100, 3),
        (1, 3, 101, 1),
    ]
    assert book.best_ask == 101
    assert book.active_order_count == 1


def test_sell_matches_highest_bid_first() -> None:
    book = CythonOrderBook(capacity=8)

    book.submit(1, BUY, 99, 3)
    book.submit(2, BUY, 100, 2)

    trades = book.submit(3, SELL, 99, 4)

    assert trades == [
        (2, 3, 100, 2),
        (1, 3, 99, 2),
    ]
    assert book.best_bid == 99
    assert book.active_order_count == 1


def test_equal_price_orders_follow_fifo() -> None:
    book = CythonOrderBook(capacity=8)

    book.submit(1, SELL, 100, 2)
    book.submit(2, SELL, 100, 3)

    trades = book.submit(3, BUY, 100, 4)

    assert trades == [
        (1, 3, 100, 2),
        (2, 3, 100, 2),
    ]
    assert book.active_order_count == 1
    assert book.best_ask == 100


def test_partial_fill_preserves_remaining_quantity() -> None:
    book = CythonOrderBook(capacity=8)

    book.submit(1, SELL, 100, 5)
    trades = book.submit(2, BUY, 100, 2)

    assert trades == [(1, 2, 100, 2)]
    assert book.active_order_count == 1
    assert book.best_ask == 100

    trades = book.submit(3, BUY, 100, 3)

    assert trades == [(1, 3, 100, 3)]
    assert book.active_order_count == 0
    assert book.best_ask is None


def test_duplicate_active_order_id_is_rejected() -> None:
    book = CythonOrderBook(capacity=8)

    book.submit(1, BUY, 100, 2)

    with pytest.raises(ValueError, match="Duplicate"):
        book.submit(1, BUY, 99, 1)


def test_full_book_rejects_an_additional_resting_order() -> None:
    book = CythonOrderBook(capacity=1)

    book.submit(1, BUY, 100, 1)

    with pytest.raises(OverflowError):
        book.submit(2, BUY, 99, 1)

    assert book.active_order_count == 1
    assert book.best_bid == 100


@pytest.mark.parametrize("side", [0, 3, -1])
def test_invalid_side_is_rejected(side: int) -> None:
    book = CythonOrderBook(capacity=8)

    with pytest.raises(ValueError):
        book.submit(1, side, 100, 1)


@pytest.mark.parametrize(
    ("price", "quantity"),
    [(0, 1), (-1, 1), (100, 0), (100, -1)],
)
def test_nonpositive_price_or_quantity_is_rejected(
    price: int,
    quantity: int,
) -> None:
    book = CythonOrderBook(capacity=8)

    with pytest.raises(ValueError):
        book.submit(1, BUY, price, quantity)


def test_boolean_order_id_is_rejected() -> None:
    book = CythonOrderBook(capacity=8)

    with pytest.raises(TypeError):
        book.submit(True, BUY, 100, 1)


def test_noninteger_price_is_rejected() -> None:
    book = CythonOrderBook(capacity=8)

    with pytest.raises(TypeError):
        book.submit(1, BUY, 100.5, 1)


def test_capacity_must_be_positive() -> None:
    with pytest.raises(ValueError):
        CythonOrderBook(capacity=0)


