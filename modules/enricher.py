#!/usr/bin/env python3
"""
Website Enricher Module

This module wraps the existing Node.js website enricher to integrate generated content
into the exported website.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import yaml


def enrich_website(config: Dict[str, Any], website_name: str) -> Path:
    """
    Enrich website with content using the website enricher module.

    Args:
        config: The loaded configuration
        website_name: Name of the website to enrich

    Returns:
        Path to the enriched website directory
    """
    logger = logging.getLogger("orchestrator.enricher")
    website_config = config["website"]
    enricher_config = website_config.get("website_enricher", {})

    # Determine the workspace directory
    workspace_name = website_config["website"].get("workspace", website_name)
    workspace_dir = Path(config["paths"]["workspaces"]) / workspace_name

    export_dir = workspace_dir / "export"
    content_dir = workspace_dir / "content"
    output_dir = workspace_dir / "output"

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Enriching website: {website_name}")
    logger.info(f"Export directory: {export_dir}")
    logger.info(f"Content directory: {content_dir}")
    logger.info(f"Output directory: {output_dir}")

    # Verify that export and content directories exist
    if not export_dir.exists():
        logger.error(f"Export directory does not exist: {export_dir}")
        raise FileNotFoundError(f"Export directory does not exist: {export_dir}")

    if not content_dir.exists():
        logger.error(f"Content directory does not exist: {content_dir}")
        raise FileNotFoundError(f"Content directory does not exist: {content_dir}")

    # Get the path to the blog config file
    blog_config_path = Path(enricher_config.get("config_file"))

    # If the config is in YAML format, convert it to JSON
    if blog_config_path.suffix.lower() in [".yaml", ".yml"]:
        logger.info(f"Converting YAML config to JSON: {blog_config_path}")

        # Ensure the file exists
        if not blog_config_path.exists():
            logger.error(f"Blog config file does not exist: {blog_config_path}")
            raise FileNotFoundError(f"Blog config file does not exist: {blog_config_path}")

        # Load YAML and convert to JSON
        with open(blog_config_path, "r") as f:
            blog_config = yaml.safe_load(f)

        # Create a temporary JSON file
        temp_json_path = workspace_dir / "blog_config.json"
        with open(temp_json_path, "w") as f:
            json.dump(blog_config, f, indent=2)

        logger.info(f"Created temporary JSON config: {temp_json_path}")
        config_path = temp_json_path
    else:
        config_path = blog_config_path

    # Find the website_enricher directory
    enricher_script_path = Path("website_enricher") / "enrich-webflow-export.js"

    # Check if the enricher script exists
    if not enricher_script_path.exists():
        script_locations: List[Path] = [
            Path("website_enricher") / "enrich-webflow-export.js",
            Path("../website_enricher") / "enrich-webflow-export.js",
            Path(os.environ["HOME"])
            / "repository/website_blog_generator/website_enricher"
            / "enrich-webflow-export.js",
        ]

        for location in script_locations:
            if location.exists():
                enricher_script_path = location
                break

        if not enricher_script_path.exists():
            logger.error(f"Website enricher script not found at any of: {script_locations}")
            raise FileNotFoundError(
                f"Website enricher script not found at any of: {script_locations}"
            )

    logger.info(f"Using website enricher script: {enricher_script_path}")

    # Build the command to run the website enricher
    cmd: List[str] = [
        "node",
        str(enricher_script_path),
        "--export",
        str(export_dir),
        "--csv",
        str(content_dir),
        "--config",
        str(config_path),
        "--output",
        str(output_dir),
    ]

    logger.info(f"Running website enricher: {' '.join(cmd)}")

    try:
        # Run the command
        process = subprocess.run(cmd, check=True, text=True, capture_output=True)

        # Log output
        if process.stdout:
            logger.debug(f"Website enricher output: {process.stdout}")

        logger.info(f"Successfully enriched website: {website_name}")
        return output_dir

    except subprocess.CalledProcessError as e:
        logger.error(f"Website enrichment failed with code {e.returncode}: {e.stderr}")
        raise RuntimeError(f"Website enrichment failed with code {e.returncode}")

    except Exception as e:
        logger.error(f"Website enrichment failed: {e}")
        raise RuntimeError(f"Website enrichment failed: {e}")


# For development/testing purposes
def simulate_enrichment(config: Dict[str, Any], website_name: str) -> Path:
    """
    Simulate website enrichment for development purposes.

    Args:
        config: The loaded configuration
        website_name: Name of the website to enrich

    Returns:
        Path to the simulated enriched website directory
    """
    logger = logging.getLogger("orchestrator.enricher")

    # Determine the workspace directory
    workspace_name = config["website"]["website"].get("workspace", website_name)
    workspace_dir = Path(config["paths"]["workspaces"]) / workspace_name

    export_dir = workspace_dir / "export"
    content_dir = workspace_dir / "content"
    output_dir = workspace_dir / "output"

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Simulating enrichment for {website_name}")

    # Check if export directory exists
    if not export_dir.exists() or not (export_dir / "index.html").exists():
        logger.warning(f"Export directory does not exist or is empty: {export_dir}")
        # Create a dummy index.html if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        with open(export_dir / "index.html", "w") as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{website_name}</title>
            </head>
            <body>
                <h1>Welcome to {website_name}</h1>
                <p>This is a simulated website export for development purposes.</p>
            </body>
            </html>
            """)

    # Copy files from export to output
    for item in export_dir.glob("*"):
        if item.is_file():
            dest = output_dir / item.name
            with open(item, "rb") as src_file:
                with open(dest, "wb") as dest_file:
                    dest_file.write(src_file.read())

    # Create a blog directory and index page
    blog_dir = output_dir / "blog"
    os.makedirs(blog_dir, exist_ok=True)

    # Create blog index page
    with open(output_dir / "blog.html", "w") as f:
        f.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{website_name} Blog</title>
        </head>
        <body>
            <h1>{website_name} Blog</h1>
            <div class="blog-posts">
                <div class="blog-post">
                    <h2><a href="/blog/sample-blog-post-1.html">Sample Blog Post 1</a></h2>
                    <p>This is a summary of blog post 1 for testing purposes.</p>
                </div>
                <div class="blog-post">
                    <h2><a href="/blog/sample-blog-post-2.html">Sample Blog Post 2</a></h2>
                    <p>This is a summary of blog post 2 for testing purposes.</p>
                </div>
                <div class="blog-post">
                    <h2><a href="/blog/sample-blog-post-3.html">Sample Blog Post 3</a></h2>
                    <p>This is a summary of blog post 3 for testing purposes.</p>
                </div>
            </div>
        </body>
        </html>
        """)

    # Create individual blog post pages
    for i in range(1, 4):
        with open(blog_dir / f"sample-blog-post-{i}.html", "w") as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sample Blog Post {i} - {website_name}</title>
            </head>
            <body>
                <h1>Sample Blog Post {i}</h1>
                <p>By Test Author | 01/05/2023 | 5 min read</p>
                <div class="content">
                    <h2>Sample Content</h2>
                    <p>This is sample content for blog post {i}.</p>
                </div>
                <p><a href="/blog.html">Back to Blog</a></p>
            </body>
            </html>
            """)

    logger.info(f"Created simulated enriched website for {website_name} at {output_dir}")
    return output_dir
