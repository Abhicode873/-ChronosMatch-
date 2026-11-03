
"""Memory allocation monitoring for ChronosMatch."""

import tracemalloc
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class MemorySnapshot:
    """Immutable snapshot of traced memory usage."""

    current_bytes: int
    peak_bytes: int

    @property
    def current_kb(self) -> float:
        """Return current traced memory in kilobytes."""
        return self.current_bytes / 1024

    @property
    def peak_kb(self) -> float:
        """Return peak traced memory in kilobytes."""
        return self.peak_bytes / 1024


class MemoryMonitor:
    """Manage a dedicated tracemalloc measurement session."""

    def __init__(self) -> None:
        self._active = False

    @property
    def is_active(self) -> bool:
        """Return whether this monitor owns an active tracing session."""
        return self._active

    def start(self) -> None:
        """Start memory tracing."""
        if self._active:
            raise RuntimeError("Memory monitor is already active")

        if tracemalloc.is_tracing():
            raise RuntimeError(
                "Another tracemalloc session is already active"
            )

        tracemalloc.start()
        self._active = True

    def _ensure_active(self) -> None:
        """Ensure this monitor has an active tracing session."""
        if not self._active or not tracemalloc.is_tracing():
            raise RuntimeError("Memory monitor is not active")

    def snapshot(self) -> MemorySnapshot:
        """Return the current and peak traced memory usage."""
        self._ensure_active()

        current_bytes, peak_bytes = tracemalloc.get_traced_memory()

        return MemorySnapshot(
            current_bytes=current_bytes,
            peak_bytes=peak_bytes,
        )

    def reset_peak(self) -> None:
        """Reset the peak measurement to the current memory level."""
        self._ensure_active()
        tracemalloc.reset_peak()

    def stop(self) -> MemorySnapshot:
        """Capture final measurements and stop memory tracing."""
        self._ensure_active()

        final_snapshot = self.snapshot()
        tracemalloc.stop()
        self._active = False

        return final_snapshot

    def __enter__(self) -> Self:
        """Start monitoring when entering a context manager."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Stop monitoring when leaving a context manager."""
        if self._active:
            self.stop()
