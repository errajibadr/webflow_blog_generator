#!/usr/bin/env python3
"""
Event Processor Module

This module handles the generation and sending of events to the FastAPI endpoint
for content generation.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from modules.content_generator.topic_manager import TopicManager

logger = logging.getLogger(__name__)


class EventProcessor:
    """Handles event generation and API communication."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080/events",
        topics_file: Optional[str | Path] = None,
    ):
        """Initialize the EventProcessor.

        Args:
            base_url: Base URL for the API endpoint
            topics_file: Path to the topics file (optional)
        """
        self.base_url = os.getenv("CONTENT_GENERATION_API_URL") if base_url is None else base_url
        self.topic_manager = TopicManager(topics_file) if topics_file else None

    def send_event(self, event_data: Dict[str, Any]) -> str:
        """Send an event to the API endpoint.

        Args:
            event_data: Event data to send

        Returns:
            Task ID from the API response
        """
        try:
            response = requests.post(f"{self.base_url}/", json=event_data)
            response.raise_for_status()
            return response.json()["task_id"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send event: {e}")
            raise

    def check_task_status(
        self, task_id: str, poll: bool = False, interval: int = 5
    ) -> Dict[str, Any]:
        """Check the status of a task.

        Args:
            task_id: Task ID to check
            poll: Whether to continuously poll until completion
            interval: Polling interval in seconds

        Returns:
            Task status and result
        """
        while True:
            try:
                response = requests.get(f"{self.base_url}/task/{task_id}")
                response.raise_for_status()
                result = response.json()

                if not poll:
                    return result

                if result["status"] in ["SUCCESS", "FAILURE"]:
                    return result

                logger.info(
                    f"Task status: {result['status']}. Checking again in {interval} seconds..."
                )
                time.sleep(interval)

            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to check task status: {e}")
                raise

    def process_batch(
        self, batch_size: int, tone: str = "friendly and familiar", poll_status: bool = False
    ) -> List[str]:
        """Process a batch of random topics.

        Args:
            batch_size: Number of topics to process
            tone: Desired tone for the content
            poll_status: Whether to poll for task completion

        Returns:
            List of task IDs
        """
        if not self.topic_manager:
            raise ValueError(
                "Topic manager not initialized. Please provide topics_file in constructor."
            )

        events = self.topic_manager.generate_batch_events(batch_size, tone)
        # Convert KeywordData objects to JSON serializable dictionaries
        for event in events:
            if "clusters" in event:
                for cluster, keywords in event["clusters"].items():
                    event["clusters"][cluster] = [keyword.model_dump_json() for keyword in keywords]

        # Filter out events with empty topics
        events = [event for event in events if event.get("clusters")]
        task_ids = []

        for event in events:
            task_id = self.send_event(event)
            task_ids.append(task_id)

            if poll_status:
                status = self.check_task_status(task_id, poll=True)
                logger.info(f"Task {task_id} completed with status: {status['status']}")

        return task_ids


def main():
    """Main function for testing the event processor."""
    logging.basicConfig(level=logging.INFO)

    # Example usage
    processor = EventProcessor(topics_file="website_configs/topics/dogtolib_content.csv")

    try:
        # Process a batch of 3 topics
        task_ids = processor.process_batch(batch_size=1, poll_status=True)
        logger.info(f"Processed batch with task IDs: {task_ids}")

    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise


if __name__ == "__main__":
    main()
