#!/usr/bin/env python3
"""Test script for decoding and saving image data locally."""

import json
import logging
from pathlib import Path

from modules.content_generator.models import BlogArticle

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_test_data(task_id: str) -> dict:
    """Load test data from a JSON file.

    Args:
        task_id: The task ID to load data for

    Returns:
        dict: The loaded test data
    """
    test_data_dir = Path("tests/test_data")
    test_data_dir.mkdir(parents=True, exist_ok=True)

    test_data_file = test_data_dir / f"{task_id}.json"

    if not test_data_file.exists():
        logger.error(f"Test data file not found: {test_data_file}")
        raise FileNotFoundError(f"Test data file not found: {test_data_file}")

    with open(test_data_file, "r", encoding="utf-8") as f:
        return json.load(f)


def test_image_decode(task_id: str):
    """Test decoding and saving images from a task result.

    Args:
        task_id: The task ID to test
    """
    try:
        # Load test data
        test_data = load_test_data(task_id)

        # Create output directory for test results
        output_dir = Path("tests/output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create blog article from test data
        blog_article = BlogArticle.from_api_response(test_data)

        # Export images
        exported_paths = blog_article.export_images(output_dir)

        logger.info(f"Successfully exported {len(exported_paths)} images:")
        for path in exported_paths:
            logger.info(f"  - {path}")

        # Save the processed blog article as JSON for verification
        output_json = output_dir / f"{task_id}_processed.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(blog_article.to_json_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"Saved processed blog article to {output_json}")

    except Exception as e:
        logger.error(f"Error testing image decode: {e}")
        raise


if __name__ == "__main__":
    # Test with the specified task ID
    TASK_ID = "b2680f25-7df1-48a8-9536-9dfeaefd34a9"
    test_image_decode(TASK_ID)
