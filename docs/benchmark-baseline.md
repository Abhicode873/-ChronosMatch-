
# ChronosMatch — Python Baseline Benchmark

## Purpose

Record the initial performance of the Python reference order book
before introducing Cython optimizations and zero-copy IPC.

## Environment

- Python: 3.13.5
- Operating system: Windows 11
- Benchmark date: 2026-10-18
- Implementation: Python reference order book

## Workload

- Measured orders: 20,000
- Warm-up orders: 2,000
- Instrument: AAPL
- Pattern: Alternating buy and sell orders at fixed prices
- Expected trades: 10,000
- Expected final active orders: 0

Order construction is excluded from the timed order-submission runs.

## Results

### Throughput run

- Elapsed time: 0.031386 seconds
- Throughput: 637,229 orders/second
- Trades executed: 10,000

### Separate per-submission latency run

| Metric | Result |
|---|---:|
| p50 | 1.4 µs |
| p95 | 2.1 µs |
| p99 | 3.1 µs |
| Maximum | 751.0 µs |

## Interpretation

The benchmark completed its workload and verified the expected trade
count and empty final order book.

The maximum latency is substantially higher than p99. This may reflect
runtime or operating-system noise, but additional repeated runs are
required to investigate the cause.

Throughput and latency were measured in separate runs. These results
are specific to the local synthetic workload and must not be interpreted
as real exchange latency.

## Limitations

- Results are from a preliminary benchmark, not a statistical study.
- Hardware details and background system activity were not recorded.
- The workload exercises a narrow, alternating buy/sell scenario.
- No comparison with Cython or IPC implementations has been performed.

## Reproduction

Run from the project root:

```powershell
.\.venv\Scripts\python.exe benchmarks\baseline.py --orders 20000 --warmup-orders 2000
```

## Future comparison

Repeat the same workload after implementing the Cython matching engine.
Compare throughput and p50, p95, p99, and maximum latency. Use multiple
trials before drawing conclusions about performance improvements.
