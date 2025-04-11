#!/usr/bin/env python3
"""
Content Generator Module

This module generates SEO content for websites based on configuration.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List

from modules.content_generator.event_processor import EventProcessor
from modules.content_generator.models import BlogArticle, ImageDetail


def process_image_placeholders(content: str, image_details: List[ImageDetail]) -> str:
    """
    Replace image placeholders in content with actual image URLs.

    Args:
        content: HTML content with image placeholders
        image_details: List of ImageDetail objects containing placeholders and URLs

    Returns:
        Content with replaced image URLs
    """
    if not content:
        return content

    # Replace each placeholder with its corresponding URL
    for image_detail in image_details:
        if image_detail.placeholder and image_detail.url:
            content = content.replace(image_detail.placeholder, image_detail.url)

    return content


def generate_content(config: Dict, website_name: str) -> Path:
    """
    Generate content using the content generation API.

    Args:
        config: The loaded configuration
        website_name: Name of the website to generate content for

    Returns:
        Path to the generated content directory
    """
    logger = logging.getLogger("orchestrator.content_generator")
    website_config = config["website"]
    content_config = website_config.get("content_generation", {})

    # Determine the workspace directory
    workspace_name = website_config["website"].get("workspace", website_name)
    content_dir = Path(config["paths"]["workspaces"]) / workspace_name / "content"
    images_dir = content_dir / "images"

    # Create content and images directories if they don't exist
    os.makedirs(content_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    logger.info(f"Generating content for website: {website_name} in {content_dir}")

    # Get content generation parameters
    topics_file = content_config.get("topics_file")
    if not topics_file:
        logger.error("No topics file specified in configuration")
        raise ValueError("No topics file specified in configuration")

    batch_size = content_config.get(
        "batch_size", config.get("defaults", {}).get("content_generation", {}).get("batch_size", 2)
    )
    max_concurrent = content_config.get(
        "max_concurrent",
        config.get("defaults", {}).get("content_generation", {}).get("max_concurrent", 3),
    )

    logger.info(f"Using topics file: {topics_file}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Max concurrent: {max_concurrent}")

    # TODO: Implement local SEO support in the API and handle the local_seo option here
    if content_config.get("local_seo") is not None:
        logger.warning("Local SEO option is not yet supported in the API version")

    try:
        # Initialize the event processor with the topics file
        processor = EventProcessor(topics_file=topics_file)

        # Get the batch results first
        results = processor.get_batch_results(
            batch_size=batch_size,
            tone="friendly and familiar",  # TODO: Make this configurable
            poll_status=True,
        )

        # Then parse the results with our content directory
        processed_results = processor.parse_batch_results(results, content_dir)

        # Process each result and save to files
        for result in processed_results:
            if result["status"] == "SUCCESS" and "blog_article" in result:
                blog_article: BlogArticle = result["blog_article"]

                # Process image placeholders in the content
                if hasattr(blog_article, "content"):
                    blog_article.content = process_image_placeholders(
                        blog_article.content, blog_article.image_details
                    )

                try:
                    # Use slug for filename
                    if not blog_article.slug:
                        logger.warning("Blog article has no slug, using default name")
                        filename = blog_article.title.lower().replace(" ", "-")
                    else:
                        filename = f"{blog_article.slug}.json"

                    file_path = content_dir / filename

                    # Convert blog article to dictionary and save as JSON
                    article_data = blog_article.to_json_dict()
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(article_data, f, ensure_ascii=False, indent=4)

                    logger.info(f"Saved blog article to {file_path}")
                except Exception as e:
                    logger.error(f"Failed to save blog article: {e}")
                    raise

        logger.info(f"Generated content for website: {website_name}")
        return content_dir

    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise RuntimeError(f"Content generation failed: {e}")


# For development/testing purposes
def simulate_content_generation(config, website_name):
    """
    Simulate content generation for development purposes.

    Args:
        config: The loaded configuration
        website_name: Name of the website to generate content for

    Returns:
        Path to the simulated content directory
    """
    logger = logging.getLogger("orchestrator.content_generator")

    # Determine the workspace directory
    workspace_name = config["website"]["website"].get("workspace", website_name)
    content_dir = Path(config["paths"]["workspaces"]) / workspace_name / "content"
    images_dir = content_dir / "images"

    # Create content and images directories if they don't exist
    os.makedirs(content_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    # Create sample JSON files with blog post content
    for i in range(1, 4):
        with open(content_dir / f"blog_post_{i}.json", "w") as f:
            f.write(f"""{{
                "Titre": "Sample Blog Post {i}",
                "Slug": "sample-blog-post-{i}",
                "Résumé de l'article": "This is a summary of blog post {i} for testing purposes.",
                "auteur": "Test Author",
                "Date de publication": "01/05/2023",
                "Durée de lecture": "5 min",
                "photo article": "/images/sample_image_{i}.jpg",
                "Contenu article": "<h2>Sample Content</h2><p>This is sample content for blog post {i}.</p>"
            }}""")

    # Create sample images
    for i in range(1, 4):
        with open(images_dir / f"sample_image_{i}.jpg", "w") as f:
            f.write(f"Sample image {i} content")

    logger.info(f"Created simulated content for {website_name} at {content_dir}")
    return content_dir
