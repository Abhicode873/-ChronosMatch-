
"""Performance metrics collection for ChronosMatch."""

from dataclasses import dataclass
from time import perf_counter_ns


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    """Immutable snapshot of collected performance metrics."""

    orders_processed: int
    trades_executed: int
    elapsed_ns: int
    throughput_orders_per_second: float
    latency_min_ns: int | None
    latency_max_ns: int | None
    latency_p50_ns: int | None
    latency_p95_ns: int | None
    latency_p99_ns: int | None
    buffer_high_watermark: int


class MetricsCollector:
    """Collect order latency, throughput and buffer utilization."""

    def __init__(self) -> None:
        self._started_ns = perf_counter_ns()
        self._latencies_ns: list[int] = []
        self._orders_processed = 0
        self._trades_executed = 0
        self._buffer_high_watermark = 0

    @property
    def orders_processed(self) -> int:
        """Return the number of recorded orders."""
        return self._orders_processed

    @property
    def trades_executed(self) -> int:
        """Return the total number of recorded trades."""
        return self._trades_executed

    def record_order(
        self,
        latency_ns: int,
        *,
        trades: int = 0,
    ) -> None:
        """Record one processed order and its execution latency."""
        if type(latency_ns) is not int:
            raise TypeError("latency_ns must be an integer")

        if latency_ns < 0:
            raise ValueError("latency_ns cannot be negative")

        if type(trades) is not int:
            raise TypeError("trades must be an integer")

        if trades < 0:
            raise ValueError("trades cannot be negative")

        self._latencies_ns.append(latency_ns)
        self._orders_processed += 1
        self._trades_executed += trades

    def record_buffer_size(self, size: int) -> None:
        """Record a buffer observation and update its high-watermark."""
        if type(size) is not int:
            raise TypeError("size must be an integer")

        if size < 0:
            raise ValueError("size cannot be negative")

        self._buffer_high_watermark = max(
            self._buffer_high_watermark,
            size,
        )

    @staticmethod
    def _percentile(
        sorted_values: list[int],
        percent: float,
    ) -> int | None:
        """Calculate a nearest-rank percentile."""
        if not sorted_values:
            return None

        rank = (len(sorted_values) * percent + 99) // 100
        index = max(0, int(rank) - 1)

        return sorted_values[index]

    def snapshot(
        self,
        *,
        elapsed_ns: int | None = None,
    ) -> MetricsSnapshot:
        """Create an immutable metrics snapshot."""
        if elapsed_ns is None:
            elapsed_ns = perf_counter_ns() - self._started_ns

        if type(elapsed_ns) is not int:
            raise TypeError("elapsed_ns must be an integer")

        if elapsed_ns < 0:
            raise ValueError("elapsed_ns cannot be negative")

        throughput = (
            self._orders_processed / (elapsed_ns / 1_000_000_000)
            if elapsed_ns > 0
            else 0.0
        )

        sorted_latencies = sorted(self._latencies_ns)

        return MetricsSnapshot(
            orders_processed=self._orders_processed,
            trades_executed=self._trades_executed,
            elapsed_ns=elapsed_ns,
            throughput_orders_per_second=throughput,
            latency_min_ns=(
                sorted_latencies[0] if sorted_latencies else None
            ),
            latency_max_ns=(
                sorted_latencies[-1] if sorted_latencies else None
            ),
            latency_p50_ns=self._percentile(sorted_latencies, 50),
            latency_p95_ns=self._percentile(sorted_latencies, 95),
            latency_p99_ns=self._percentile(sorted_latencies, 99),
            buffer_high_watermark=self._buffer_high_watermark,
        )
