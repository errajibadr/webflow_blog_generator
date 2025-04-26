#!/usr/bin/env python3
"""
Website Importer Module

This module handles importing websites to Hostinger through either:
1. Hostinger API (if available)
2. FTP import (preferred method)
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.ftp_importer import FTPImporter

logger = logging.getLogger(__name__)


def import_website(config: Dict[str, Any], website_name: str, purge_remote: bool = False) -> bool:
    """
    Import a website to Hostinger.

    Args:
        config: The loaded configuration
        website_name: Name of the website to import
        purge_remote: If True, purge all files in the remote directory before import

    Returns:
        True if successful, False otherwise
    """
    # Use the new FTPImporter class for improved performance and reliability
    importer = FTPImporter(config)
    return importer.import_website(website_name, purge_remote=purge_remote)


def _purge_remote_dir(ftp_host, remote_dir):
    """
    Recursively delete all files and directories in remote_dir on the FTP server.
    """
    logger = logging.getLogger("orchestrator.importer.ftp")
    try:
        for item in ftp_host.listdir(remote_dir):
            item_path = ftp_host.path.join(remote_dir, item)
            if ftp_host.path.isdir(item_path):
                logger.info(f"Recursively deleting remote directory: {item_path}")
                _purge_remote_dir(ftp_host, item_path)
                ftp_host.rmdir(item_path)
                logger.info(f"Deleted remote directory: {item_path}")
            else:
                ftp_host.remove(item_path)

    except Exception as e:
        logger.error(f"Error purging remote directory {remote_dir}: {e}")
        raise


# For development/testing purposes
def simulate_import(
    config: Dict[str, Any], website_name: str, source_dirs: Optional[List[Path]] = None
) -> bool:
    """
    Simulate a website import for development purposes.

    Args:
        config: The loaded configuration
        website_name: Name of the website to import
        source_dirs: List of directories with files to import (optional)

    Returns:
        True if successful
    """
    logger = logging.getLogger("orchestrator.importer")

    # Determine the workspace directory if source_dirs not provided
    if source_dirs is None:
        workspace_name = config["website"]["website"].get("workspace", website_name)
        workspace_dir = Path(config["paths"]["workspaces"]) / workspace_name
        output_dir = workspace_dir / "output"

        # Verify that output directory exists
        if not output_dir.exists():
            logger.warning(f"Output directory does not exist: {output_dir}")
            return False

        source_dirs = [output_dir]

    logger.info(
        f"Simulating import for website: {website_name} from {', '.join(str(d) for d in source_dirs)}"
    )

    # Just wait a bit to simulate the import process
    logger.info("Uploading website files...")
    time.sleep(2)

    logger.info("Configuring website on Hostinger...")
    time.sleep(1)

    logger.info(f"Completed simulated import for website: {website_name}")
    return True
