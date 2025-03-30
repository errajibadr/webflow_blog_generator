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
from typing import Any, Dict, List, Tuple

import yaml

logger = logging.getLogger("orchestrator.enricher")


def enrich_website(config: Dict[str, Any], website_name: str) -> Path:
    """
    Enrich website with content using the website enricher module.

    Args:
        config: The loaded configuration
        website_name: Name of the website to enrich

    Returns:
        Path to the enriched website directory
    """

    website_config = config["website"]

    # Setup directories and check they exist
    dirs = setup_directories(config, website_name)
    export_dir, content_dir, output_dir = dirs

    # Prepare blog config for enricher
    config_path = prepare_blog_config(website_config, dirs)

    # Find enricher script
    script_path = find_enricher_script()

    # Run enricher
    return run_enricher(script_path, export_dir, content_dir, output_dir, config_path, website_name)


def setup_directories(config: Dict[str, Any], website_name: str) -> Tuple[Path, Path, Path]:
    """
    Set up the necessary directories for the enrichment process.

    Args:
        config: The loaded configuration
        website_name: Name of the website

    Returns:
        Tuple of (export_dir, content_dir, output_dir)

    Raises:
        FileNotFoundError: If export or content directories don't exist
    """
    logger = logging.getLogger("orchestrator.enricher")
    website_config = config["website"]

    # Determine the workspace directory
    workspace_name = website_config["website"].get("workspace", website_name)
    workspace_dir = Path(config["paths"]["workspaces"]) / workspace_name

    # Get paths to directories
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

    return export_dir, content_dir, output_dir


def prepare_blog_config(website_config: Dict[str, Any], dirs: Tuple[Path, Path, Path]) -> Path:
    """
    Prepare the blog configuration for the enricher.

    Args:
        website_config: The website configuration
        dirs: Tuple of (export_dir, content_dir, output_dir)

    Returns:
        Path to the blog config file to use

    Raises:
        FileNotFoundError: If external blog config file is not found
    """
    _, _, output_dir = dirs
    workspace_dir = output_dir.parent
    enricher_config = website_config.get("website_enricher", {})

    # Create a JSON config file for the enricher
    temp_json_path = workspace_dir / "blog_config.json"

    # Check if we have an inline blog_config in the website config
    if "blog_config" in website_config:
        return _handle_inline_config(website_config, temp_json_path)
    else:
        return _handle_external_config(enricher_config, temp_json_path)


def _handle_inline_config(website_config: Dict[str, Any], temp_json_path: Path) -> Path:
    """Handle inline blog_config from the website configuration."""

    logger.info("Using inline blog_config from website configuration")
    blog_config = website_config["blog_config"]

    # Write the config to a temporary JSON file
    with open(temp_json_path, "w") as f:
        json.dump(blog_config, f, indent=2)

    logger.info(f"Created temporary JSON config from inline blog_config: {temp_json_path}")
    return temp_json_path


def _handle_external_config(enricher_config: Dict[str, Any], temp_json_path: Path) -> Path:
    """Handle external blog config file specified in enricher_config."""

    # Get the path to the external blog config file
    blog_config_path = Path(enricher_config.get("config_file", ""))

    if not blog_config_path or not blog_config_path.exists():
        logger.error(f"Blog config file not found: {blog_config_path}")
        raise FileNotFoundError(f"Blog config file not found: {blog_config_path}")

    logger.info(f"Using external blog config file: {blog_config_path}")

    # If the config is in YAML format, convert it to JSON
    if blog_config_path.suffix.lower() in [".yaml", ".yml"]:
        logger.info(f"Converting YAML config to JSON: {blog_config_path}")

        # Load YAML and convert to JSON
        with open(blog_config_path, "r") as f:
            blog_config = yaml.safe_load(f)

        # Create a temporary JSON file
        with open(temp_json_path, "w") as f:
            json.dump(blog_config, f, indent=2)

        logger.info(f"Created temporary JSON config: {temp_json_path}")
        return temp_json_path
    else:
        return blog_config_path


def find_enricher_script() -> Path:
    """
    Find the website enricher script.

    Returns:
        Path to the enricher script

    Raises:
        FileNotFoundError: If the enricher script cannot be found
    """
    logger = logging.getLogger("orchestrator.enricher")

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
    return enricher_script_path


def run_enricher(
    script_path: Path,
    export_dir: Path,
    content_dir: Path,
    output_dir: Path,
    config_path: Path,
    website_name: str,
) -> Path:
    """
    Run the website enricher script.

    Args:
        script_path: Path to the enricher script
        export_dir: Path to the export directory
        content_dir: Path to the content directory
        output_dir: Path to the output directory
        config_path: Path to the blog config file
        website_name: Name of the website

    Returns:
        Path to the enriched website directory

    Raises:
        RuntimeError: If the enricher script fails
    """

    # Build the command to run the website enricher
    cmd: List[str] = [
        "node",
        str(script_path),
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
        _create_dummy_export(export_dir, website_name)

    # Copy files from export to output
    _copy_files_to_output(export_dir, output_dir)

    # Create blog files
    _create_sample_blog_files(output_dir, website_name)

    logger.info(f"Created simulated enriched website for {website_name} at {output_dir}")
    return output_dir


def _create_dummy_export(export_dir: Path, website_name: str) -> None:
    """Create a dummy export for simulation purposes."""
    logger = logging.getLogger("orchestrator.enricher")

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


def _copy_files_to_output(export_dir: Path, output_dir: Path) -> None:
    """Copy files from export directory to output directory."""
    # Copy files from export to output
    for item in export_dir.glob("*"):
        if item.is_file():
            dest = output_dir / item.name
            with open(item, "rb") as src_file:
                with open(dest, "wb") as dest_file:
                    dest_file.write(src_file.read())


def _create_sample_blog_files(output_dir: Path, website_name: str) -> None:
    """Create sample blog files for simulation purposes."""
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
