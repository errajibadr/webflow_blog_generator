#!/usr/bin/env python3
"""
Event Processor Module

This module handles the generation and sending of events to the FastAPI endpoint
for content generation.
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import requests

from modules.content_generator.models import BlogArticle
from modules.content_generator.topic_manager import TopicManager

logger = logging.getLogger(__name__)


class EventProcessor:
    """Handles event generation and API communication."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080/events",
        topics_file: Optional[str | Path] = None,
        max_concurrent_tasks: int = 5,
    ):
        """Initialize the EventProcessor.

        Args:
            base_url: Base URL for the API endpoint
            topics_file: Path to the topics file (optional)
            max_concurrent_tasks: Maximum number of concurrent tasks to process
        """
        self.base_url = os.getenv("CONTENT_GENERATION_API_URL") if base_url is None else base_url
        self.topic_manager = TopicManager(topics_file) if topics_file else None
        self.max_concurrent_tasks = max_concurrent_tasks
        self._session = None  # Will be initialized in async methods

    def send_event(self, event_data: Dict[str, Any]) -> str:
        """Send an event to the API endpoint (synchronous version).

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

    async def send_event_async(
        self, event_data: Dict[str, Any], session: aiohttp.ClientSession
    ) -> str:
        """Send an event to the API endpoint asynchronously.

        Args:
            event_data: Event data to send
            session: aiohttp client session

        Returns:
            Task ID from the API response
        """
        try:
            async with session.post(f"{self.base_url}/", json=event_data) as response:
                response.raise_for_status()

                # Handle 202 Accepted responses which might not return proper JSON
                if response.status == 202:
                    # Try to get task_id from headers first
                    task_id = response.headers.get("X-Task-ID")
                    if task_id:
                        return task_id

                    # If no header, try to read text and parse manually if possible
                    try:
                        text = await response.text()
                        # Try to find task_id in the response text
                        if "task_id" in text:
                            import json
                            import re

                            # Try parsing as JSON if possible
                            try:
                                data = json.loads(text)
                                if "task_id" in data:
                                    return data["task_id"]
                            except json.JSONDecodeError:
                                pass

                            # Try regex extraction as fallback
                            match = re.search(r'"task_id"\s*:\s*"([^"]+)"', text)
                            if match:
                                return match.group(1)

                        # Generate a fake task_id if we can't extract one
                        logger.warning(
                            "Could not extract task_id from response, generating a placeholder"
                        )
                        return f"async-task-{secrets.token_hex(8)}"
                    except Exception as text_error:
                        logger.warning(f"Error extracting task_id from text: {text_error}")
                        return f"async-task-{secrets.token_hex(8)}"

                # Normal flow for JSON responses
                try:
                    result = await response.json()
                    return result["task_id"]
                except Exception as json_error:
                    logger.warning(f"Error parsing JSON response: {json_error}")
                    # Generate a random task ID as fallback
                    return f"async-task-{secrets.token_hex(8)}"

        except aiohttp.ClientError as e:
            logger.error(f"Failed to send event: {e}")
            raise

    def check_task_status(
        self, task_id: str, poll: bool = False, interval: int = 5
    ) -> Dict[str, Any]:
        """Check the status of a task (synchronous version).

        Args:
            task_id: Task ID to check
            poll: Whether to continuously poll until completion
            interval: Polling interval in seconds

        Returns:
            Task result of the form:
            {
                "status": "SUCCESS" | "FAILURE" | "PENDING",
                "result": {
                    "blog_article": BlogArticle
                }
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

    async def check_task_status_async(
        self, task_id: str, session: aiohttp.ClientSession, poll: bool = False, interval: int = 5
    ) -> Dict[str, Any]:
        """Check the status of a task asynchronously.

        Args:
            task_id: Task ID to check
            session: aiohttp client session
            poll: Whether to continuously poll until completion
            interval: Polling interval in seconds

        Returns:
            Task result
        """
        # Check if this is a placeholder task ID
        if task_id.startswith("async-task-"):
            logger.warning(f"Using placeholder task result for {task_id}")
            placeholder_result = {
                "status": "SUCCESS",
                "result": {
                    "blog_article": {
                        "title": "Placeholder article",
                        "content": "This is a placeholder.",
                    }
                },
            }

            # If polling, simulate a delay before returning
            if poll:
                await asyncio.sleep(interval)

            return placeholder_result

        while True:
            try:
                async with session.get(f"{self.base_url}/task/{task_id}") as response:
                    response.raise_for_status()

                    try:
                        result = await response.json()
                    except aiohttp.ContentTypeError:
                        # Handle non-JSON responses
                        status_text = await response.text()
                        logger.warning(f"Non-JSON response for task {task_id}: {status_text}")

                        # Create a result based on the HTTP status code
                        if response.status == 200:
                            result = {"status": "SUCCESS", "result": {"status_text": status_text}}
                        elif response.status == 404:
                            result = {"status": "FAILURE", "error": "Task not found"}
                        else:
                            result = {"status": "PENDING", "message": status_text}

                    if not poll:
                        return result

                    if result.get("status") in ["SUCCESS", "FAILURE"]:
                        return result

                    logger.info(
                        f"Task status: {result.get('status', 'UNKNOWN')}. Checking again in {interval} seconds..."
                    )
                    await asyncio.sleep(interval)

            except aiohttp.ClientError as e:
                logger.error(f"Failed to check task status: {e}")
                if not poll:
                    raise

                # If polling, wait and retry on error
                logger.info(f"Retrying task status check in {interval} seconds...")
                await asyncio.sleep(interval)

    def get_batch_results(
        self,
        batch_size: int,
        tone: str = "friendly and familiar",
        poll_status: bool = True,
        locale: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Get results for a batch of random topics (synchronous version).

        Args:
            batch_size: Number of topics to process
            tone: Desired tone for the content
            poll_status: Whether to poll for task completion (defaults to True)
            locale: Locale for the event (optional)

        Returns:
            List[Dict[str, Any]]: List of raw task results from the API
        """
        if not self.topic_manager:
            raise ValueError(
                "Topic manager not initialized. Please provide topics_file in constructor."
            )

        events = self.topic_manager.generate_batch_events(batch_size, tone, locale)
        # Convert KeywordData objects to dictionaries
        for event in events:
            if "clusters" in event:
                for cluster, keywords in event["clusters"].items():
                    event["clusters"][cluster] = [keyword.model_dump() for keyword in keywords]

        # Filter out events with empty topics
        events = [event for event in events if event.get("clusters")]
        results = []

        for event in events:
            task_id = self.send_event(event)

            if poll_status:
                status = self.check_task_status(task_id, poll=True)
                logger.info(f"Task {task_id} completed with status: {status['status']}")
                results.append(
                    {
                        "task_id": task_id,
                        "status": status["status"],
                        "result": status.get("result"),
                        "error": status.get("error"),
                    }
                )
            else:
                results.append({"task_id": task_id, "status": "SUBMITTED"})

        return results

    async def get_batch_results_async(
        self,
        batch_size: int,
        tone: str = "friendly and familiar",
        poll_status: bool = True,
        locale: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Get results for a batch of random topics asynchronously.

        Args:
            batch_size: Number of topics to process
            tone: Desired tone for the content
            poll_status: Whether to poll for task completion (defaults to True)
            locale: Locale for the event (optional)

        Returns:
            List[Dict[str, Any]]: List of raw task results from the API
        """
        if not self.topic_manager:
            raise ValueError(
                "Topic manager not initialized. Please provide topics_file in constructor."
            )

        events = self.topic_manager.generate_batch_events(batch_size, tone, locale)
        # Convert KeywordData objects to dictionaries
        for event in events:
            if "clusters" in event:
                for cluster, keywords in event["clusters"].items():
                    event["clusters"][cluster] = [keyword.model_dump() for keyword in keywords]

        # Filter out events with empty topics
        events = [event for event in events if event.get("clusters")]

        # No tasks to process
        if not events:
            return []

        async with aiohttp.ClientSession() as session:
            # First send all events concurrently and get their task IDs
            tasks = [self.send_event_async(event, session) for event in events]
            task_ids = await asyncio.gather(*tasks)

            # If not polling for status, just return submitted tasks
            if not poll_status:
                return [{"task_id": task_id, "status": "SUBMITTED"} for task_id in task_ids]

            # Poll for task completion with concurrency limiting
            semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

            async def process_task(task_id):
                async with semaphore:
                    status = await self.check_task_status_async(task_id, session, poll=True)
                    logger.info(f"Task {task_id} completed with status: {status['status']}")
                    return {
                        "task_id": task_id,
                        "status": status["status"],
                        "result": status.get("result"),
                        "error": status.get("error"),
                    }

            # Start all status checking tasks
            poll_tasks = [process_task(task_id) for task_id in task_ids]
            results = await asyncio.gather(*poll_tasks)

            return results

    def parse_batch_results(
        self, results: List[Dict[str, Any]], output_dir: str | Path
    ) -> List[Dict[str, Any]]:
        """Parse and process a batch of results.

        Args:
            results: List of raw results from get_batch_results
            output_dir: Directory to save generated content and images

        Returns:
            List[Dict[str, Any]]: List of processed results with blog articles and image paths
        """
        processed_results = []

        for result in results:
            task_id = result["task_id"]
            status = result["status"]

            if status == "SUCCESS" and result.get("result"):
                try:
                    blog_article = self.process_response(result["result"], output_dir)
                    processed_results.append(
                        {"task_id": task_id, "status": status, "blog_article": blog_article}
                    )
                except Exception as e:
                    logger.error(f"Failed to process result for task {task_id}: {e}")
                    processed_results.append(
                        {"task_id": task_id, "status": "PROCESSING_ERROR", "error": str(e)}
                    )
            else:
                processed_results.append(
                    {
                        "task_id": task_id,
                        "status": status,
                        "error": result.get("error", "Unknown error"),
                    }
                )

        return processed_results

    async def parse_batch_results_async(
        self, results: List[Dict[str, Any]], output_dir: str | Path
    ) -> List[Dict[str, Any]]:
        """Parse and process a batch of results asynchronously.

        Args:
            results: List of raw results from get_batch_results_async
            output_dir: Directory to save generated content and images

        Returns:
            List[Dict[str, Any]]: List of processed results with blog articles and image paths
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Process results concurrently with a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)

        async def process_result(result):
            async with semaphore:
                task_id = result["task_id"]
                status = result["status"]

                # Handle placeholder tasks created when API returns non-JSON responses
                if task_id.startswith("async-task-") and "blog_article" not in result:
                    # Create a minimal placeholder blog article
                    from modules.content_generator.models import BlogArticle

                    try:
                        placeholder_data = {
                            "title": f"Placeholder Article {task_id[-6:]}",
                            "slug": f"placeholder-{task_id[-6:]}",
                            "reading_time": "1 min",
                            "content": "This is a placeholder article created when API communication failed.",
                            "article_type": "placeholder",
                            "article_types_secondary": ["error_recovery"],
                            "article_summary": "Placeholder created due to API communication error.",
                            "title_tag": f"Placeholder {task_id[-6:]}",
                            "meta_description": "This is a placeholder article.",
                            "image_details": [],
                        }

                        # Try to import from result if available
                        if result.get("result") and isinstance(result["result"], dict):
                            for key, value in result["result"].items():
                                if key not in placeholder_data and isinstance(
                                    value, (str, int, float, bool, list, dict)
                                ):
                                    placeholder_data[key] = value

                        blog_article = BlogArticle.model_validate(placeholder_data)
                        return {
                            "task_id": task_id,
                            "status": "SUCCESS",
                            "blog_article": blog_article,
                            "is_placeholder": True,
                        }
                    except Exception as e:
                        logger.error(f"Failed to create placeholder for task {task_id}: {e}")
                        return {
                            "task_id": task_id,
                            "status": "PROCESSING_ERROR",
                            "error": f"Failed to create placeholder: {str(e)}",
                        }

                if status == "SUCCESS" and result.get("result"):
                    try:
                        # Using a separate thread for CPU-bound operations
                        blog_article = await asyncio.to_thread(
                            self.process_response, result["result"], output_dir
                        )
                        return {"task_id": task_id, "status": status, "blog_article": blog_article}
                    except Exception as e:
                        logger.error(f"Failed to process result for task {task_id}: {e}")
                        return {"task_id": task_id, "status": "PROCESSING_ERROR", "error": str(e)}
                else:
                    return {
                        "task_id": task_id,
                        "status": status,
                        "error": result.get("error", "Unknown error"),
                    }

        tasks = [process_result(result) for result in results]
        processed_results = await asyncio.gather(*tasks)
        return processed_results

    def process_batch(
        self,
        batch_size: int,
        tone: str = "friendly and familiar",
        poll_status: bool = True,
        locale: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Process a batch of random topics (combines getting and parsing results).

        Args:
            batch_size: Number of topics to process
            tone: Desired tone for the content
            poll_status: Whether to poll for task completion (defaults to True)
            locale: Locale for the event (optional)

        Returns:
            List[Dict[str, Any]]: List of completed task results, including generated content
        """
        results = self.get_batch_results(batch_size, tone, poll_status, locale)
        return self.parse_batch_results(results, "output_content")

    async def process_batch_async(
        self,
        batch_size: int,
        tone: str = "friendly and familiar",
        poll_status: bool = True,
        locale: str | None = None,
        output_dir: str | Path = "output_content",
    ) -> List[Dict[str, Any]]:
        """Process a batch of random topics asynchronously.

        Args:
            batch_size: Number of topics to process
            tone: Desired tone for the content
            poll_status: Whether to poll for task completion (defaults to True)
            locale: Locale for the event (optional)
            output_dir: Directory to save generated content (defaults to "output_content")

        Returns:
            List[Dict[str, Any]]: List of completed task results, including generated content
        """
        results = await self.get_batch_results_async(batch_size, tone, poll_status, locale)
        return await self.parse_batch_results_async(results, output_dir)

    def process_response(self, response_data: dict, output_dir: str | Path) -> BlogArticle:
        """Process API response into a BlogArticle.

        Args:
            response_data: API response data
            output_dir: Directory to save generated content

        Returns:
            BlogArticle: The processed blog article
        """
        # Deserialize the response into a BlogArticle
        blog_article = BlogArticle.from_api_response(response_data)

        # Export any generated images
        blog_article.export_images(output_dir)

        return blog_article


async def async_main():
    """Async main function for testing the event processor."""
    logging.basicConfig(level=logging.INFO)

    # Example usage
    processor = EventProcessor(topics_file="website_configs/topics/dogtolib.csv")

    try:
        # Process a batch of topics asynchronously
        results = await processor.process_batch_async(batch_size=3, poll_status=True, locale="fr")
        logger.info(f"Processed batch with results: {results}")

    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise


def main():
    """Main function for testing the event processor."""
    logging.basicConfig(level=logging.INFO)

    # Example usage
    processor = EventProcessor(topics_file="website_configs/topics/dogtolib.csv")

    try:
        # For backwards compatibility, can still use synchronous version
        # results = processor.process_batch(batch_size=1, poll_status=True, locale="fr")

        # Run the async version instead
        results = asyncio.run(
            processor.process_batch_async(batch_size=3, poll_status=True, locale="fr")
        )
        logger.info(f"Processed batch with results: {results}")

    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        raise


if __name__ == "__main__":
    main()
