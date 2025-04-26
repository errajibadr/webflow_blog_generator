#!/usr/bin/env python3
"""
Website Exporter Module

This module handles exporting websites from Hostinger, using one of these methods:
1. Hostinger API (if available)
2. FTP export (preferred method)
"""

from __future__ import annotations

import ftplib
import logging
import os
import shutil
from ftplib import FTP
from pathlib import Path
from typing import Any, Dict, Optional

import ftputil

# Import credential manager (with fallback)
try:
    import modules.cred_manager as cred_manager

    CRED_MANAGER_AVAILABLE = True
except ImportError:
    CRED_MANAGER_AVAILABLE = False

logger = logging.getLogger(__name__)


def _simulate_export(config: Dict[str, Any], website_name: str) -> bool:
    """Simulate exporting website content for dry runs.

    Args:
        config: Config dictionary
        website_name: Name of the website

    Returns:
        bool: Always returns True
    """
    logger = logging.getLogger("exporter")

    # Get export directory from config
    export_dir = Path(config["paths"]["workspaces"]) / website_name / "export"
    logger.debug(f"Export directory: {export_dir}")

    # Ensure export directory exists
    export_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy file to simulate export
    with open(export_dir / "dry-run-export.txt", "w") as f:
        f.write(f"Simulated export of {website_name} at {export_dir}\n")
        f.write("This is a dry run, no actual FTP connection was made.\n")

    logger.info(f"Completed simulated export for website: {website_name}")
    return True


def export_website(config: Dict[str, Any], website_name: str) -> bool:
    """Export website content from remote server.

    Args:
        config: Config dictionary
        website_name: Name of the website

    Returns:
        bool: True if export successful, False otherwise
    """
    logger = logging.getLogger("exporter")
    logger.info(f"Exporting website {website_name}...")

    # Check if in dry run mode
    if config.get("dry_run"):
        return _simulate_export(config, website_name)

    # Get export directory from config
    export_dir = Path(config["paths"]["workspaces"]) / website_name / "export"
    logger.debug(f"Export directory: {export_dir}")

    # Ensure export directory exists and is empty
    if export_dir.exists():
        shutil.rmtree(export_dir)
    export_dir.mkdir(parents=True)

    # Get website config
    website_config = config["website"]
    hostinger_config = website_config.get("hostinger", {})
    ftp_host = hostinger_config.get("host", f"ftp.{website_config['website'].get('domain', '')}")
    remote_dir = hostinger_config.get("remote_dir", "/")

    try:
        # Connect to FTP server using credential manager or fallback to config
        if CRED_MANAGER_AVAILABLE:
            try:
                # Get credentials from credential manager
                username = cred_manager.get_credential(website_name, "FTP_USERNAME")
                password = cred_manager.get_credential(website_name, "FTP_PASSWORD")
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
            return False

        # Connect to FTP server with timeout
        with ftputil.FTPHost(ftp_host, username, password, timeout=20) as ftp_host:
            # Check if the specified remote_dir exists
            if not ftp_host.path.exists(remote_dir):
                logger.error(f"Remote directory {remote_dir} does not exist.")
                return False

            # Get all files recursively from the remote directory
            logger.info(f"Starting download from {remote_dir}...")

            def _download_tree(remote_path, local_path):
                """Download a directory tree recursively."""
                # Create local directory
                local_dir = Path(local_path)
                local_dir.mkdir(exist_ok=True)

                # List remote directory
                for item in ftp_host.listdir(remote_path):
                    remote_item = ftp_host.path.join(remote_path, item)
                    local_item = os.path.join(local_path, item)

                    # Skip directory links that might cause infinite recursion
                    if ftp_host.path.islink(remote_item):
                        logger.debug(f"Skipping symbolic link: {remote_item}")
                        continue

                    # Download directory recursively
                    if ftp_host.path.isdir(remote_item):
                        logger.debug(f"Processing directory: {remote_item}")
                        _download_tree(remote_item, local_item)
                    # Download file
                    else:
                        logger.debug(f"Downloading: {remote_item}")
                        ftp_host.download(remote_item, local_item)

            # Start recursive download
            _download_tree(remote_dir, export_dir)
            logger.info(f"Website content exported to: {export_dir}")
            return True

    except ftplib.all_errors as e:
        logger.error(f"FTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error exporting website: {e}")
        return False


