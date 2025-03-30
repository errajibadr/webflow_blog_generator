#!/usr/bin/env python3
"""
Website Importer Module

This module handles importing websites to Hostinger through either:
1. Hostinger API (if available)
2. FTP import (preferred method)
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

import ftputil
import ftputil.error


def import_website(config: Dict[str, Any], website_name: str) -> bool:
    """
    Import a website to Hostinger.

    Args:
        config: The loaded configuration
        website_name: Name of the website to import

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger("orchestrator.importer")
    website_config = config["website"]

    # Determine the workspace directory
    workspace_name = website_config["website"].get("workspace", website_name)
    workspace_dir = Path(config["paths"]["workspaces"]) / workspace_name
    output_dir = workspace_dir / "output"

    # Verify that output directory exists
    if not output_dir.exists():
        logger.error(f"Output directory does not exist: {output_dir}")
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    logger.info(f"Importing website: {website_name} from {output_dir}")

    try:
        # Get import method from config or use default priority order
        import_method = website_config.get("import", {}).get("method", "ftp")

        if import_method == "ftp":
            success = _import_via_ftp(config, website_name, output_dir)
        elif import_method == "simulate":
            success = simulate_import(config, website_name)
        else:
            logger.error(f"Unknown import method: {import_method}")
            return False

        if success:
            logger.info(f"Successfully imported website: {website_name}")
            return True
        else:
            logger.error(f"Import failed for website: {website_name}")
            return False

    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise RuntimeError(f"Failed to import website: {e}")


def _import_via_ftp(config: Dict[str, Any], website_name: str, output_dir: Path) -> bool:
    """
    Import a website to Hostinger using FTP.

    Args:
        config: The loaded configuration
        website_name: Name of the website to import
        output_dir: Directory with files to import

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger("orchestrator.importer.ftp")
    website_config = config["website"]

    # Get FTP configuration
    hostinger_config = website_config.get("hostinger", {})
    ftp_host = hostinger_config.get("host", f"ftp.{website_config['website'].get('domain', '')}")
    ftp_user = hostinger_config["username"]
    ftp_password = hostinger_config["password"]
    remote_dir = hostinger_config.get("remote_dir", "/")

    logger.info(f"Starting FTP import to {ftp_host}{remote_dir}")

    try:
        # Connect to FTP server
        with ftputil.FTPHost(ftp_host, ftp_user, ftp_password) as ftp_host:
            # Check if the specified remote_dir exists, create if not
            if not ftp_host.path.exists(remote_dir):
                logger.info(f"Creating remote directory {remote_dir}")
                ftp_host.makedirs(remote_dir)

            # Initialize counters for statistics
            file_count = 0
            dir_count = 0
            skipped_count = 0

            # Walk the local directory structure
            for dirpath, dirnames, filenames in os.walk(output_dir):
                # Create the corresponding remote path
                rel_path = os.path.relpath(dirpath, output_dir)
                remote_path = os.path.join(remote_dir, rel_path) if rel_path != "." else remote_dir

                # Ensure the remote directory exists
                if rel_path != "." and not ftp_host.path.exists(remote_path):
                    logger.debug(f"Creating remote directory: {remote_path}")
                    ftp_host.makedirs(remote_path)
                    dir_count += 1
                elif rel_path != ".":
                    dir_count += 1

                if dir_count <= 5:  # Only show first 5 directories in debug mode
                    logger.debug(f"Processing directory: {dirpath}")

                # Upload each file
                for filename in filenames:
                    local_file = os.path.join(dirpath, filename)
                    remote_file = os.path.join(remote_path, filename)

                    # Check if file exists and is older (need to upload)
                    update_file = True
                    if ftp_host.path.exists(remote_file):
                        local_time = os.path.getmtime(local_file)
                        try:
                            remote_time = ftp_host.path.getmtime(remote_file)
                            if remote_time >= local_time:
                                if skipped_count < 5:  # Limit log entries
                                    logger.debug(f"Skipping (up to date): {remote_file}")
                                skipped_count += 1
                                update_file = False
                        except ftputil.error.FTPOSError:
                            # If we can't get the mtime, we should upload
                            logger.debug(f"Could not get mtime for {remote_file}, will upload")

                    if update_file:
                        if file_count < 10:  # Only show first 10 files in debug mode
                            logger.debug(f"Uploading: {local_file} -> {remote_file}")
                        file_count += 1
                        ftp_host.upload(local_file, remote_file)

            # Log summary
            logger.info("FTP import completed successfully:")
            logger.info(f"  Directories processed: {dir_count}")
            logger.info(f"  Files uploaded: {file_count}")
            logger.info(f"  Files skipped (up to date): {skipped_count}")

            return True

    except Exception as e:
        logger.error(f"FTP import failed: {e}")
        return False


# For development/testing purposes
def simulate_import(config: Dict[str, Any], website_name: str) -> bool:
    """
    Simulate a website import for development purposes.

    Args:
        config: The loaded configuration
        website_name: Name of the website to import

    Returns:
        True if successful
    """
    logger = logging.getLogger("orchestrator.importer")

    # Determine the workspace directory
    workspace_name = config["website"]["website"].get("workspace", website_name)
    workspace_dir = Path(config["paths"]["workspaces"]) / workspace_name
    output_dir = workspace_dir / "output"

    # Verify that output directory exists
    if not output_dir.exists():
        logger.warning(f"Output directory does not exist: {output_dir}")
        return False

    logger.info(f"Simulating import for website: {website_name} from {output_dir}")

    # Just wait a bit to simulate the import process
    logger.info("Uploading website files...")
    time.sleep(2)

    logger.info("Configuring website on Hostinger...")
    time.sleep(1)

    logger.info(f"Completed simulated import for website: {website_name}")
    return True
