"""
Logging configuration for Website SEO Orchestrator.
"""

import logging
import os
import sys
from typing import List

import coloredlogs

from .loader import ConfigDict


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


def set_verbosity(logger: logging.Logger, verbose: bool = False) -> None:
    """
    Set the verbosity level of logging.

    Args:
        logger: The logger instance to modify
        verbose: Whether to enable verbose logging
    """
    if verbose:
        coloredlogs.install(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
