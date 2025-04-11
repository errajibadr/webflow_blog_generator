#!/usr/bin/env python3
"""Script to fetch and save task data for testing."""

import json
import logging
from pathlib import Path

from modules.content_generator.event_processor import EventProcessor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_and_save_task_data(task_id: str):
    """Fetch task data and save it locally.

    Args:
        task_id: The task ID to fetch
    """
    try:
        # Initialize EventProcessor
        processor = EventProcessor()

        # Create test data directory
        test_data_dir = Path("tests/test_data")
        test_data_dir.mkdir(parents=True, exist_ok=True)

        # Fetch task status and result
        logger.info(f"Fetching task data for ID: {task_id}")
        task_result = processor.check_task_status(task_id)

        # Save raw task data
        output_file = test_data_dir / f"{task_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(task_result.get("result", {}), f, ensure_ascii=False, indent=2)

        logger.info(f"Saved task data to {output_file}")

        # Also save processed result
        if task_result["status"] == "SUCCESS" and task_result.get("result"):
            output_dir = Path("tests/output")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Process the response
            blog_article, image_paths = processor.process_response(
                task_result["result"], output_dir
            )

            # Save processed blog article
            processed_file = test_data_dir / f"{task_id}_processed.json"
            with open(processed_file, "w", encoding="utf-8") as f:
                json.dump(blog_article.to_json_dict(), f, ensure_ascii=False, indent=2)

            logger.info(f"Saved processed blog article to {processed_file}")
            logger.info(f"Exported {len(image_paths)} images to {output_dir}")

    except Exception as e:
        logger.error(f"Error fetching task data: {e}")
        raise


if __name__ == "__main__":
    # Fetch data for the specified task ID
    TASK_ID = "b2680f25-7df1-48a8-9536-9dfeaefd34a9"
    fetch_and_save_task_data(TASK_ID)
