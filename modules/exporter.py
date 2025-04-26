#!/usr/bin/env python3
"""
Website Exporter Module

This module handles exporting websites via FTP from hosting providers like Hostinger.
"""

from __future__ import annotations

import concurrent.futures
import ftplib
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional

import ftputil

from modules.credentials import get_credential

logger = logging.getLogger(__name__)

# Constants for performance tuning
MAX_WORKERS = 5  # Number of parallel download workers
CHUNK_SIZE = 8192 * 8  # 64KB chunks for large file downloads
CONNECTION_TIMEOUT = 30  # FTP connection timeout in seconds
RETRY_COUNT = 3  # Number of retries for failed downloads
RETRY_DELAY = 2  # Delay between retries in seconds
LARGE_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB threshold for chunk-based download
SUCCESS_RATE_THRESHOLD = 0.9  # 90% success rate required for export to be considered successful


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
    ftp_host_str = hostinger_config.get(
        "host", f"ftp.{website_config['website'].get('domain', '')}"
    )
    remote_dir = hostinger_config.get("remote_dir", "/")

    try:
        # Get FTP credentials from credential manager or fallback to config
        try:
            username = get_credential(website_name, "FTP_USERNAME")
            password = get_credential(website_name, "FTP_PASSWORD")
            logger.debug(f"Using credentials from credential manager for {website_name}")
        except Exception as e:
            # Fall back to config if credential manager fails
            logger.debug(f"Credential manager failed, falling back to config: {e}")
            username = hostinger_config.get("username")
            password = hostinger_config.get("password")

        if not all([ftp_host_str, username, password]):
            logger.error(
                "Missing FTP credentials. Please check your configuration or use the credential manager."
            )
            return False

        # Connect to FTP server and download website content
        return _download_website_content(
            ftp_host_str=ftp_host_str,
            username=username,
            password=password,
            remote_dir=remote_dir,
            export_dir=export_dir,
            config=config,
        )

    except ftplib.all_errors as e:
        logger.error(f"FTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error exporting website: {e}")
        return False


def _download_website_content(
    ftp_host_str: str,
    username: str,
    password: str,
    remote_dir: str,
    export_dir: Path,
    config: Dict[str, Any],
) -> bool:
    """Download website content via FTP.

    Args:
        ftp_host_str: FTP hostname
        username: FTP username
        password: FTP password
        remote_dir: Remote directory path
        export_dir: Local export directory
        config: Configuration dictionary

    Returns:
        bool: True if successful, False otherwise
    """
    logger = logging.getLogger("exporter")

    try:
        # Connect to FTP server with timeout
        with ftputil.FTPHost(
            ftp_host_str, username, password, timeout=CONNECTION_TIMEOUT
        ) as ftp_host:
            # Check if the specified remote_dir exists
            if not ftp_host.path.exists(remote_dir):
                logger.error(f"Remote directory {remote_dir} does not exist.")
                return False

            # Get all files recursively from the remote directory
            logger.info(f"Starting download from {remote_dir}...")

            # Use sequential scanning and parallel download approach
            return _sequential_scan_parallel_download(
                ftp_host=ftp_host,
                host_str=ftp_host_str,
                username=username,
                password=password,
                remote_dir=remote_dir,
                export_dir=export_dir,
            )

    except Exception as e:
        logger.error(f"Error downloading website content: {e}")
        return False


