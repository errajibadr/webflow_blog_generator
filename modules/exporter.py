#!/usr/bin/env python3
"""
Website Exporter Module

This module handles exporting websites from Hostinger, using one of these methods:
1. Hostinger API (if available)
2. FTP export (preferred method)
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict

import ftputil


def export_website(config: Dict[str, Any], website_name: str) -> Path:
    """
    Export a website from Hostinger.

    Args:
        config: The loaded configuration
        website_name: Name of the website to export

    Returns:
        Path to the exported website files
    """
    logger = logging.getLogger("orchestrator.exporter")
    website_config = config["website"]

    # Determine the workspace directory
    workspace_name = website_config["website"].get("workspace", website_name)
    workspace_dir = Path(config["paths"]["workspaces"]) / workspace_name
    export_dir = workspace_dir / "export"

    # Ensure export directory exists
    os.makedirs(export_dir, exist_ok=True)

    logger.info(f"Exporting website: {website_name} to {export_dir}")

    try:
        # Get export method from config or use default priority order
        export_method = website_config.get("export", {}).get("method", "auto")

        if export_method == "ftp":
            success = _export_via_ftp(config, website_name, export_dir)
        elif export_method == "simulate":
            success = simulate_export(config, website_name)

        if not success:
            raise RuntimeError(f"Failed to export website: {website_name}")

        logger.info(f"Successfully exported website: {website_name} to {export_dir}")
        return export_dir

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise RuntimeError(f"Failed to export website: {e}")


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
    ftp_user = hostinger_config["username"]
    ftp_password = hostinger_config["password"]
    remote_dir = hostinger_config.get("remote_dir", "/")

    logger.info(f"Starting FTP export from {ftp_host}{remote_dir}")

    try:
        # Connect to FTP server
        with ftputil.FTPHost(ftp_host, ftp_user, ftp_password) as ftp_host:
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
