#!/usr/bin/env python3
"""
Website SEO Orchestrator

This script orchestrates the process of generating SEO content for websites and integrating
it with exported websites from Hostinger.

Usage:
    python main.py --website your-site --all
    python main.py --website your-site --export --generate
    python main.py --website your-site --enrich --import_website
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import coloredlogs
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration types
ConfigDict = Dict[str, Any]


def setup_logging(config: ConfigDict) -> logging.Logger:
    """
    Set up logging based on configuration.

    Args:
        config: The loaded configuration dictionary

    Returns:
        Logger instance configured according to settings
    """
    log_level = getattr(logging, config["logging"]["level"])
    log_file = config["logging"]["file"]
    console = config["logging"].get("console", True)

    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Configure logging
    handlers: List[logging.Handler] = []
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    if console:
        handlers.append(logging.StreamHandler(sys.stdout))

    # Basic configuration
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    # Add colored logs for console output
    coloredlogs.install(level=log_level, fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    return logging.getLogger("orchestrator")


def load_config(config_path: Union[str, Path], website_name: Optional[str] = None) -> ConfigDict:
    """
    Load main config and optionally a website-specific config.

    Args:
        config_path: Path to the main configuration file
        website_name: Name of the website to load config for

    Returns:
        Merged configuration dictionary

    Raises:
        FileNotFoundError: If the website config file doesn't exist
    """
    # Load main config
    with open(config_path, "r") as f:
        config: ConfigDict = yaml.safe_load(f)

    if website_name:
        # Load website config
        website_config_path = Path("website_configs") / f"{website_name}.yaml"
        if not website_config_path.exists():
            raise FileNotFoundError(f"Website config not found: {website_config_path}")

        with open(website_config_path, "r") as f:
            website_config = yaml.safe_load(f)

        # Merge website config with main config
        config["website"] = website_config

    # Expand environment variables in config
    config = expand_env_vars(config)

    return config


def expand_env_vars(config: Any) -> Any:
    """
    Recursively expand environment variables in config values.

    Args:
        config: Configuration object (can be dict, list, or primitive value)

    Returns:
        Configuration with environment variables expanded
    """
    if isinstance(config, dict):
        return {k: expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [expand_env_vars(i) for i in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        env_var = config[2:-1]
        return os.environ.get(env_var, config)
    else:
        return config


def ensure_workspace_dirs(config: ConfigDict, website_name: str) -> Path:
    """
    Create necessary workspace directories for a website.

    Args:
        config: The loaded configuration
        website_name: Name of the website

    Returns:
        Path to the workspace directory
    """
    logger = logging.getLogger("orchestrator")

    # Get workspace directory
    workspace_name = config["website"]["website"].get("workspace", website_name)
    workspace_dir = Path(config["paths"]["workspaces"]) / workspace_name

    # Create workspace subdirectories
    for subdir in ["export", "content", "output"]:
        dir_path = workspace_dir / subdir
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"Ensured directory exists: {dir_path}")

    return workspace_dir


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
    from modules.content_generator import generate_content

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


def run_import_website(config: ConfigDict, website_name: str) -> None:
    """
    Run the import step.

    Args:
        config: The loaded configuration
        website_name: Name of the website to import
    """
    logger = logging.getLogger("orchestrator.import")
    logger.info(f"Starting import process for website: {website_name}")

    if config.get("dry_run"):
        logger.info(f"[DRY RUN] Would import website: {website_name}")
        return

    # Import the module only when needed
    from modules.importer import import_website

    import_website(config, website_name)


def run_pipeline(config: ConfigDict, website_name: str, steps: List[str], **kwargs) -> None:
    """
    Run the specified steps of the pipeline.

    Args:
        config: The loaded configuration
        website_name: Name of the website
        steps: List of steps to run (export, generate, enrich, import)

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
            run_export(config, website_name)

        if "generate" in steps:
            run_generate(config, website_name)

        if "enrich" in steps:
            run_enrich(config, website_name, **kwargs)

        if "import" in steps:
            run_import_website(config, website_name)

        logger.info(f"Pipeline completed for website: {website_name}")
    except Exception as e:
        logger.exception(f"Error in pipeline: {e}")
        raise


def main() -> None:
    """
    Main entry point.

    Parses command line arguments, loads configuration, and runs the pipeline.
    """
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description="Website SEO Orchestrator")
    parser.add_argument("--website", required=True, help="Website name (must match a config file)")
    parser.add_argument("--config", default="config.yaml", help="Path to main config file")

    # Steps to run
    parser.add_argument("--export", action="store_true", help="Export website from Hostinger")
    parser.add_argument("--generate", action="store_true", help="Generate SEO content")
    parser.add_argument("--enrich", action="store_true", help="Enrich website with content")
    parser.add_argument(
        "--import", dest="import_website", action="store_true", help="Import website to Hostinger"
    )
    parser.add_argument(
        "--force-hta", action="store_true", help="Force overwrite of .htaccess file"
    )
    parser.add_argument("--all", action="store_true", help="Run all steps")

    # Other options
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual changes)")

    args = parser.parse_args()

    try:
        # Load config
        config = load_config(args.config, args.website)

        # Set verbose mode if requested
        if args.verbose:
            config["logging"]["level"] = "DEBUG"

        # Set up logging
        logger = setup_logging(config)

        # Determine steps to run
        steps: List[str] = []
        if args.export:
            steps.append("export")
        if args.generate:
            steps.append("generate")
        if args.enrich:
            steps.append("enrich")
        if args.import_website:
            steps.append("import")
        if args.all or not steps:  # Default to all if no steps specified
            steps = ["export", "generate", "enrich", "import"]
        kwargs = {
            "force-hta": args.force_hta,
        }

        logger.info(f"Running steps: {', '.join(steps)}")

        # Set dry run flag
        config["dry_run"] = args.dry_run
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")

        # Run pipeline
        run_pipeline(config, args.website, steps, **kwargs)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
