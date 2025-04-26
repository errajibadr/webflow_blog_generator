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
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import coloredlogs
import yaml
from dotenv import load_dotenv

# Import credential manager
from modules.credentials import (
    get_credential,
    list_available_backends,
    manage_credentials,
    set_backend,
    store_credential,
)

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


def expand_env_vars(value: Any) -> Any:
    """Recursively expand environment variables and credential references in the given value.

    Supports the formats:
    - ${ENV_VAR}
    - ${env:ENV_VAR}
    - ${cred:WEBSITE_CRED_TYPE}

    Args:
        value: The value to process (can be dict, list, or string)

    Returns:
        Any: The processed value with environment variables expanded
    """
    # Handle different value types
    if isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(v) for v in value]
    elif isinstance(value, str):
        # First try our specific formats
        def replace_var(match):
            full_match = match.group(0)
            var_type = match.group(1) if match.group(1) else "env"
            var_name = match.group(2)

            if var_type == "env":
                # Standard environment variable
                return os.environ.get(var_name, "")
            elif var_type == "cred":
                # Credential reference format: ${cred:WEBSITE_CRED_TYPE}
                parts = var_name.split("_", 1)
                if len(parts) != 2:
                    logging.warning(f"Invalid credential reference format: {full_match}")
                    return ""

                website, cred_type = parts
                try:
                    return get_credential(website, cred_type)
                except Exception as e:
                    logging.error(f"Error retrieving credential: {e}")
                    return ""

            return os.environ.get(var_name, "")

        # Match ${var}, ${env:var} or ${cred:var}
        pattern = r"\${(?:(env|cred):)?([A-Za-z0-9_]+)}"
        value = re.sub(pattern, replace_var, value)

        # Then try standard format as fallback
        return os.path.expandvars(value)
    else:
        return value


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


def run_import_website(config: ConfigDict, website_name: str, purge_remote: bool = False) -> None:
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
            run_import_website(config, website_name, purge_remote=purge_remote)

        logger.info(f"Pipeline completed for website: {website_name}")
    except Exception as e:
        logger.exception(f"Error in pipeline: {e}")
        raise


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Website SEO Orchestrator")
    parser.add_argument("--website", help="Website name (must match a config file)")
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
    parser.add_argument(
        "--purge-remote",
        action="store_true",
        help="Purge all files in the remote directory before import (DANGEROUS)",
    )

    credential_group = parser.add_argument_group("Credential Management")
    credential_group.add_argument(
        "--credential",
        choices=["add", "remove", "list", "test", "configure"],
        help="Credential management action",
    )

    credential_group.add_argument(
        "--website-cred", help="Website name for credential action", dest="cred_website"
    )

    credential_group.add_argument(
        "--type", help="Type of credential (e.g., FTP_USERNAME, FTP_PASSWORD)"
    )

    credential_group.add_argument("--value", help="Value for the credential")

    credential_group.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for credential value instead of command line",
    )

    credential_group.add_argument(
        "--force", action="store_true", help="Skip confirmation for dangerous operations"
    )

    credential_group.add_argument(
        "--show-values",
        action="store_true",
        help="Show credential values when listing (requires confirmation)",
    )

    # Backend management
    backend_group = parser.add_argument_group("Credential Backend Management")
    backend_group.add_argument(
        "--credential-backend",
        help='Select credential backend (file, env, vault) or "list" to show available backends',
    )

    backend_group.add_argument(
        "--backend-config",
        action="append",
        help="Backend configuration in KEY=VALUE format (can specify multiple times)",
    )

    return parser.parse_args()


def main() -> None:
    """
    Run the main orchestration pipeline.
    """
    # Parse command line arguments
    args = parse_args()

    # Handle credential backend selection if the module is available
    if args.credential_backend:
        if args.credential_backend == "list":
            backends = list_available_backends()
            print("Available credential backends:")
            for backend in backends:
                print(
                    f"- {backend['name']}{' (current)' if backend['current'] else ''}: {backend['description']}"
                )
            sys.exit(0)
        else:
            # Parse backend config if provided
            backend_config = {}
            if args.backend_config:
                for config_item in args.backend_config:
                    if "=" in config_item:
                        key, value = config_item.split("=", 1)
                        backend_config[key] = value
                    else:
                        print(
                            f"Error: Invalid backend config format: {config_item}. Use KEY=VALUE format."
                        )
                        sys.exit(1)

            # Set the backend
            try:
                set_backend(args.credential_backend, **backend_config)
                print(f"Credential backend set to: {args.credential_backend}")
                sys.exit(0)
            except Exception as e:
                print(f"Error setting credential backend: {e}")
                sys.exit(1)

    # Handle credential management commands
    if args.credential:
        result = manage_credentials(
            action=args.credential,
            website=args.cred_website,
            cred_type=args.type,
            value=args.value,
            interactive=args.interactive,
            force=args.force,
            show_values=args.show_values,
            host=args.website,  # Use website as host if needed
        )

        print(result)
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
    if args.verbose:
        coloredlogs.install(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)

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
        steps = []
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
