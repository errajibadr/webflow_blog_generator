"""
Pipeline runner for Website SEO Orchestrator.

This module contains functions to run individual steps of the pipeline and the complete pipeline.
"""

import asyncio
import logging
from typing import Any, Dict, List

from modules.config import ConfigDict, ensure_workspace_dirs


def run_export(config: ConfigDict, website_name: str) -> None:
    """
    Run the export step.

    Args:
        config: The loaded configuration
        website_name: Name of the website to export
    """
    logger = logging.getLogger("orchestrator.export")
    logger.info(f"Starting export process for website: {website_name}")

    if config.get("dry_run"):
        logger.info(f"[DRY RUN] Would export website: {website_name}")
        return

    # Import the module only when needed
    from modules.exporter import export_website

    export_website(config, website_name)


# Async version of run_generate
async def run_generate_async(config: ConfigDict, website_name: str) -> None:
    """
    Run the content generation step asynchronously.

    Args:
        config: The loaded configuration
        website_name: Name of the website to generate content for
    """
    logger = logging.getLogger("orchestrator.generate")
    logger.info(f"Starting async content generation for website: {website_name}")

    if config.get("dry_run"):
        logger.info(f"[DRY RUN] Would generate content for website: {website_name}")
        return

    # Import the module only when needed
    from modules.content_generator.content_generator import generate_content_async

    await generate_content_async(config, website_name)


def run_generate(config: ConfigDict, website_name: str) -> None:
    """
    Run the content generation step.

    Args:
        config: The loaded configuration
        website_name: Name of the website to generate content for
    """
    logger = logging.getLogger("orchestrator.generate")
    logger.info(f"Starting content generation for website: {website_name}")

    if config.get("dry_run"):
        logger.info(f"[DRY RUN] Would generate content for website: {website_name}")
        return

    # Import the module only when needed
    from modules.content_generator.content_generator import generate_content

    generate_content(config, website_name)


def run_enrich(config: ConfigDict, website_name: str, **kwargs) -> None:
    """
    Run the website enrichment step.

    Args:
        config: The loaded configuration
        website_name: Name of the website to enrich
    """
    logger = logging.getLogger("orchestrator.enrich")
    logger.info(f"Starting website enrichment for website: {website_name}")

    if config.get("dry_run"):
        logger.info(f"[DRY RUN] Would enrich website: {website_name}")
        return

    # Import the module only when needed
    from modules.enricher import enrich_website

    enrich_website(config, website_name, **kwargs)


def run_upload_website(config: ConfigDict, website_name: str, purge_remote: bool = False) -> None:
    """
    Run the import step.

    Args:
        config: The loaded configuration
        website_name: Name of the website to import
        purge_remote: If True, purge all files in the remote directory before import
    """
    logger = logging.getLogger("orchestrator.import")
    logger.info(f"Starting import process for website: {website_name}")

    if config.get("dry_run"):
        logger.info(f"[DRY RUN] Would import website: {website_name}")
        return

    # Import the module only when needed
    from modules.importer import import_website

    import_website(config, website_name, purge_remote=purge_remote)


# Async version of run_pipeline
async def run_pipeline_async(
    config: ConfigDict, website_name: str, steps: List[str], purge_remote: bool = False, **kwargs
) -> None:
    """
    Run the specified steps of the pipeline asynchronously.

    Args:
        config: The loaded configuration
        website_name: Name of the website
        steps: List of steps to run (export, generate, enrich, import)
        purge_remote: If True, purge all files in the remote directory before import

    Raises:
        Exception: If any step fails
    """
    logger = logging.getLogger("orchestrator")

    # Create necessary directories
    workspace_dir = ensure_workspace_dirs(config, website_name)
    logger.info(f"Using workspace directory: {workspace_dir}")

    # Run requested steps
    try:
        if "export" in steps:
            # Still synchronous
            run_export(config, website_name)

        if "generate" in steps:
            # Use async generate
            await run_generate_async(config, website_name)

        if "enrich" in steps:
            # Still synchronous
            run_enrich(config, website_name, **kwargs)

        if "upload" in steps:
            # Still synchronous
            run_upload_website(config, website_name, purge_remote=purge_remote)

        logger.info(f"Pipeline completed for website: {website_name}")
    except Exception as e:
        logger.exception(f"Error in pipeline: {e}")
        raise


def run_pipeline(
    config: ConfigDict, website_name: str, steps: List[str], purge_remote: bool = False, **kwargs
) -> None:
    """
    Run the specified steps of the pipeline.

    Args:
        config: The loaded configuration
        website_name: Name of the website
        steps: List of steps to run (export, generate, enrich, import)
        purge_remote: If True, purge all files in the remote directory before import

    Raises:
        Exception: If any step fails
    """
    logger = logging.getLogger("orchestrator")

    # Check if we should use async pipeline
    use_async = config.get("use_async", True)

    if use_async and "generate" in steps:
        # Only use async version if we're doing content generation
        asyncio.run(run_pipeline_async(config, website_name, steps, purge_remote, **kwargs))
        return

    # Create necessary directories
    workspace_dir = ensure_workspace_dirs(config, website_name)
    logger.info(f"Using workspace directory: {workspace_dir}")

    # Run requested steps
    try:
        if "export" in steps:
            run_export(config, website_name)

        if "generate" in steps:
            run_generate(config, website_name)

        if "enrich" in steps:
            run_enrich(config, website_name, **kwargs)

        if "upload" in steps:
            run_upload_website(config, website_name, purge_remote=purge_remote)

        logger.info(f"Pipeline completed for website: {website_name}")
    except Exception as e:
        logger.exception(f"Error in pipeline: {e}")
        raise
