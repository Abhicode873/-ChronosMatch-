
"""Tests defining the ChronosMatch order model contract."""

import time

import pytest

from chronosmatch.core.models import Order, Side


def test_valid_order_preserves_its_fields() -> None:
    order = Order(
        order_id="order-001",
        symbol="AAPL",
        side=Side.BUY,
        price_ticks=23500,
        quantity=10,
        timestamp_ns=123456789,
    )

    assert order.order_id == "order-001"
    assert order.symbol == "AAPL"
    assert order.side is Side.BUY
    assert order.price_ticks == 23500
    assert order.quantity == 10
    assert order.timestamp_ns == 123456789


def test_symbol_is_normalized() -> None:
    order = Order(
        order_id="order-002",
        symbol=" aapl ",
        side=Side.SELL,
        price_ticks=23500,
        quantity=5,
        timestamp_ns=100,
    )

    assert order.symbol == "AAPL"


def test_order_id_is_trimmed() -> None:
    order = Order(
        order_id=" order-003 ",
        symbol="MSFT",
        side=Side.BUY,
        price_ticks=40000,
        quantity=2,
        timestamp_ns=100,
    )

    assert order.order_id == "order-003"


def test_timestamp_defaults_to_monotonic_clock() -> None:
    before = time.monotonic_ns()

    order = Order(
        order_id="order-004",
        symbol="AAPL",
        side=Side.BUY,
        price_ticks=23500,
        quantity=1,
    )

    after = time.monotonic_ns()

    assert before <= order.timestamp_ns <= after


@pytest.mark.parametrize("order_id", ["", "   "])
def test_empty_order_id_is_rejected(order_id: str) -> None:
    with pytest.raises(ValueError):
        Order(
            order_id=order_id,
            symbol="AAPL",
            side=Side.BUY,
            price_ticks=100,
            quantity=1,
        )


@pytest.mark.parametrize("symbol", ["", "   "])
def test_empty_symbol_is_rejected(symbol: str) -> None:
    with pytest.raises(ValueError):
        Order(
            order_id="order-005",
            symbol=symbol,
            side=Side.BUY,
            price_ticks=100,
            quantity=1,
        )


@pytest.mark.parametrize("price_ticks", [0, -1])
def test_nonpositive_price_is_rejected(price_ticks: int) -> None:
    with pytest.raises(ValueError):
        Order(
            order_id="order-006",
            symbol="AAPL",
            side=Side.BUY,
            price_ticks=price_ticks,
            quantity=1,
        )


@pytest.mark.parametrize("quantity", [0, -1])
def test_nonpositive_quantity_is_rejected(quantity: int) -> None:
    with pytest.raises(ValueError):
        Order(
            order_id="order-007",
            symbol="AAPL",
            side=Side.BUY,
            price_ticks=100,
            quantity=quantity,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("price_ticks", True),
        ("price_ticks", 100.5),
        ("quantity", False),
        ("quantity", 1.5),
        ("timestamp_ns", True),
        ("timestamp_ns", 1.5),
    ],
)
def test_numeric_fields_require_integers(
    field: str,
    value: object,
) -> None:
    fields: dict[str, object] = {
        "order_id": "order-008",
        "symbol": "AAPL",
        "side": Side.BUY,
        "price_ticks": 100,
        "quantity": 1,
        "timestamp_ns": 100,
    }
    fields[field] = value

    with pytest.raises(TypeError):
        Order(**fields)  # type: ignore[arg-type]


def test_negative_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError):
        Order(
            order_id="order-009",
            symbol="AAPL",
            side=Side.BUY,
            price_ticks=100,
            quantity=1,
            timestamp_ns=-1,
        )


def test_order_is_immutable() -> None:
    from dataclasses import FrozenInstanceError

    order = Order(
        order_id="order-010",
        symbol="AAPL",
        side=Side.BUY,
        price_ticks=100,
        quantity=1,
        timestamp_ns=100,
    )

    with pytest.raises(FrozenInstanceError):
        order.quantity = 99  # type: ignore[misc]
