
import asyncio
import tempfile
from pathlib import Path

from chronosmatch.simulator.market_simulator import AsyncMarketSimulator
from chronosmatch.simulator.pipeline import run_market_pipeline


async def main():
    with tempfile.TemporaryDirectory() as directory:
        buffer_path = Path(directory) / "test.mmap"

        simulator = AsyncMarketSimulator(
            seed=42,
            price_variation_ticks=0,
        )

        result = await run_market_pipeline(
            simulator,
            order_count=100,
            buffer_path=buffer_path,
            buffer_capacity=8,
            book_capacity=128,
        )

        assert result.orders_processed == 100
        assert result.trade_count > 0
        assert result.metrics.orders_processed == 100

        print("Pipeline test: PASSED")
        print("Orders processed:", result.orders_processed)
        print("Trades executed:", result.trade_count)
        print("Throughput:", result.metrics.throughput_orders_per_second)


asyncio.run(main())
