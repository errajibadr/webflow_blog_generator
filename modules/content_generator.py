#!/usr/bin/env python3
"""
Content Generator Module

This module generates SEO content for websites based on configuration.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


def generate_content(config, website_name):
    """
    Generate content using the content generation module.

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

    # Create content directory if it doesn't exist
    os.makedirs(content_dir, exist_ok=True)

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

    # Call the content generation script using UV
    cmd = [
        "uv",
        "run",
        "main.py",
        "--input",
        topics_file,
        "--output",
        str(content_dir),
        "--batch",
        str(batch_size),
        "--max-concurrent",
        str(max_concurrent),
    ]

    logger.info(f"Running content generation: {' '.join(cmd)}")

    try:
        # Run the command
        process = subprocess.run(cmd, check=True, text=True, capture_output=True)

        # Log output
        if process.stdout:
            logger.debug(f"Content generation output: {process.stdout}")

        logger.info(f"Generated content for website: {website_name}")
        return content_dir

    except subprocess.CalledProcessError as e:
        logger.error(f"Content generation failed with code {e.returncode}: {e.stderr}")
        raise RuntimeError(f"Content generation failed with code {e.returncode}")

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
