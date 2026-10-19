
"""Tests for the ChronosMatch binary order protocol."""

import pytest

from chronosmatch.core.models import Order, Side
from chronosmatch.ipc.protocol import (
    ORDER_RECORD_SIZE,
    decode_order,
    encode_order,
)


def make_order(
    order_id: str = "order-001",
    symbol: str = "AAPL",
    side: Side = Side.BUY,
    price_ticks: int = 23500,
    quantity: int = 10,
    timestamp_ns: int = 123456789,
) -> Order:
    """Create a deterministic order for protocol tests."""
    return Order(
        order_id=order_id,
        symbol=symbol,
        side=side,
        price_ticks=price_ticks,
        quantity=quantity,
        timestamp_ns=timestamp_ns,
    )


@pytest.mark.parametrize("side", [Side.BUY, Side.SELL])
def test_order_round_trip(side: Side) -> None:
    original = make_order(side=side)

    decoded = decode_order(encode_order(original))

    assert decoded == original


def test_record_has_fixed_size() -> None:
    encoded = encode_order(make_order())

    assert ORDER_RECORD_SIZE == 78
    assert len(encoded) == 78


def test_normalized_symbol_is_preserved() -> None:
    order = make_order(symbol=" aapl ")

    assert decode_order(encode_order(order)).symbol == "AAPL"


def test_order_id_too_long_is_rejected() -> None:
    with pytest.raises(ValueError):
        encode_order(make_order(order_id="x" * 33))


def test_symbol_too_long_is_rejected() -> None:
    with pytest.raises(ValueError):
        encode_order(make_order(symbol="ABCDEFGHIJKLMNOPQ"))


def test_non_ascii_identifier_is_rejected() -> None:
    with pytest.raises(ValueError):
        encode_order(make_order(order_id="order-🚀"))


def test_embedded_null_identifier_is_rejected() -> None:
    with pytest.raises(ValueError):
        encode_order(make_order(order_id="order\x00-001"))


def test_non_order_input_is_rejected() -> None:
    with pytest.raises(TypeError):
        encode_order("not-an-order")  # type: ignore[arg-type]


def test_value_outside_unsigned_64_bit_range_is_rejected() -> None:
    with pytest.raises(ValueError):
        encode_order(make_order(price_ticks=2**64))


def test_wrong_record_size_is_rejected() -> None:
    encoded = encode_order(make_order())

    with pytest.raises(ValueError):
        decode_order(encoded[:-1])

    with pytest.raises(ValueError):
        decode_order(encoded + b"\x00")


def test_invalid_magic_header_is_rejected() -> None:
    encoded = bytearray(encode_order(make_order()))
    encoded[0] = 0

    with pytest.raises(ValueError):
        decode_order(encoded)


def test_unsupported_protocol_version_is_rejected() -> None:
    encoded = bytearray(encode_order(make_order()))
    encoded[4] = 255

    with pytest.raises(ValueError):
        decode_order(encoded)


def test_invalid_side_code_is_rejected() -> None:
    encoded = bytearray(encode_order(make_order()))
    encoded[5] = 255

    with pytest.raises(ValueError):
        decode_order(encoded)
