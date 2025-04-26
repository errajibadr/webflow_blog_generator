#!/usr/bin/env python3
"""
Website SEO Orchestrator

This script orchestrates the process of generating SEO content for websites and integrating
it with exported websites from Hostinger.

Usage:
    python main.py --website your-site --all
    python main.py --website your-site --export --generate
    python main.py --website your-site --enrich --upload
"""

import sys

from modules.cli import (
    get_steps_from_args,
    handle_credential_backend,
    handle_credential_management,
    parse_args,
)

# Import modules
from modules.config import load_config, set_verbosity, setup_logging
from modules.pipeline import run_pipeline


def main() -> None:
    """
    Run the main orchestration pipeline.
    """
    # Parse command line arguments
    args = parse_args()

    # Handle credential backend selection
    if handle_credential_backend(args):
        sys.exit(0)

    # Handle credential management commands
    if handle_credential_management(args):
        sys.exit(0)

    # Load config
    try:
        config = load_config(args.config, args.website)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Set up logging
    logger = setup_logging(config)

    # Set verbosity
    set_verbosity(logger, args.verbose)

    # Handle dry run flag
    if args.dry_run:
        config["dry_run"] = True
        logger.info("Running in dry run mode - no changes will be made")

    try:
        # Validate website
        if not args.website:
            logger.error("Website name is required. Use --website WEBSITE")
            sys.exit(1)

        # Determine which steps to run
        steps = get_steps_from_args(args)

        # Run the pipeline
        run_pipeline(
            config, args.website, steps, purge_remote=args.purge_remote, force_hta=args.force_hta
        )

    except Exception as e:
        logger.exception(f"Error in pipeline: {e}")
        sys.exit(1)

    logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    main()
