"""Unit tests for ChronosMatch memory monitoring."""

import pytest

from chronosmatch.monitoring.memory import MemoryMonitor


def test_snapshot_requires_active_monitor() -> None:
    monitor = MemoryMonitor()

    with pytest.raises(RuntimeError, match="not active"):
        monitor.snapshot()


def test_monitor_starts_and_records_memory() -> None:
    monitor = MemoryMonitor()

    monitor.start()

    try:
        assert monitor.is_active is True

        snapshot = monitor.snapshot()

        assert snapshot.current_bytes >= 0
        assert snapshot.peak_bytes >= snapshot.current_bytes
        assert snapshot.current_kb >= 0
        assert snapshot.peak_kb >= snapshot.current_kb

    finally:
        monitor.stop()


def test_monitor_tracks_memory_allocations() -> None:
    monitor = MemoryMonitor()

    with monitor:
        allocation = bytearray(100_000)
        snapshot = monitor.snapshot()

        assert len(allocation) == 100_000
        assert snapshot.current_bytes > 0
        assert snapshot.peak_bytes >= snapshot.current_bytes


def test_reset_peak_updates_peak_measurement() -> None:
    monitor = MemoryMonitor()

    with monitor:
        retained_allocation = bytearray(100_000)
        assert len(retained_allocation) == 100_000

        # Create a temporary allocation to establish a high peak.
        temporary_allocation = bytearray(500_000)
        del temporary_allocation

        before_reset = monitor.snapshot()

        # Verify the previous peak is substantially above current usage.
        assert (
            before_reset.peak_bytes
            > before_reset.current_bytes + 400_000
        )

        monitor.reset_peak()

        after_reset = monitor.snapshot()

        assert after_reset.current_bytes > 0
        assert after_reset.peak_bytes >= after_reset.current_bytes
        assert after_reset.peak_bytes < before_reset.peak_bytes


def test_stop_returns_final_snapshot() -> None:
    monitor = MemoryMonitor()
    monitor.start()

    final_snapshot = monitor.stop()

    assert final_snapshot.current_bytes >= 0
    assert final_snapshot.peak_bytes >= final_snapshot.current_bytes
    assert monitor.is_active is False


def test_starting_twice_is_rejected() -> None:
    monitor = MemoryMonitor()

    monitor.start()

    try:
        with pytest.raises(RuntimeError, match="already active"):
            monitor.start()
    finally:
        monitor.stop()


def test_context_manager_stops_monitor() -> None:
    monitor = MemoryMonitor()

    with monitor:
        assert monitor.is_active is True

    assert monitor.is_active is False


def test_context_manager_stops_after_exception() -> None:
    monitor = MemoryMonitor()

    with pytest.raises(ValueError, match="test error"), monitor:
        raise ValueError("test error")

    assert monitor.is_active is False