def _sequential_scan_parallel_download(
    ftp_host, host_str: str, username: str, password: str, remote_dir: str, export_dir: Path
) -> bool:
    """
    Scan files sequentially, then download in parallel using dedicated connections.

    Args:
        ftp_host: FTPHost connection for scanning
        host_str: FTP host string
        username: FTP username
        password: FTP password
        remote_dir: Remote directory path
        export_dir: Local export directory

    Returns:
        bool: True if successful, False otherwise
    """
    logger = logging.getLogger("exporter.parallel")

    # Create a list to hold all file tasks
    download_tasks = []
    dir_count = 0

    # First pass: Build the directory structure and collect file tasks
    logger.info("Scanning remote structure and building directory tree...")
    start_time = time.time()

    try:
        # Normalize the remote directory path
        remote_dir = remote_dir.rstrip("/") + "/"
        if remote_dir == "//":
            remote_dir = "/"

        # Use a file cache to avoid redundant downloads
        file_cache = {}  # Format: {remote_path: (size, mtime)}

        # Set the initial working directory explicitly
        ftp_host.chdir(remote_dir)

        # Walk the directory tree
        for dirpath, dirnames, filenames in ftp_host.walk("."):
            # Convert relative paths to absolute paths
            abs_remote_path = ftp_host.path.abspath(dirpath) if dirpath != "." else remote_dir

            # Create the corresponding local path
            rel_path = os.path.relpath(dirpath, ".") if dirpath != "." else ""
            local_path = export_dir / rel_path if rel_path else export_dir

            # Create local subdirectories
            os.makedirs(local_path, exist_ok=True)
            dir_count += 1

            if dir_count <= 5:  # Only show first 5 directories in debug mode
                logger.debug(f"Processing directory: {abs_remote_path}")

            # Collect download tasks for all files in this directory
            for filename in filenames:
                # Use absolute paths to avoid working directory issues
                remote_file = ftp_host.path.join(abs_remote_path, filename)
                local_file = local_path / filename

                # Get file size and modification time
                try:
                    file_size = ftp_host.path.getsize(remote_file)
                    mod_time = ftp_host.path.getmtime(remote_file)
                    file_cache[remote_file] = (file_size, mod_time)

                    # Check if file exists and is newer
                    update_file = True
                    if local_file.exists():
                        local_time = os.path.getmtime(local_file)
                        if local_time >= mod_time:
                            update_file = False

                    if update_file:
                        # Add to download tasks with absolute path
                        download_tasks.append((remote_file, str(local_file), file_size))
                except Exception as e:
                    logger.warning(f"Error checking file {remote_file}: {e}")

        scan_time = time.time() - start_time
        logger.info(
            f"Directory scan completed in {scan_time:.2f}s. Found {len(download_tasks)} files to download."
        )

        # Sort tasks by size (smaller files first to maximize throughput)
        download_tasks.sort(key=lambda x: x[2])

        # Second pass: Download files in parallel using separate connections
        if download_tasks:
            # Calculate optimal worker count based on file count and system capabilities
            worker_count = min(MAX_WORKERS, len(download_tasks))
            logger.info(f"Starting parallel download with {worker_count} workers")

            # Track statistics
            successful_downloads = 0
            failed_downloads = 0

            with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
                # Create a function that establishes its own connection
                def download_with_own_connection(remote_file, local_file, file_size):
                    try:
                        # Each worker gets its own FTP connection
                        with ftputil.FTPHost(
                            host_str, username, password, timeout=CONNECTION_TIMEOUT
                        ) as worker_ftp:
                            return _download_file_with_retry(
                                worker_ftp, remote_file, local_file, file_size
                            )
                    except Exception as e:
                        logger.error(f"Connection error for {remote_file}: {e}")
                        return False

                # Submit download tasks
                future_to_file = {}
                for remote_file, local_file, file_size in download_tasks:
                    future = executor.submit(
                        download_with_own_connection,
                        remote_file=remote_file,
                        local_file=local_file,
                        file_size=file_size,
                    )
                    future_to_file[future] = (remote_file, local_file)

                # Process completed downloads
                total_tasks = len(future_to_file)
                completed = 0

                for future in concurrent.futures.as_completed(future_to_file):
                    remote_file, local_file = future_to_file[future]
                    try:
                        success = future.result()
                        if success:
                            successful_downloads += 1
                        else:
                            failed_downloads += 1
                            logger.error(f"Failed to download: {remote_file}")
                    except Exception as e:
                        failed_downloads += 1
                        logger.error(f"Exception downloading {remote_file}: {e}")

                    # Update progress
                    completed += 1
                    if completed % 10 == 0 or completed == total_tasks:
                        progress = (completed / total_tasks) * 100
                        logger.info(f"Progress: {progress:.1f}% ({completed}/{total_tasks})")

        total_time = time.time() - start_time
        logger.info(f"FTP export completed in {total_time:.2f}s:")
        logger.info(f"  Directories processed: {dir_count}")
        logger.info(f"  Files downloaded: {successful_downloads}")
        logger.info(f"  Files failed: {failed_downloads}")
        logger.info(f"  Files skipped: {len(file_cache) - len(download_tasks)}")

        # Consider export successful if at least SUCCESS_RATE_THRESHOLD of files were downloaded
        if total_tasks > 0:
            success_rate = float(successful_downloads) / float(total_tasks)
            if success_rate < SUCCESS_RATE_THRESHOLD:
                logger.warning(f"Download success rate was only {success_rate:.1%}")
            return success_rate >= SUCCESS_RATE_THRESHOLD
        return True

    except Exception as e:
        logger.error(f"Error during file scanning or download: {e}")
        return False


