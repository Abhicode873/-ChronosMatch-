
# ChronosMatch — Python vs Cython Performance Comparison

## 1. Objective

Compare the performance of the Python reference order book and the
Cython matching engine using equivalent pre-generated order workloads.

The comparison measures throughput and per-submission latency while
checking that both implementations produce identical trade sequences.

## 2. Test Environment

- Python: 3.13.5
- Operating System: Windows 11
- Platform build: 10.0.26200-SP0
- Cython book capacity: 1,024
- Benchmark trials: 5 per workload
- Workload preparation: Excluded from timed execution

## 3. Benchmark Methodology

Two workloads were tested:

- 20,000 measured orders with 2,000 warm-up orders.
- 100,000 measured orders with 10,000 warm-up orders.

The workload consists of alternating AAPL buy and sell orders.
Each buy order rests in the book, and the following sell order crosses it,
producing one trade per pair.

Both implementations process equivalent orders.

Throughput is measured using a single timer around the complete order
submission loop. Latency is measured separately using a timer around
each individual submission.

Five throughput trials were performed for each engine and workload.
The median throughput is used for comparison.

## 4. Throughput Results

### 20,000 Orders

| Metric | Python | Cython |
|---|---:|---:|
| Trial 1 | 639,243 | 1,631,202 |
| Trial 2 | 366,960 | 1,433,332 |
| Trial 3 | 725,008 | 1,622,507 |
| Trial 4 | 762,462 | 1,520,855 |
| Trial 5 | 605,807 | 1,567,361 |
| Median | 639,243 | 1,567,361 |

Cython/Python median throughput ratio: **2.45x**

### 100,000 Orders

| Metric | Python | Cython |
|---|---:|---:|
| Trial 1 | 740,521 | 1,674,287 |
| Trial 2 | 726,527 | 1,582,186 |
| Trial 3 | 555,655 | 1,701,407 |
| Trial 4 | 746,983 | 1,539,862 |
| Trial 5 | 687,509 | 1,661,016 |
| Median | 726,527 | 1,661,016 |

Cython/Python median throughput ratio: **2.29x**

Throughput is measured in orders per second.

## 5. Latency Results

### 20,000 Orders

| Percentile | Python | Cython |
|---|---:|---:|
| p50 | 1.400 us | 0.600 us |
| p95 | 1.700 us | 0.900 us |
| p99 | 2.800 us | 1.100 us |

### 100,000 Orders

| Percentile | Python | Cython |
|---|---:|---:|
| p50 | 1.500 us | 0.600 us |
| p95 | 2.700 us | 1.100 us |
| p99 | 3.500 us | 1.400 us |

Latency percentiles are from separately instrumented runs.

## 6. Correctness Verification

The benchmark compared complete trade sequences from both engines.

Results:

- 20,000-order test: 10,000 identical trades.
- 100,000-order test: 50,000 identical trades.
- Both order books finished with zero active orders.
- No trade sequence mismatch was detected.

**Correctness verification: PASSED**

## 7. Analysis

The Cython implementation achieved higher measured throughput
in both workloads.

At 20,000 orders, the median throughput ratio was 2.45x.

At 100,000 orders, the median throughput ratio was 2.29x.

The Cython engine also recorded lower p50, p95, and p99 submission
latencies in these tests.

The results demonstrate a performance advantage for the tested
Cython interface and workload on this development machine.

## 8. Limitations

This is a local microbenchmark, not a measurement of real exchange latency.

The workload repeatedly uses one resting order followed by one crossing
order. It does not represent a deep or highly populated limit order book.

The benchmark does not yet cover:

- Multiple simultaneous price levels.
- Large multi-level matching operations.
- Heavy partial-fill workloads.
- High-volume order cancellation.
- End-to-end market data and IPC latency.

The Python interface accepts Order objects, whereas the Cython interface
accepts primitive numeric fields. This difference is part of the
measured interface performance.

Further testing with more varied order-book scenarios is required
before drawing broader performance conclusions.

## 9. Conclusion

The first performance comparison demonstrated that the Cython matching
engine can process the tested workload faster than the Python reference
implementation.

The next objective is to benchmark more realistic order-book scenarios
and continue optimizing the matching engine while maintaining correctness.

These results establish an initial performance comparison for ChronosMatch.
