
# cython: language_level=3, boundscheck=False, wraparound=False

"""Cython-based fixed-capacity limit order book prototype."""

from cpython.mem cimport PyMem_Malloc, PyMem_Free
from libc.stdint cimport int64_t, uint8_t, uint64_t

BUY = 1
SELL = 2

cdef uint8_t _BUY = 1
cdef uint8_t _SELL = 2
cdef uint64_t _UINT64_MAX = <uint64_t>-1

_UINT64_MAX_PY = 18446744073709551615
_INT64_MAX_PY = 9223372036854775807


cdef struct OrderEntry:
    uint64_t order_id
    uint8_t side
    int64_t price_ticks
    int64_t remaining_quantity
    uint64_t sequence
    uint8_t active


cdef class CythonOrderBook:
    """Fixed-capacity book using C-level storage and matching scans."""

    cdef OrderEntry* _orders
    cdef Py_ssize_t _capacity
    cdef Py_ssize_t _active_count
    cdef uint64_t _next_sequence

    def __cinit__(self, capacity=1024):
        cdef Py_ssize_t i

        self._orders = NULL
        self._capacity = 0
        self._active_count = 0
        self._next_sequence = 0

        if isinstance(capacity, bool) or not isinstance(capacity, int):
            raise TypeError("capacity must be an integer")

        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")

        if capacity > 1_000_000:
            raise ValueError("capacity cannot exceed 1,000,000")

        self._capacity = capacity
        self._orders = <OrderEntry*>PyMem_Malloc(
            capacity * sizeof(OrderEntry)
        )

        if self._orders == NULL:
            raise MemoryError()

        for i in range(self._capacity):
            self._orders[i].order_id = 0
            self._orders[i].side = 0
            self._orders[i].price_ticks = 0
            self._orders[i].remaining_quantity = 0
            self._orders[i].sequence = 0
            self._orders[i].active = 0

    def __dealloc__(self):
        if self._orders != NULL:
            PyMem_Free(self._orders)
            self._orders = NULL

    @property
    def best_bid(self):
        """Return the highest active bid, or None."""
        cdef Py_ssize_t i
        cdef int64_t best_price = 0
        cdef bint found = False

        for i in range(self._capacity):
            if (
                self._orders[i].active
                and self._orders[i].side == _BUY
            ):
                if not found or self._orders[i].price_ticks > best_price:
                    best_price = self._orders[i].price_ticks
                    found = True

        if not found:
            return None
        return best_price

    @property
    def best_ask(self):
        """Return the lowest active ask, or None."""
        cdef Py_ssize_t i
        cdef int64_t best_price = 0
        cdef bint found = False

        for i in range(self._capacity):
            if (
                self._orders[i].active
                and self._orders[i].side == _SELL
            ):
                if not found or self._orders[i].price_ticks < best_price:
                    best_price = self._orders[i].price_ticks
                    found = True

        if not found:
            return None
        return best_price

    @property
    def active_order_count(self):
        """Return the number of orders resting in the book."""
        return self._active_count

    def submit(self, order_id, side, price_ticks, quantity):
        """Submit an order and return execution tuples.

        Each trade is:
            (maker_order_id, taker_order_id, price_ticks, quantity)

        Price-time priority is enforced by choosing the best eligible
        price and then the earliest sequence number.
        """
        cdef uint64_t oid
        cdef uint8_t side_value
        cdef int64_t price_value
        cdef int64_t remaining
        cdef int64_t fill_quantity
        cdef int64_t quantity_value
        cdef Py_ssize_t i
        cdef Py_ssize_t best_index
        cdef Py_ssize_t free_index
        cdef OrderEntry* resting
        cdef bint has_crossing_order
        cdef list trades

        # Validate identifiers and numeric inputs before changing state.
        if isinstance(order_id, bool) or not isinstance(order_id, int):
            raise TypeError("order_id must be an integer")

        if order_id < 0 or order_id > _UINT64_MAX_PY:
            raise ValueError("order_id must fit an unsigned 64-bit integer")

        if isinstance(side, bool) or not isinstance(side, int):
            raise TypeError("side must be an integer")

        if side not in (BUY, SELL):
            raise ValueError("side must be BUY (1) or SELL (2)")

        if isinstance(price_ticks, bool) or not isinstance(price_ticks, int):
            raise TypeError("price_ticks must be an integer")

        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise TypeError("quantity must be an integer")

        if price_ticks <= 0 or quantity <= 0:
            raise ValueError("price_ticks and quantity must be positive")

        if price_ticks > _INT64_MAX_PY or quantity > _INT64_MAX_PY:
            raise ValueError("price_ticks and quantity must fit signed 64-bit")

        oid = order_id
        side_value = side
        price_value = price_ticks
        quantity_value = quantity
        remaining = quantity_value

        # A resting ID cannot be duplicated.
        for i in range(self._capacity):
            if (
                self._orders[i].active
                and self._orders[i].order_id == oid
            ):
                raise ValueError("Duplicate active order ID")

        # Avoid mutating a full book if this order cannot trade at all.
        if self._active_count == self._capacity:
            has_crossing_order = False

            for i in range(self._capacity):
                if not self._orders[i].active:
                    continue

                if side_value == _BUY:
                    if (
                        self._orders[i].side == _SELL
                        and self._orders[i].price_ticks <= price_value
                    ):
                        has_crossing_order = True
                        break
                else:
                    if (
                        self._orders[i].side == _BUY
                        and self._orders[i].price_ticks >= price_value
                    ):
                        has_crossing_order = True
                        break

            if not has_crossing_order:
                raise OverflowError("Order book capacity exhausted")

        trades = []

        while remaining > 0:
            best_index = -1

            # Select the best eligible resting order, including FIFO ties.
            for i in range(self._capacity):
                if not self._orders[i].active:
                    continue

                if side_value == _BUY:
                    if (
                        self._orders[i].side != _SELL
                        or self._orders[i].price_ticks > price_value
                    ):
                        continue

                    if best_index == -1:
                        best_index = i
                    elif (
                        self._orders[i].price_ticks
                        < self._orders[best_index].price_ticks
                        or (
                            self._orders[i].price_ticks
                            == self._orders[best_index].price_ticks
                            and self._orders[i].sequence
                            < self._orders[best_index].sequence
                        )
                    ):
                        best_index = i

                else:
                    if (
                        self._orders[i].side != _BUY
                        or self._orders[i].price_ticks < price_value
                    ):
                        continue

                    if best_index == -1:
                        best_index = i
                    elif (
                        self._orders[i].price_ticks
                        > self._orders[best_index].price_ticks
                        or (
                            self._orders[i].price_ticks
                            == self._orders[best_index].price_ticks
                            and self._orders[i].sequence
                            < self._orders[best_index].sequence
                        )
                    ):
                        best_index = i

            if best_index == -1:
                break

            resting = &self._orders[best_index]

            if resting.remaining_quantity < remaining:
                fill_quantity = resting.remaining_quantity
            else:
                fill_quantity = remaining

            trades.append(
                (
                    resting.order_id,
                    oid,
                    resting.price_ticks,
                    fill_quantity,
                )
            )

            remaining -= fill_quantity
            resting.remaining_quantity -= fill_quantity

            if resting.remaining_quantity == 0:
                resting.active = 0
                self._active_count -= 1

        # Store any unfilled remainder as a new resting order.
        if remaining > 0:
            free_index = -1

            for i in range(self._capacity):
                if not self._orders[i].active:
                    free_index = i
                    break

            if free_index == -1:
                raise OverflowError("Order book capacity exhausted")

            if self._next_sequence == _UINT64_MAX:
                raise OverflowError("Order sequence counter exhausted")

            self._orders[free_index].order_id = oid
            self._orders[free_index].side = side_value
            self._orders[free_index].price_ticks = price_value
            self._orders[free_index].remaining_quantity = remaining
            self._orders[free_index].sequence = self._next_sequence
            self._orders[free_index].active = 1

            self._next_sequence += 1
            self._active_count += 1

        return trades