def _export_via_ftp(config: Dict[str, Any], website_name: str, export_dir: Path) -> bool:
    """
    Export a website from Hostinger using FTP.

    Args:
        config: The loaded configuration
        website_name: Name of the website to export
        export_dir: Directory to save exported files

    Returns:
        True if successful, False otherwise
    """

    logger = logging.getLogger("orchestrator.exporter.ftp")
    website_config = config["website"]

    # Get FTP configuration
    hostinger_config = website_config.get("hostinger", {})
    ftp_host = hostinger_config.get("host", f"ftp.{website_config['website'].get('domain', '')}")
    remote_dir = hostinger_config.get("remote_dir", "/")

    logger.info(f"Starting FTP export from {ftp_host}{remote_dir}")

    try:
        # Connect to FTP server with timeout
        with ftputil.FTPHost(ftp_host, timeout=20) as ftp_host:
            # Check if the specified remote_dir exists
            if not ftp_host.path.exists(remote_dir):
                logger.error(f"Specified remote directory {remote_dir} does not exist!")
                logger.info("Please check your configuration and set the correct remote_dir path.")
                logger.info("You can use debug mode to see available directories.")
                return False
            else:
                logger.info(f"Confirmed {remote_dir} exists and will be used for download.")

            # Download files recursively
            file_count = 0
            dir_count = 0
            skipped_count = 0

            for dirpath, dirnames, filenames in ftp_host.walk(remote_dir):
                # Create the corresponding local path
                rel_path = os.path.relpath(dirpath, remote_dir)
                local_path = export_dir / rel_path if rel_path != "." else export_dir

                # Create local subdirectories
                os.makedirs(local_path, exist_ok=True)
                dir_count += 1

                if dir_count <= 5:  # Only show first 5 directories in debug mode
                    logger.debug(f"Processing directory: {dirpath}")

                # Download each file
                for filename in filenames:
                    remote_file = os.path.join(dirpath, filename)
                    local_file = local_path / filename

                    # Check if file exists and is newer
                    update_file = True
                    if local_file.exists():
                        remote_time = ftp_host.path.getmtime(remote_file)
                        local_time = os.path.getmtime(local_file)
                        if local_time >= remote_time:
                            if skipped_count < 5:  # Limit log entries
                                logger.debug(f"Skipping (up to date): {remote_file}")
                            skipped_count += 1
                            update_file = False

                    if update_file:
                        if file_count < 10:  # Only show first 10 files in debug mode
                            logger.debug(f"Downloading: {remote_file}")
                        file_count += 1
                        ftp_host.download(remote_file, str(local_file))

            # Log summary
            logger.info("FTP export completed successfully:")
            logger.info(f"  Directories processed: {dir_count}")
            logger.info(f"  Files downloaded: {file_count}")
            logger.info(f"  Files skipped (up to date): {skipped_count}")

            return True

    except Exception as e:
        logger.error(f"FTP export failed: {e}")
        return False


# For development/testing purposes
def simulate_export(config: Dict[str, Any], website_name: str) -> bool:
    """
    Simulate a website export for development purposes.

    Args:
        config: The loaded configuration
        website_name: Name of the website to export

    Returns:
        True if successful
    """
    logger = logging.getLogger("orchestrator.exporter")

    # Determine the workspace directory
    workspace_name = config["website"]["website"].get("workspace", website_name)
    workspace_dir = Path(config["paths"]["workspaces"]) / workspace_name
    export_dir = workspace_dir / "export"

    # Ensure export directory exists
    os.makedirs(export_dir, exist_ok=True)

    logger.info(f"Simulating export for website: {website_name} to {export_dir}")

    # Create fake export files
    sample_html = export_dir / "index.html"
    sample_css = export_dir / "styles.css"

    # Check if we have a sample template directory
    template_dir = Path(config.get("templates", {}).get("directory", "templates"))
    if os.path.exists(template_dir / "sample_website"):
        logger.info(f"Using template from {template_dir / 'sample_website'}")
        shutil.copytree(template_dir / "sample_website", export_dir, dirs_exist_ok=True)
    else:
        # Create a minimal fake website if no template available
        logger.info("Creating minimal sample website")
        with open(sample_html, "w") as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sample Exported Website</title>
                <link rel="stylesheet" href="styles.css">
            </head>
            <body>
                <header>
                    <h1>Sample Exported Website</h1>
                </header>
                <main>
                    <p>This is a simulated export of the website.</p>
                </main>
                <footer>
                    <p>&copy; 2023 Example</p>
                </footer>
            </body>
            </html>
            """)

        with open(sample_css, "w") as f:
            f.write("""
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
            }
            header, footer {
                background-color: #f8f8f8;
                padding: 10px;
                text-align: center;
            }
            main {
                padding: 20px;
            }
            """)

    logger.info(f"Completed simulated export for website: {website_name}")
    return True


def connect_ftp(config: Dict[str, Any], website_name: str) -> Optional[FTP]:
    """Connect to FTP server using credentials from config or credential manager.

    Args:
        config: Configuration dictionary
        website_name: Name of the website

    Returns:
        FTP connection object or None if connection fails
    """
    # Get FTP settings from config
    try:
        ftp_config = config["website"].get("ftp", {})
        host = ftp_config.get("host")

        # First try to get credentials from credential manager
        if CRED_MANAGER_AVAILABLE:
            try:
                username = cred_manager.get_credential(website_name, "FTP_USERNAME")
                password = cred_manager.get_credential(website_name, "FTP_PASSWORD")
                logger.debug(f"Using credentials from credential manager for {website_name}")
            except Exception as e:
                # Fall back to config if credential manager fails
                logger.debug(f"Credential manager failed, falling back to config: {e}")
                username = ftp_config.get("username")
                password = ftp_config.get("password")
        else:
            # Use credentials from config if credential manager is not available
            username = ftp_config.get("username")
            password = ftp_config.get("password")

        if not all([host, username, password]):
            logger.error(
                "Missing FTP credentials. Please check your configuration or use the credential manager."
            )
            return None

        # Connect to FTP server
        ftp = FTP()
        ftp.connect(host)
        ftp.login(username, password)
        logger.info(f"Connected to FTP server: {host}")
        return ftp

    except ftplib.all_errors as e:
        logger.error(f"FTP connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error connecting to FTP: {e}")
        return None
