
"""Fixed-size binary order protocol for ChronosMatch."""

import struct

from chronosmatch.core.models import Order, Side

# Protocol header and field definitions.
_MAGIC = b"CHRM"
_PROTOCOL_VERSION = 1

_ORDER_ID_WIDTH = 32
_SYMBOL_WIDTH = 16
_UINT64_MAX = (1 << 64) - 1

_SIDE_TO_CODE = {
    Side.BUY: 1,
    Side.SELL: 2,
}

_CODE_TO_SIDE = {
    code: side for side, code in _SIDE_TO_CODE.items()
}

# Big-endian, standard-size fields with no native alignment padding:
# magic(4) + version(1) + side(1) + order_id(32) + symbol(16)
# + price_ticks(8) + quantity(8) + timestamp_ns(8) = 78 bytes.
_RECORD = struct.Struct(">4sBB32s16sQQQ")
ORDER_RECORD_SIZE = _RECORD.size


def _encode_text_field(value: str, field_name: str, width: int) -> bytes:
    """Encode a string as a fixed-width, null-padded ASCII field."""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")

    if not value:
        raise ValueError(f"{field_name} must not be empty")

    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain null characters")

    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(
            f"{field_name} must contain ASCII characters only"
        ) from exc

    if len(encoded) > width:
        raise ValueError(
            f"{field_name} exceeds the maximum length of {width} bytes"
        )

    return encoded.ljust(width, b"\x00")


def encode_order(order: Order) -> bytes:
    """Encode a validated Order into one fixed-size binary record."""
    if not isinstance(order, Order):
        raise TypeError("order must be an Order instance")

    order_id = _encode_text_field(
        order.order_id, "order_id", _ORDER_ID_WIDTH
    )
    symbol = _encode_text_field(
        order.symbol, "symbol", _SYMBOL_WIDTH
    )

    try:
        side_code = _SIDE_TO_CODE[order.side]
    except (KeyError, TypeError) as exc:
        raise ValueError("Unsupported order side") from exc

    numeric_fields = {
        "price_ticks": order.price_ticks,
        "quantity": order.quantity,
        "timestamp_ns": order.timestamp_ns,
    }

    for field_name, value in numeric_fields.items():
        if type(value) is not int:
            raise TypeError(f"{field_name} must be an integer")

        if value < 0 or value > _UINT64_MAX:
            raise ValueError(
                f"{field_name} must fit in an unsigned 64-bit integer"
            )

    if order.price_ticks == 0:
        raise ValueError("price_ticks must be greater than zero")

    if order.quantity == 0:
        raise ValueError("quantity must be greater than zero")

    return _RECORD.pack(
        _MAGIC,
        _PROTOCOL_VERSION,
        side_code,
        order_id,
        symbol,
        order.price_ticks,
        order.quantity,
        order.timestamp_ns,
    )


def _decode_text_field(raw: bytes, field_name: str) -> str:
    """Decode a null-padded ASCII field and validate its contents."""
    try:
        value = raw.rstrip(b"\x00").decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"{field_name} contains invalid ASCII data"
        ) from exc

    if not value:
        raise ValueError(f"{field_name} must not be empty")

    if "\x00" in value:
        raise ValueError(
            f"{field_name} contains invalid embedded null characters"
        )

    return value


def decode_order(record: bytes | bytearray | memoryview) -> Order:
    """Decode and validate a fixed-size binary order record."""
    if not isinstance(record, (bytes, bytearray, memoryview)):
        raise TypeError("record must be bytes-like")

    if len(record) != ORDER_RECORD_SIZE:
        raise ValueError(
            f"Record must be exactly {ORDER_RECORD_SIZE} bytes"
        )

    (
        magic,
        version,
        side_code,
        raw_order_id,
        raw_symbol,
        price_ticks,
        quantity,
        timestamp_ns,
    ) = _RECORD.unpack(record)

    if magic != _MAGIC:
        raise ValueError("Invalid protocol magic header")

    if version != _PROTOCOL_VERSION:
        raise ValueError(f"Unsupported protocol version: {version}")

    try:
        side = _CODE_TO_SIDE[side_code]
    except KeyError as exc:
        raise ValueError(f"Invalid order side code: {side_code}") from exc

    order_id = _decode_text_field(raw_order_id, "order_id")
    symbol = _decode_text_field(raw_symbol, "symbol")

    # The Order constructor applies the domain-level validation again.
    return Order(
        order_id=order_id,
        symbol=symbol,
        side=side,
        price_ticks=price_ticks,
        quantity=quantity,
        timestamp_ns=timestamp_ns,
    )
