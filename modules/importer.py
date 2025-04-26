#!/usr/bin/env python3
"""
Website Importer Module

This module handles importing websites to Hostinger through either:
1. Hostinger API (if available)
2. FTP import (preferred method)
"""

from __future__ import annotations

import ftplib
import logging
import os
import time
from ftplib import FTP
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import ftputil
import ftputil.error

# Import credential manager (with fallback)
try:
    from modules.credentials import get_credential

    CRED_MANAGER_AVAILABLE = True
except ImportError:
    CRED_MANAGER_AVAILABLE = False

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
    logger.info(f"Importing website {website_name}...")

    # Check if in dry run mode
    if config.get("dry_run"):
        logger.info(f"DRY RUN: Would import website {website_name}")
        return True

    # Get import source directory from config
    workspace = config["website"]["website"].get("workspace", website_name)
    output_dir = Path(config["paths"]["workspaces"]) / workspace / "output"

    if not output_dir.exists():
        logger.error(f"Output directory does not exist: {output_dir}")
        return False

    # Get FTP settings from config
    website_config = config["website"]
    hostinger_config = website_config.get("hostinger", {})
    remote_dir = hostinger_config.get("remote_dir", "/")

    # Connect to FTP using credential manager or fallback to config
    try:
        try:
            # Get credentials from credential manager
            username = get_credential(website_name, "FTP_USERNAME")
            password = get_credential(website_name, "FTP_PASSWORD")
            logger.debug(f"Using credentials from credential manager for {website_name}")

        except Exception as e:
            # Fall back to config if credential manager fails
            logger.debug(f"Credential manager failed, falling back to config: {e}")
            username = hostinger_config.get("username")
            password = hostinger_config.get("password")

        # Get FTP host
        ftp_host = hostinger_config.get(
            "host", f"ftp.{website_config['website'].get('domain', '')}"
        )

        if not all([ftp_host, username, password]):
            logger.error(
                "Missing FTP credentials. Please check your configuration or use the credential manager."
            )
            return False

        # TODO: Update this to use ftputil instead of raw FTP
        import ftputil

        # Connect to FTP server
        with ftputil.FTPHost(ftp_host, username, password, timeout=30) as ftp_host:
            # Check if remote directory exists
            if not ftp_host.path.exists(remote_dir):
                logger.error(f"Remote directory does not exist: {remote_dir}")
                return False

            # Purge remote directory if requested
            if purge_remote:
                logger.warning(f"Purging remote directory: {remote_dir}")
                # Recursively delete all files and directories
                for item in ftp_host.listdir(remote_dir):
                    remote_path = ftp_host.path.join(remote_dir, item)
                    if ftp_host.path.isdir(remote_path):
                        ftp_host.rmtree(remote_path)
                    else:
                        ftp_host.remove(remote_path)

            # Upload files
            logger.info(f"Starting upload to {remote_dir}...")

            def _upload_directory(local_path, remote_path):
                """Upload a directory recursively."""
                # Ensure remote directory exists
                if not ftp_host.path.exists(remote_path):
                    ftp_host.mkdir(remote_path)

                # Upload all files and directories
                for item in os.listdir(local_path):
                    local_item = os.path.join(local_path, item)
                    remote_item = ftp_host.path.join(remote_path, item)

                    # Upload directory recursively
                    if os.path.isdir(local_item):
                        logger.debug(f"Processing directory: {local_item}")
                        _upload_directory(local_item, remote_item)
                    # Upload file
                    else:
                        logger.debug(f"Uploading: {local_item}")
                        ftp_host.upload(local_item, remote_item)

            # Start recursive upload
            _upload_directory(output_dir, remote_dir)
            logger.info(f"Website content imported to {remote_dir}")
            return True

    except ftplib.all_errors as e:
        logger.error(f"FTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error importing website: {e}")
        return False


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


