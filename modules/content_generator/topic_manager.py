#!/usr/bin/env python3
"""
Topic Manager Module

This module handles reading topics from files, random topic selection,
and converting topics into events for the content generation system.
"""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any, Dict, List

from modules.content_generator.models import KeywordData
from modules.utils.csv_processor import TopicsCSVProcessor

logger = logging.getLogger(__name__)


class TopicManager:
    """Manages topic selection and event generation for content generation."""

    def __init__(self, topics_file: str | Path):
        """Initialize the TopicManager.

        Args:
            topics_file: Path to the JSON file containing topics
        """
        self.topics_file = Path(topics_file)
        self.topics: Dict[str, List[KeywordData]] = {}
        self._load_topics()

    def _load_topics(self) -> None:
        """Load topics from the JSON file."""
        try:
            self.topics = TopicsCSVProcessor().read_csv(input_path=self.topics_file)
            logger.info(f"Loaded {len(self.topics)} topics from {self.topics_file}")
        except Exception as e:
            logger.error(f"Failed to load topics from {self.topics_file}: {e}")
            raise

    def select_random_topics(self, count: int = 1) -> Dict[str, List[KeywordData]]:
        """Select random topics from the loaded topics.

        Args:
            count: Number of topics to select

        Returns:
            List of selected topics
        """
        if not self.topics:
            raise ValueError("No topics available")

        # Ensure we don't try to sample more topics than available
        available_count = min(count, len(self.topics))
        topics = random.sample(list(self.topics.keys()), available_count)
        return {topic: self.topics[topic] for topic in topics}

    def create_event(
        self,
        topic: Dict[str, List[KeywordData]],
        action: str = "content_generation",
        tone: str = "friendly and familiar",
        backlinks: List[str] = [],
    ) -> Dict[str, Any]:
        """Create an event from a topic.

        Args:
            topic: Topic data
            tone: Desired tone for the content

        Returns:
            Event data conforming to EventSchema
        """

        event = {
            "action": action,
            "tone": tone,
            "clusters": topic,
            "backlinks": backlinks,
        }

        return event

    def create_random_event(
        self,
        tone: str = "friendly and familiar",
        backlinks: List[str] = [],
    ) -> Dict[str, Any]:
        return self.create_event(self.select_random_topics(1), tone=tone, backlinks=backlinks)

    def generate_batch_events(
        self, batch_size: int, tone: str = "friendly and familiar"
    ) -> List[Dict[str, Any]]:
        """Generate multiple events for batch processing.

        Args:
            batch_size: Number of events to generate
            tone: Desired tone for the content

        Returns:
            List of event data
        """
        topics = self.select_random_topics(batch_size)
        return [
            self.create_event({topic: keywords}, tone=tone) for topic, keywords in topics.items()
        ]

    def get_remaining_topics_count(self) -> int:
        """Get the count of remaining available topics.

        Returns:
            Number of remaining topics
        """
        return len(self.topics)


if __name__ == "__main__":
    topic_manager = TopicManager(topics_file="website_configs/topics/dogtolib_content.csv")

    # print(topic_manager.select_random_topics(1))
    print(topic_manager.create_random_event(tone="friendly and familiar"))
