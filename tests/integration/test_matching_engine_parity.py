
"""Cross-engine parity tests for matching and order cancellation."""

from chronosmatch.core.cython_order_book import BUY, SELL, CythonOrderBook

from chronosmatch.core.models import Order, Side
from chronosmatch.core.order_book import OrderBook


def test_python_and_cython_engines_match_after_cancellations() -> None:
    """Verify equivalent matching and cancellation behaviour."""

    python_book = OrderBook("AAPL")
    cython_book = CythonOrderBook(capacity=8)

    # Map Python string IDs to Cython integer IDs.
    order_ids = {
        "buy-1": 1,
        "buy-2": 2,
        "sell-1": 3,
        "sell-2": 4,
        "incoming-buy": 5,
    }

    def submit(
        order_id: str,
        side: Side,
        price: int,
        quantity: int,
    ) -> None:
        python_trades = python_book.submit(
            Order(
                order_id=order_id,
                symbol="AAPL",
                side=side,
                price_ticks=price,
                quantity=quantity,
            )
        )

        cython_side = BUY if side is Side.BUY else SELL
        cython_trades = cython_book.submit(
            order_ids[order_id],
            cython_side,
            price,
            quantity,
        )

        expected_trades = [
            (
                order_ids[trade.maker_order_id],
                order_ids[trade.taker_order_id],
                trade.price_ticks,
                trade.quantity,
            )
            for trade in python_trades
        ]

        assert cython_trades == expected_trades

    # Create two buy orders at different prices.
    submit("buy-1", Side.BUY, 100, 5)
    submit("buy-2", Side.BUY, 99, 3)

    # Create two sell orders at the same price.
    submit("sell-1", Side.SELL, 105, 2)
    submit("sell-2", Side.SELL, 105, 4)

    # Cancel the first sell order in both engines.
    assert python_book.cancel("sell-1") is True
    assert cython_book.cancel(order_ids["sell-1"]) is True

    # Cancel an unknown order in both engines.
    assert python_book.cancel("unknown") is False
    assert cython_book.cancel(999) is False

    # A crossing buy should match the remaining sell order.
    submit("incoming-buy", Side.BUY, 105, 4)

    # Compare final order-book state.
    assert python_book.best_bid == cython_book.best_bid
    assert python_book.best_ask == cython_book.best_ask
    assert python_book.active_order_count == cython_book.active_order_count

    assert python_book.best_bid == 100
    assert python_book.best_ask is None
    assert python_book.active_order_count == 2
