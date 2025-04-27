#!/usr/bin/env python3
"""
Benchmark script to compare synchronous vs asynchronous content generation.

This script measures the performance difference between the two methods.
"""

import asyncio
import logging
import time
from pathlib import Path

from modules.content_generator.event_processor import EventProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("benchmark")


async def run_async_benchmark(batch_size, topics_file):
    """Run the asynchronous benchmark."""
    logger.info(f"Running async benchmark with batch size {batch_size}")

    processor = EventProcessor(
        topics_file=topics_file,
        max_concurrent_tasks=batch_size,  # Allow max concurrency for the test
    )

    start_time = time.time()
    results = await processor.process_batch_async(
        batch_size=batch_size, poll_status=True, locale="en"
    )
    elapsed = time.time() - start_time

    success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
    logger.info(f"Async benchmark completed in {elapsed:.2f} seconds")
    logger.info(f"Successfully generated {success_count}/{batch_size} articles")

    return elapsed, success_count


def run_sync_benchmark(batch_size, topics_file):
    """Run the synchronous benchmark."""
    logger.info(f"Running sync benchmark with batch size {batch_size}")

    processor = EventProcessor(topics_file=topics_file)

    start_time = time.time()
    results = processor.process_batch(batch_size=batch_size, poll_status=True, locale="en")
    elapsed = time.time() - start_time

    success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
    logger.info(f"Sync benchmark completed in {elapsed:.2f} seconds")
    logger.info(f"Successfully generated {success_count}/{batch_size} articles")

    return elapsed, success_count


async def main():
    """Main function to run benchmarks."""
    # Path to topics file
    topics_file = Path("website_configs/topics/dogtolib.csv")

    # Output directory for generated content
    output_dir = Path("benchmark_output")
    output_dir.mkdir(exist_ok=True)

    batch_sizes = [1, 3, 5]
    results = []

    for batch_size in batch_sizes:
        # Run synchronous benchmark
        sync_time, sync_success = run_sync_benchmark(batch_size, topics_file)

        # Add a small delay to avoid rate limiting
        await asyncio.sleep(2)

        # Run asynchronous benchmark
        async_time, async_success = await run_async_benchmark(batch_size, topics_file)

        speedup = sync_time / async_time if async_time > 0 else 0
        results.append(
            {
                "batch_size": batch_size,
                "sync_time": sync_time,
                "async_time": async_time,
                "speedup": speedup,
                "sync_success": sync_success,
                "async_success": async_success,
            }
        )

        # Add a delay between batch sizes
        await asyncio.sleep(5)

    # Print results summary
    logger.info("\n----- BENCHMARK RESULTS -----")
    logger.info(f"{'Batch Size':^10} | {'Sync Time':^10} | {'Async Time':^10} | {'Speedup':^10}")
    logger.info("-" * 47)

    for result in results:
        logger.info(
            f"{result['batch_size']:^10} | "
            f"{result['sync_time']:.2f}s | "
            f"{result['async_time']:.2f}s | "
            f"{result['speedup']:.2f}x"
        )

    # Calculate average speedup
    if results:
        avg_speedup = sum(r["speedup"] for r in results) / len(results)
        logger.info(f"\nAverage speedup: {avg_speedup:.2f}x")


if __name__ == "__main__":
    asyncio.run(main())
