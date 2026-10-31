
# ChronosMatch — Asynchronous Market Simulator

## 1. Objective

Develop an asynchronous market simulator to generate realistic simulated
limit-order requests for the ChronosMatch trading engine.

The simulator uses Python asyncio and the existing validated Order model.

## 2. Implemented Features

- Asynchronous order generation using an async generator.
- BUY and SELL order generation.
- Support for multiple trading symbols.
- Configurable base prices.
- Configurable price variation.
- Configurable minimum and maximum quantities.
- Unique sequential order IDs.
- Monotonic timestamps.
- Reproducible order generation through a random seed.
- Configurable delay between generated orders.
- Input validation and error handling.

## 3. Supported Default Symbols

| Symbol | Base Price (Ticks) |
|---|---:|
| AAPL | 100,000 |
| MSFT | 400,000 |
| GOOGL | 150,000 |

## 4. Test Results

Dedicated simulator unit tests cover:

- Valid order generation.
- Multiple symbol generation.
- BUY and SELL distribution.
- Reproducibility with identical seeds.
- Unique IDs across multiple streams.
- Custom simulator configuration.
- Invalid order counts.
- Invalid price and quantity configuration.
- Asynchronous task cooperation.

Simulator unit tests: 15 passed.

Complete project test suite: 104 passed.

Ruff code-quality checks: All checks passed.

## 5. Demonstration Results

Command:

`python scripts/run_market_simulator.py --orders 1000 --seed 42`

Environment:
- Python 3.13.5
- Windows 11

Observed results:

| Metric | Result |
|---|---:|
| Requested orders | 1,000 |
| Generated orders | 1,000 |
| Execution time | 0.005737 seconds |
| Observed generation rate | 174,319 orders/sec |
| BUY orders | 495 |
| SELL orders | 505 |
| AAPL orders | 332 |
| GOOGL orders | 340 |
| MSFT orders | 328 |

## 6. Interpretation

The demonstration verified that the simulator successfully generated
1,000 validated orders with unique identifiers and supported trading symbols.

The generation rate is a local measurement with zero configured delay.
It does not represent matching-engine throughput or end-to-end trading
system performance.

## 7. Current Scope and Next Steps

The simulator currently generates Order objects independently.

Integration with the binary protocol, memory-mapped ring buffer,
and Cython matching engine is planned for the next development phase.

The next objective is to establish an end-to-end order flow from
asynchronous generation through IPC into the matching engine.
