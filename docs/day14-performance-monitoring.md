# Day 14 — Performance Monitoring and Garbage Collection Analysis

## 1. Objective

Day 14 introduces performance monitoring and memory observation
to the ChronosMatch pipeline.

The objective is to measure:
- Processed orders and executed trades
- Pipeline throughput
- Order-processing latency percentiles
- Ring-buffer high-watermark
- Python memory usage
- Garbage collection impact

## 2. Performance Monitoring

The MetricsCollector records pipeline performance information.

### Metrics collected

| Metric | Description |
|---|---|
| Orders processed | Total orders consumed by the pipeline |
| Trades executed | Total executions produced by matching |
| Throughput | Processed orders per second |
| Minimum latency | Lowest observed order-processing latency |
| Maximum latency | Highest observed order-processing latency |
| p50 latency | 50th percentile latency |
| p95 latency | 95th percentile latency |
| p99 latency | 99th percentile latency |
| Buffer high-watermark | Highest sampled ring-buffer occupancy |

Latency is measured from order generation to consumer processing.
It includes asynchronous pipeline and buffer waiting time.
It is not a measurement of matching-engine execution time alone.

## 3. Pipeline Monitoring Demo

Command:

    python .\scripts\run_pipeline.py --orders 1000 --seed 42 --buffer-capacity 16

Observed results:

| Metric | Result |
|---|---:|
| Orders generated | 1,000 |
| Orders processed | 1,000 |
| Trades executed | 720 |
| Execution time | 0.041361 seconds |
| Pipeline rate | 24,178 orders/sec |
| Internally measured throughput | 24,295 orders/sec |
| Buffer capacity | 16 |
| Buffer high-watermark | 12 |
| Minimum latency | 64.3 us |
| Maximum latency | 3,234.6 us |
| p50 latency | 115.5 us |
| p95 latency | 152.0 us |
| p99 latency | 258.9 us |

The two throughput figures use slightly different measurement
boundaries within the pipeline.

## 4. Garbage Collection Experiment

The benchmark compares pipeline execution with Python's cyclic
garbage collector enabled and disabled.

Command:

    python .\scripts\benchmark_gc.py --orders 5000 --trials 3 --seed 42

### Results

| Metric | GC enabled | GC disabled |
|---|---:|---:|
| Median pipeline time | 138.986 ms | 130.071 ms |
| Median throughput | 35,975 orders/sec | 38,441 orders/sec |
| Median p50 latency | 121.8 us | 120.9 us |
| Median p95 latency | 186.6 us | 182.4 us |
| Median p99 latency | 328.9 us | 318.0 us |
| Median GC collections | 1 | 0 |
| Traced peak memory | 2.485 MB | 2.485 MB |

In this experiment, disabling cyclic garbage collection produced
approximately 6.9% higher median throughput.

However, the experiment used only three trials and observed only
one median collection with GC enabled.

This result is preliminary. It does not establish that disabling
garbage collection is beneficial for production workloads.

Python reference counting remains active when cyclic garbage
collection is disabled.

## 5. Memory Monitoring

The MemoryMonitor uses Python's tracemalloc interface to observe
current and peak traced memory allocations.

It supports:
- Starting memory tracing
- Reading current and peak traced memory
- Resetting the peak measurement
- Stopping tracing
- Context-manager usage

Traced Python memory is not equivalent to total process RAM.
Native allocations, memory-mapped regions and other operating-system
memory usage may not be fully represented.

## 6. Limitations

- The pipeline demo is a single-process asynchronous producer-consumer
  workflow.
- Cross-process ring-buffer operation is tested separately.
- Results depend on the local machine and runtime environment.
- Small benchmark runs are sensitive to operating-system scheduling.
- The garbage collection experiment is preliminary.
- Latency includes queueing and asynchronous scheduling, not only
  matching-engine execution.

## 7. Conclusion

Day 14 adds performance metrics, latency tracking, buffer occupancy
monitoring, memory observation and a garbage collection benchmark.

The measurements provide a foundation for future reliability,
stress testing and performance analysis.