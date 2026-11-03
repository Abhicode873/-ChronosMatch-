
"""Unit tests for ChronosMatch performance metrics."""

import pytest

from chronosmatch.monitoring.metrics import MetricsCollector


def test_empty_snapshot_has_no_latency_values() -> None:
    collector = MetricsCollector()

    snapshot = collector.snapshot(elapsed_ns=1_000_000_000)

    assert snapshot.orders_processed == 0
    assert snapshot.trades_executed == 0
    assert snapshot.throughput_orders_per_second == 0
    assert snapshot.latency_min_ns is None
    assert snapshot.latency_max_ns is None
    assert snapshot.latency_p50_ns is None
    assert snapshot.latency_p95_ns is None
    assert snapshot.latency_p99_ns is None


def test_record_order_updates_counts() -> None:
    collector = MetricsCollector()

    collector.record_order(1000, trades=2)
    collector.record_order(2000, trades=1)
    collector.record_order(3000)

    assert collector.orders_processed == 3
    assert collector.trades_executed == 3


def test_latency_statistics_are_calculated_correctly() -> None:
    collector = MetricsCollector()

    for latency in (500, 100, 400, 200, 300):
        collector.record_order(latency)

    snapshot = collector.snapshot(elapsed_ns=1_000_000_000)

    assert snapshot.latency_min_ns == 100
    assert snapshot.latency_max_ns == 500
    assert snapshot.latency_p50_ns == 300
    assert snapshot.latency_p95_ns == 500
    assert snapshot.latency_p99_ns == 500


def test_throughput_is_calculated_correctly() -> None:
    collector = MetricsCollector()

    for _ in range(10):
        collector.record_order(1000)

    snapshot = collector.snapshot(elapsed_ns=2_000_000_000)

    assert snapshot.throughput_orders_per_second == 5.0


def test_buffer_high_watermark_tracks_maximum_size() -> None:
    collector = MetricsCollector()

    collector.record_buffer_size(4)
    collector.record_buffer_size(7)
    collector.record_buffer_size(2)
    collector.record_buffer_size(6)

    snapshot = collector.snapshot(elapsed_ns=1_000_000)

    assert snapshot.buffer_high_watermark == 7


def test_snapshot_preserves_trade_and_order_counts() -> None:
    collector = MetricsCollector()

    collector.record_order(1000, trades=3)
    collector.record_order(2000, trades=2)

    snapshot = collector.snapshot(elapsed_ns=1_000_000)

    assert snapshot.orders_processed == 2
    assert snapshot.trades_executed == 5
    assert snapshot.elapsed_ns == 1_000_000


@pytest.mark.parametrize("latency", [True, 1.5, "100"])
def test_invalid_latency_type_is_rejected(latency: object) -> None:
    collector = MetricsCollector()

    with pytest.raises(TypeError, match="latency_ns"):
        collector.record_order(latency)  # type: ignore[arg-type]


def test_negative_latency_is_rejected() -> None:
    collector = MetricsCollector()

    with pytest.raises(ValueError, match="latency_ns"):
        collector.record_order(-1)


@pytest.mark.parametrize("trades", [True, 1.5, "2"])
def test_invalid_trade_count_type_is_rejected(trades: object) -> None:
    collector = MetricsCollector()

    with pytest.raises(TypeError, match="trades"):
        collector.record_order(1000, trades=trades)  # type: ignore[arg-type]


def test_negative_trade_count_is_rejected() -> None:
    collector = MetricsCollector()

    with pytest.raises(ValueError, match="trades"):
        collector.record_order(1000, trades=-1)


def test_invalid_buffer_size_is_rejected() -> None:
    collector = MetricsCollector()

    with pytest.raises(TypeError, match="size"):
        collector.record_buffer_size(True)

    with pytest.raises(ValueError, match="size"):
        collector.record_buffer_size(-1)


def test_invalid_elapsed_time_is_rejected() -> None:
    collector = MetricsCollector()

    with pytest.raises(TypeError, match="elapsed_ns"):
        collector.snapshot(elapsed_ns=True)

    with pytest.raises(ValueError, match="elapsed_ns"):
        collector.snapshot(elapsed_ns=-1)