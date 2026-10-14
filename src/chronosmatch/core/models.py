
"""Validated domain models for the ChronosMatch trading engine."""

import time
from dataclasses import dataclass, field
from enum import Enum


class Side(Enum):
    """Supported sides of a limit order."""

    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True, slots=True)
class Order:
    """An immutable limit-order request.

    Prices are represented as integer ticks, not floating-point values.
    timestamp_ns uses the local monotonic clock and is not wall-clock time.
    """

    order_id: str
    symbol: str
    side: Side
    price_ticks: int
    quantity: int
    timestamp_ns: int = field(default_factory=time.monotonic_ns)

    def __post_init__(self) -> None:
        """Validate and normalize the order at creation time."""

        # Validate and normalize the order ID.
        if not isinstance(self.order_id, str):
            raise TypeError("order_id must be a string")

        normalized_order_id = self.order_id.strip()
        if not normalized_order_id:
            raise ValueError("order_id must not be empty")

        object.__setattr__(self, "order_id", normalized_order_id)

        # Validate and normalize the trading symbol.
        if not isinstance(self.symbol, str):
            raise TypeError("symbol must be a string")

        normalized_symbol = self.symbol.strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")

        object.__setattr__(self, "symbol", normalized_symbol)

        # Reject strings such as "BUY" to keep the API explicit.
        if not isinstance(self.side, Side):
            raise TypeError("side must be a Side enum member")

        # bool is a subclass of int in Python, so use exact type checks.
        integer_fields = {
            "price_ticks": self.price_ticks,
            "quantity": self.quantity,
            "timestamp_ns": self.timestamp_ns,
        }

        for field_name, value in integer_fields.items():
            if type(value) is not int:
                raise TypeError(f"{field_name} must be an integer")

        if self.price_ticks <= 0:
            raise ValueError("price_ticks must be greater than zero")

        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")

        if self.timestamp_ns < 0:
            raise ValueError("timestamp_ns must not be negative")