def _download_file_with_retry(ftp_host, remote_file: str, local_file: str, file_size: int) -> bool:
    """
    Download a file with retry logic and optimized for large files.

    Args:
        ftp_host: FTPHost connection
        remote_file: Remote file path
        local_file: Local file path
        file_size: Size of the file in bytes

    Returns:
        bool: True if successful, False otherwise
    """
    logger = logging.getLogger("exporter.download")

    for attempt in range(RETRY_COUNT):
        try:
            # Create local directory if it doesn't exist
            os.makedirs(os.path.dirname(local_file), exist_ok=True)

            if file_size > LARGE_FILE_THRESHOLD:
                # Use chunk-based download for large files to optimize memory usage
                _download_large_file(ftp_host, remote_file, local_file)
            else:
                # Use standard download - make sure we're using an absolute path
                ftp_host.download(remote_file, local_file)

            # Verify file size after download
            if os.path.exists(local_file) and os.path.getsize(local_file) > 0:
                return True
            else:
                logger.warning(f"Size verification failed for {remote_file}, retrying...")

        except ftplib.error_perm as e:
            # Permanent error - no need to retry
            logger.error(f"FTP permission error for {remote_file}: {e}")
            return False

        except Exception as e:
            if attempt < RETRY_COUNT - 1:
                logger.warning(f"Download attempt {attempt + 1} failed for {remote_file}: {e}")
                time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"All download attempts failed for {remote_file}: {e}")
                return False

    return False


def _download_large_file(ftp_host, remote_file: str, local_file: str) -> None:
    """
    Download a large file in chunks to minimize memory usage.

    Args:
        ftp_host: FTPHost connection
        remote_file: Remote file path
        local_file: Local file path
    """
    # Make sure local directory exists
    os.makedirs(os.path.dirname(local_file), exist_ok=True)

    with open(local_file, "wb") as local_fp:
        try:
            # Use lower level FTP command to get the file
            ftp_host.download_if_newer(remote_file, local_file)
        except Exception:
            # Fallback - try to get the raw session
            try:
                ftp_session = ftp_host._session

                # Go to parent directory of the file
                parent_dir = os.path.dirname(remote_file)
                if parent_dir:
                    ftp_session.cwd(parent_dir)

                # Get just the filename
                filename = os.path.basename(remote_file)

                # Open data connection in binary mode
                cmd = f"RETR {filename}"
                with ftp_session.transfercmd(cmd) as conn:
                    while True:
                        data = conn.recv(CHUNK_SIZE)
                        if not data:
                            break
                        local_fp.write(data)

                # Complete the transfer
                ftp_session.voidresp()

            except Exception as e:
                # Let the retry mechanism handle this
                raise Exception(f"Chunk download failed: {e}")


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


def simulate_export(config: Dict[str, Any], website_name: str) -> bool:
    """
    Simulate a website export for development/testing purposes.

    Args:
        config: The loaded configuration
        website_name: Name of the website to export

    Returns:
        True if successful
    """
    logger = logging.getLogger("exporter")

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