def _import_via_ftp(
    config: Dict[str, Any], source_dirs: List[Tuple[Path, bool]], purge_remote: bool = False
) -> bool:
    """
    Import a website to Hostinger using FTP.

    Args:
        config: The loaded configuration
        website_name: Name of the website to import
        source_dirs: List of tuples containing (directory_path, preserve_parent_dir_flag)
                    When preserve_parent_dir_flag is True, the parent directory name will be
                    preserved in the remote path
        purge_remote: If True, purge all files in the remote directory before import

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
        # Configure FTP connection with UTF-8 encoding and binary mode
        with ftputil.FTPHost(
            ftp_host,
            ftp_user,
            ftp_password,
            timeout=20,
            encoding="latin1",  # Use latin1 for better compatibility with special characters
        ) as ftp_host:
            # Set binary mode for the FTP session
            ftp_host._session.voidcmd("TYPE I")

            # Check if the specified remote_dir exists, create if not
            if not ftp_host.path.exists(remote_dir):
                logger.info(f"Creating remote directory {remote_dir}")
                ftp_host.makedirs(remote_dir)
            elif purge_remote:
                logger.warning(f"Purging all contents of remote directory: {remote_dir}")
                _purge_remote_dir(ftp_host, remote_dir)
                logger.info(f"Purged all contents of remote directory: {remote_dir}")

            # Initialize counters for statistics
            file_count = 0
            dir_count = 0
            skipped_count = 0

            # Process each source directory
            for source_dir, preserve_parent in source_dirs:
                source_name = source_dir.name if preserve_parent else ""
                logger.info(
                    f"Processing source directory: {source_dir}{' (preserving directory name)' if preserve_parent else ''}"
                )

                # Walk the local directory structure
                for dirpath, dirnames, filenames in os.walk(source_dir):
                    logger.info(f"Processing directory: {dirpath}")
                    # Create the corresponding remote path
                    rel_path = os.path.relpath(dirpath, source_dir)

                    # If we're preserving the parent directory name and this is not the root
                    # of the source directory, include it in the path
                    if preserve_parent:
                        if rel_path == ".":
                            # For the root of source_dir, use just the directory name
                            remote_path = os.path.join(remote_dir, source_name)
                        else:
                            # For subdirectories, include both source_name and relative path
                            remote_path = os.path.join(remote_dir, source_name, rel_path)
                    else:
                        # Standard behavior without preserving parent
                        remote_path = (
                            os.path.join(remote_dir, rel_path) if rel_path != "." else remote_dir
                        )

                    # Ensure the remote directory exists
                    try:
                        if not ftp_host.path.exists(remote_path):
                            logger.debug(f"Creating remote directory: {remote_path}")
                            ftp_host.makedirs(remote_path)
                            dir_count += 1
                        elif remote_path != remote_dir:  # Don't count the root remote dir
                            dir_count += 1
                    except UnicodeEncodeError:
                        logger.error(f"Encoding error with directory name: {remote_path}")
                        continue

                    if dir_count <= 5:  # Only show first 5 directories in debug mode
                        logger.debug(f"Processing directory: {dirpath} -> {remote_path}")

                    # Upload each file
                    for filename in filenames:
                        try:
                            local_file = os.path.join(dirpath, filename)
                            remote_file = os.path.join(remote_path, filename)
                            temp_remote_file = os.path.join(remote_path, f".in.{filename}")

                            # Clean up temp file if it exists before upload
                            if ftp_host.path.exists(temp_remote_file):
                                try:
                                    logger.warning(
                                        f"Removing leftover temp file before upload: {temp_remote_file}"
                                    )
                                    ftp_host.remove(temp_remote_file)
                                except Exception as cleanup_error:
                                    logger.error(
                                        f"Failed to remove temp file {temp_remote_file}: {cleanup_error}"
                                    )
                                    # Continue anyway, as upload will fail if not removed

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
                                    logger.debug(
                                        f"Could not get mtime for {remote_file}, will upload"
                                    )

                            if update_file:
                                if file_count < 10:  # Only show first 10 files in debug mode
                                    logger.debug(f"Uploading: {local_file} -> {remote_file}")
                                file_count += 1

                                # Custom upload implementation to ensure binary mode
                                try:
                                    with open(local_file, "rb") as local_fp:
                                        # Reset binary mode before each transfer
                                        ftp_host._session.voidcmd("TYPE I")
                                        # Use lower level FTP commands for more control
                                        ftp_host._session.storbinary(
                                            f"STOR {remote_file}", local_fp
                                        )
                                except Exception as upload_error:
                                    logger.error(
                                        f"Error during binary upload of {filename}: {upload_error}"
                                    )
                                    continue

                        except UnicodeEncodeError:
                            logger.error(f"Encoding error with file: {filename}")
                            continue
                        except Exception as e:
                            logger.error(f"Error uploading file {filename}: {e}")
                            continue

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


def _connect_ftp(config: Dict[str, Any], website_name: str) -> Optional[FTP]:
    """Connect to FTP server using credentials from config or credential manager.

    Args:
        config: Configuration dictionary
        website_name: Name of the website

    Returns:
        FTP connection object or None if connection fails
    """
    # Get FTP settings from config
    try:
        website_config = config["website"]
        hostinger_config = website_config.get("hostinger", {})
        ftp_host = hostinger_config.get(
            "host", f"ftp.{website_config['website'].get('domain', '')}"
        )

        # First try to get credentials from credential manager
        if CRED_MANAGER_AVAILABLE:
            try:
                username = get_credential(website_name, "FTP_USERNAME")
                password = get_credential(website_name, "FTP_PASSWORD")
                logger.debug(f"Using credentials from credential manager for {website_name}")
            except Exception as e:
                # Fall back to config if credential manager fails
                logger.debug(f"Credential manager failed, falling back to config: {e}")
                username = hostinger_config.get("username")
                password = hostinger_config.get("password")
        else:
            # Use credentials from config if credential manager is not available
            username = hostinger_config.get("username")
            password = hostinger_config.get("password")

        if not all([ftp_host, username, password]):
            logger.error(
                "Missing FTP credentials. Please check your configuration or use the credential manager."
            )
            return None

        # Connect to FTP server
        ftp = FTP()
        ftp.connect(ftp_host)
        ftp.login(username, password)
        logger.info(f"Connected to FTP server: {ftp_host}")
        return ftp

    except ftplib.all_errors as e:
        logger.error(f"FTP connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error connecting to FTP: {e}")
        return None
