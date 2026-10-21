
"""Memory-mapped ring buffer for fixed-size ChronosMatch orders.

This implementation supports sequential use and coordinated access by
multiple handles that share the same lock. Initialize the file before
starting producer and consumer processes.
"""

import mmap
import struct
from pathlib import Path
from threading import RLock
from typing import Any, Self

from chronosmatch.core.models import Order
from chronosmatch.ipc.protocol import (
    ORDER_RECORD_SIZE,
    decode_order,
    encode_order,
)

_MAGIC = b"CMRB"
_VERSION = 1
_MAX_CAPACITY = (1 << 32) - 1

# 32-byte header:
# magic (4), version (1), padding (3), capacity (4),
# read sequence (8), write sequence (8), reserved (4).
_HEADER = struct.Struct(">4sB3xIQQ4x")
_HEADER_SIZE = _HEADER.size
_UINT64_MAX = (1 << 64) - 1


class RingBuffer:
    """Persistent FIFO ring buffer for fixed-size order records."""

    def __init__(
        self,
        path: str | Path,
        capacity: int,
        lock: Any | None = None,
    ) -> None:
        if type(capacity) is not int:
            raise TypeError("capacity must be an integer")
        if capacity <= 0:
            raise ValueError("capacity must be greater than zero")
        if capacity > _MAX_CAPACITY:
            raise ValueError("capacity exceeds the supported range")

        self.path = Path(path)
        self.capacity = capacity
        self._lock = lock if lock is not None else RLock()
        self._closed = False
        self._map: mmap.mmap | None = None
        self._read_seq = 0
        self._write_seq = 0

        self._file = self.path.open(
            "r+b" if self.path.exists() else "w+b",
            buffering=0,
        )

        try:
            expected_size = _HEADER_SIZE + capacity * ORDER_RECORD_SIZE
            file_size = self.path.stat().st_size

            if file_size == 0:
                # Initialize the file before producer/consumer processes start.
                self._file.truncate(expected_size)
                self._file.seek(0)
                self._file.write(
                    _HEADER.pack(
                        _MAGIC,
                        _VERSION,
                        capacity,
                        0,
                        0,
                    )
                )
                self._file.flush()
            elif file_size < _HEADER_SIZE:
                raise ValueError("Buffer file is too small for its header")
            elif file_size != expected_size:
                raise ValueError("Ring-buffer file size is invalid")

            self._map = mmap.mmap(
                self._file.fileno(),
                expected_size,
                access=mmap.ACCESS_WRITE,
            )

            with self._lock:
                self._refresh_header(self._ensure_open())

        except Exception:
            if self._map is not None:
                self._map.close()
                self._map = None
            self._file.close()
            self._closed = True
            raise

    def _ensure_open(self) -> mmap.mmap:
        """Return the memory mapping or raise when closed."""
        if self._closed or self._map is None:
            raise ValueError("Ring buffer is closed")
        return self._map

    def _refresh_header(self, mapping: mmap.mmap) -> None:
        """Refresh local counters from shared metadata while holding the lock."""
        try:
            (
                magic,
                version,
                stored_capacity,
                read_seq,
                write_seq,
            ) = _HEADER.unpack_from(mapping, 0)
        except struct.error as exc:
            raise ValueError("Invalid ring-buffer header") from exc

        if magic != _MAGIC:
            raise ValueError("Invalid ring-buffer magic header")
        if version != _VERSION:
            raise ValueError(f"Unsupported ring-buffer version: {version}")
        if stored_capacity != self.capacity:
            raise ValueError("Ring-buffer capacity does not match its header")
        if write_seq < read_seq:
            raise ValueError("Invalid ring-buffer sequence counters")
        if write_seq - read_seq > self.capacity:
            raise ValueError("Ring-buffer occupancy exceeds capacity")

        self._read_seq = read_seq
        self._write_seq = write_seq

    @property
    def size(self) -> int:
        """Return the number of unread records."""
        with self._lock:
            mapping = self._ensure_open()
            self._refresh_header(mapping)
            return self._write_seq - self._read_seq

    @property
    def is_empty(self) -> bool:
        """Return whether the buffer contains no unread records."""
        return self.size == 0

    @property
    def is_full(self) -> bool:
        """Return whether the buffer has reached capacity."""
        return self.size == self.capacity

    def write(self, order: Order) -> bool:
        """Write an order or return False when the buffer is full."""
        # Encode before acquiring the lock to keep the critical section short.
        record = encode_order(order)

        with self._lock:
            mapping = self._ensure_open()
            self._refresh_header(mapping)

            if self._write_seq - self._read_seq >= self.capacity:
                return False

            slot = self._write_seq % self.capacity
            offset = _HEADER_SIZE + slot * ORDER_RECORD_SIZE

            # Publish the record before updating the shared write counter.
            mapping[offset : offset + ORDER_RECORD_SIZE] = record
            self._write_seq += 1
            self._write_header(mapping)
            return True

    def read(self) -> Order | None:
        """Read the oldest record, or return None if the buffer is empty."""
        with self._lock:
            mapping = self._ensure_open()
            self._refresh_header(mapping)

            if self._write_seq == self._read_seq:
                return None

            slot = self._read_seq % self.capacity
            offset = _HEADER_SIZE + slot * ORDER_RECORD_SIZE

            record = mapping[offset : offset + ORDER_RECORD_SIZE]
            order = decode_order(record)

            self._read_seq += 1
            self._write_header(mapping)
            return order

    def _write_header(self, mapping: mmap.mmap) -> None:
        """Write updated sequence counters to the shared metadata header."""
        if self._read_seq > _UINT64_MAX or self._write_seq > _UINT64_MAX:
            raise OverflowError("Ring-buffer sequence counter exhausted")

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
        """Flush and close this handle's mapping and file."""
        with self._lock:
            if self._closed:
                return

            mapping = self._ensure_open()
            mapping.flush()
            mapping.close()
            self._map = None
            self._file.close()
            self._closed = True

    def __enter__(self) -> Self:
        """Support use as a context manager."""
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close the buffer when leaving a with statement."""
        self.close()
