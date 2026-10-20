
"""Memory-mapped ring buffer for fixed-size ChronosMatch orders.

This version provides sequential FIFO access and persistence across close
and reopen. It is not yet safe for concurrent producer-consumer access.
"""

import mmap
import struct
from pathlib import Path
from typing import Self

from chronosmatch.core.models import Order
from chronosmatch.ipc.protocol import ORDER_RECORD_SIZE, decode_order, encode_order

_MAGIC = b"CMRB"
_VERSION = 1
_MAX_CAPACITY = (1 << 32) - 1

# 32-byte header:
# magic (4), version (1), padding (3), capacity (4),
# read sequence (8), write sequence (8), reserved (4).
_HEADER = struct.Struct(">4sB3xIQQ4x")
_HEADER_SIZE = _HEADER.size


class RingBuffer:
    """Persistent, fixed-capacity FIFO ring buffer for Order records."""

    def __init__(self, path: str | Path, capacity: int) -> None:
        if type(capacity) is not int:
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")
        if capacity > _MAX_CAPACITY:
            raise ValueError("capacity exceeds the supported range")

        self.path = Path(path)
        self.capacity = capacity
        self._closed = False
        self._map: mmap.mmap | None = None

        self._file = self.path.open(
         "r+b" if self.path.exists() else "w+b",
         buffering=0,
         )

        try:
            file_size = self.path.stat().st_size
            expected_size = _HEADER_SIZE + capacity * ORDER_RECORD_SIZE

            if file_size == 0:
                # Initialize a new buffer file.
                self._file.truncate(expected_size)
                self._read_seq = 0
                self._write_seq = 0
                self._file.seek(0)
                self._file.write(
                    _HEADER.pack(
                        _MAGIC,
                        _VERSION,
                        capacity,
                        self._read_seq,
                        self._write_seq,
                    )
                )
                self._file.flush()

            else:
                if file_size < _HEADER_SIZE:
                    raise ValueError("Buffer file is too small for its header")

                self._file.seek(0)
                raw_header = self._file.read(_HEADER_SIZE)

                try:
                    (
                        magic,
                        version,
                        stored_capacity,
                        read_seq,
                        write_seq,
                    ) = _HEADER.unpack(raw_header)
                except struct.error as exc:
                    raise ValueError("Invalid ring-buffer header") from exc

                if magic != _MAGIC:
                    raise ValueError("Invalid ring-buffer magic header")
                if version != _VERSION:
                    raise ValueError(
                        f"Unsupported ring-buffer version: {version}"
                    )
                if stored_capacity != capacity:
                    raise ValueError(
                        f"Existing buffer capacity is {stored_capacity}, "
                        f"not {capacity}"
                    )
                if file_size != expected_size:
                    raise ValueError("Ring-buffer file size is invalid")
                if write_seq < read_seq:
                    raise ValueError("Invalid ring-buffer sequence counters")
                if write_seq - read_seq > capacity:
                    raise ValueError("Ring-buffer occupancy exceeds capacity")

                self._read_seq = read_seq
                self._write_seq = write_seq

            self._map = mmap.mmap(
                self._file.fileno(),
                expected_size,
                access=mmap.ACCESS_WRITE,
            )

        except Exception:
            self._file.close()
            self._closed = True
            raise

    def _ensure_open(self) -> mmap.mmap:
        """Return the mapping or raise if the buffer is closed."""
        if self._closed or self._map is None:
            raise ValueError("Ring buffer is closed")
        return self._map

    @property
    def size(self) -> int:
        """Return the number of unread records."""
        self._ensure_open()
        return self._write_seq - self._read_seq

    @property
    def is_empty(self) -> bool:
        """Return whether the buffer contains no unread records."""
        return self.size == 0

    @property
    def is_full(self) -> bool:
        """Return whether the buffer has reached its capacity."""
        return self.size == self.capacity

    def write(self, order: Order) -> bool:
        """Write an order, returning False when the buffer is full."""
        mapping = self._ensure_open()

        # Validate and encode before changing buffer state.
        record = encode_order(order)

        if self.is_full:
            return False

        slot = self._write_seq % self.capacity
        offset = _HEADER_SIZE + slot * ORDER_RECORD_SIZE

        mapping[offset : offset + ORDER_RECORD_SIZE] = record

        self._write_seq += 1
        self._write_header(mapping)
        return True

    def read(self) -> Order | None:
        """Read the oldest order, or return None when the buffer is empty."""
        mapping = self._ensure_open()

        if self.is_empty:
            return None

        slot = self._read_seq % self.capacity
        offset = _HEADER_SIZE + slot * ORDER_RECORD_SIZE

        # Copy this one record out of the mapping before decoding.
        record = mapping[offset : offset + ORDER_RECORD_SIZE]
        order = decode_order(record)

        self._read_seq += 1
        self._write_header(mapping)
        return order

    def _write_header(self, mapping: mmap.mmap) -> None:
        """Persist the current metadata in the mapped header."""
        _HEADER.pack_into(
            mapping,
            0,
            _MAGIC,
            _VERSION,
            self.capacity,
            self._read_seq,
            self._write_seq,
        )

    def close(self) -> None:
        """Flush and close the mapping and underlying file."""
        if self._closed:
            return

        mapping = self._ensure_open()
        mapping.flush()
        mapping.close()
        self._map = None
        self._file.close()
        self._closed = True

    def __enter__(self) -> Self:
        """Allow use through a with statement."""
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close the buffer when leaving a with statement."""
        self.close()
