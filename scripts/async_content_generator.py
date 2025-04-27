#!/usr/bin/env python3
"""
Async Content Generator Example

This script demonstrates how to use the async features of the EventProcessor
to generate content concurrently.
"""

import argparse
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

from modules.content_generator.event_processor import EventProcessor


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate content asynchronously")
    parser.add_argument("--topics", "-t", type=str, required=True, help="Path to topics CSV file")
    parser.add_argument(
        "--batch-size",
        "-b",
        type=int,
        default=5,
        help="Number of articles to generate (default: 5)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output_content",
        help="Output directory for generated content (default: output_content)",
    )
    parser.add_argument(
        "--locale", "-l", type=str, default="en", help="Locale for generated content (default: en)"
    )
    parser.add_argument(
        "--tone",
        type=str,
        default="friendly and familiar",
        help="Tone for generated content (default: friendly and familiar)",
    )
    parser.add_argument(
        "--max-concurrent",
        "-m",
        type=int,
        default=10,
        help="Maximum number of concurrent tasks (default: 10)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


async def main():
    """Run the async content generation example."""
    args = parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("async_generator")

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    topics_file = Path(args.topics)
    if not topics_file.exists():
        logger.error(f"Topics file not found: {topics_file}")
        return

    logger.info(f"Starting async content generation")
    logger.info(f"Using topics file: {topics_file}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Max concurrent tasks: {args.max_concurrent}")

    # Initialize the EventProcessor with the async configuration
    processor = EventProcessor(
        topics_file=str(topics_file), max_concurrent_tasks=args.max_concurrent
    )

    # Measure performance
    start_time = time.time()

    try:
        # Process the batch asynchronously
        results = await processor.process_batch_async(
            batch_size=args.batch_size,
            tone=args.tone,
            locale=args.locale,
            poll_status=True,
            output_dir=output_dir,
        )

        # Calculate success rate
        total = len(results)
        success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
        error_count = total - success_count

        # Report results
        elapsed = time.time() - start_time
        logger.info(f"Content generation completed in {elapsed:.2f} seconds")
        logger.info(f"Successfully generated {success_count}/{total} articles")

        if error_count > 0:
            logger.warning(f"Failed to generate {error_count} articles")
            for result in results:
                if result.get("status") != "SUCCESS":
                    logger.warning(
                        f"Task {result.get('task_id')}: {result.get('error', 'Unknown error')}"
                    )

        # List generated articles
        logger.info("Generated articles:")
        for result in results:
            if result.get("status") == "SUCCESS" and "blog_article" in result:
                blog = result["blog_article"]
                logger.info(f"  - {blog.title} ({blog.slug}.json)")

    except Exception as e:
        logger.error(f"Error during content generation: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
