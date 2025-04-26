#!/usr/bin/env python3
"""
FTP Importer Module

Handles optimized FTP uploads for website importing with concurrent transfers
and robust error handling.
"""

from __future__ import annotations

import ftplib
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from ftplib import FTP
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import ftputil
import ftputil.error

from modules.credentials import get_credential

logger = logging.getLogger(__name__)


class FTPImporter:
    """
    Handles website importing via FTP with optimized performance.
    Consolidates functionality from previous import implementations.
    """

    def __init__(self, config, max_workers=4, chunk_size=8192):
        """
        Initialize the FTP importer with configuration and performance settings.

        Args:
            config: The configuration dictionary
            max_workers: Maximum number of concurrent upload workers
            chunk_size: Size of chunks for large file uploads
        """
        self.config = config
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.logger = logging.getLogger("orchestrator.importer.ftp")
        self.stats = {"uploaded": 0, "skipped": 0, "failed": 0, "dirs_created": 0}

    def connect(self, website_name):
        """
        Establish FTP connection using credentials from config or credential manager.

        Args:
            website_name: Name of the website for credential lookup

        Returns:
            ftputil.FTPHost: Connected FTP host object

        Raises:
            ConnectionError: If connection fails
        """
        website_config = self.config["website"]
        hostinger_config = website_config.get("hostinger", {})

        # Get FTP host
        ftp_host = hostinger_config.get(
            "host", f"ftp.{website_config['website'].get('domain', '')}"
        )

        # Get credentials from credential manager or config
        try:
            # Try credential manager first
            username = get_credential(website_name, "FTP_USERNAME")
            password = get_credential(website_name, "FTP_PASSWORD")
            self.logger.debug(f"Using credentials from credential manager for {website_name}")
        except Exception as e:
            # Fall back to config
            self.logger.debug(f"Credential manager failed, falling back to config: {e}")
            username = hostinger_config.get("username")
            password = hostinger_config.get("password")

        if not all([ftp_host, username, password]):
            raise ValueError(
                "Missing FTP credentials. Please check your configuration or use the credential manager."
            )

        # Connect with enhanced settings
        try:
            ftp_host = ftputil.FTPHost(
                ftp_host,
                username,
                password,
                timeout=30,
                encoding="latin1",  # Use latin1 for better compatibility with special characters
            )

            # Set binary mode for the FTP session
            ftp_host._session.voidcmd("TYPE I")

            self.logger.info(f"Connected to FTP server: {ftp_host}")
            return ftp_host
        except ftplib.all_errors as e:
            self.logger.error(f"FTP connection error: {e}")
            raise ConnectionError(f"Failed to connect to FTP server: {e}")
        except Exception as e:
            self.logger.error(f"Error connecting to FTP: {e}")
            raise ConnectionError(f"Unexpected error connecting to FTP: {e}")

    def _ensure_remote_dir(self, ftp_host, remote_dir):
        """
        Ensure remote directory exists, create if necessary.

        Args:
            ftp_host: Connected FTP host
            remote_dir: Remote directory path

        Returns:
            bool: True if successful
        """
        try:
            if not ftp_host.path.exists(remote_dir):
                self.logger.debug(f"Creating remote directory: {remote_dir}")
                ftp_host.makedirs(remote_dir)
                self.stats["dirs_created"] += 1
            return True
        except UnicodeEncodeError:
            self.logger.error(f"Encoding error with directory name: {remote_dir}")
            return False
        except Exception as e:
            self.logger.error(f"Error creating remote directory {remote_dir}: {e}")
            return False

    def _purge_remote_dir(self, ftp_host, remote_dir):
        """
        Recursively delete all files and directories in remote directory.

        Args:
            ftp_host: Connected FTP host
            remote_dir: Remote directory to purge
        """
        try:
            for item in ftp_host.listdir(remote_dir):
                item_path = ftp_host.path.join(remote_dir, item)
                if ftp_host.path.isdir(item_path):
                    self.logger.info(f"Recursively deleting remote directory: {item_path}")
                    self._purge_remote_dir(ftp_host, item_path)
                    ftp_host.rmdir(item_path)
                    self.logger.debug(f"Deleted remote directory: {item_path}")
                else:
                    ftp_host.remove(item_path)

            self.logger.info(f"Purged all contents of remote directory: {remote_dir}")
        except Exception as e:
            self.logger.error(f"Error purging remote directory {remote_dir}: {e}")
            raise

    def _should_upload_file(self, ftp_host, local_file, remote_file):
        """
        Determine if a file needs to be uploaded based on modification times.

        Args:
            ftp_host: Connected FTP host
            local_file: Path to local file
            remote_file: Path to remote file

        Returns:
            bool: True if file should be uploaded
        """
        if not ftp_host.path.exists(remote_file):
            return True

        try:
            local_time = os.path.getmtime(local_file)
            try:
                remote_time = ftp_host.path.getmtime(remote_file)
                if remote_time >= local_time:
                    return False
            except ftputil.error.FTPOSError:
                # If we can't get the mtime, upload to be safe
                self.logger.debug(f"Could not get mtime for {remote_file}, will upload")
                return True
        except Exception as e:
            self.logger.error(f"Error comparing file times for {local_file}: {e}")
            # Upload to be safe if we can't compare times
            return True

        return True

    def _upload_file(self, ftp_host, local_file, remote_file, retries=3, backoff_factor=2):
        """
        Upload a single file with retry logic.

        Args:
            ftp_host: Connected FTP host
            local_file: Path to local file
            remote_file: Path to remote file
            retries: Number of retry attempts
            backoff_factor: Exponential backoff factor

        Returns:
            bool: True if upload succeeds
        """
        temp_remote_file = os.path.join(
            os.path.dirname(remote_file), f".in.{os.path.basename(remote_file)}"
        )

        # Clean up temp file if it exists before upload
        if ftp_host.path.exists(temp_remote_file):
            try:
                self.logger.warning(
                    f"Removing leftover temp file before upload: {temp_remote_file}"
                )
                ftp_host.remove(temp_remote_file)
            except Exception as cleanup_error:
                self.logger.error(f"Failed to remove temp file {temp_remote_file}: {cleanup_error}")

        # Attempt upload with retries
        attempt = 0
        while attempt < retries:
            try:
                with open(local_file, "rb") as local_fp:
                    # Reset binary mode before each transfer
                    ftp_host._session.voidcmd("TYPE I")
                    # Use lower level FTP commands for more control
                    ftp_host._session.storbinary(f"STOR {remote_file}", local_fp)
                return True
            except Exception as upload_error:
                attempt += 1
                if attempt >= retries:
                    self.logger.error(
                        f"Error during upload of {local_file} after {retries} attempts: {upload_error}"
                    )
                    return False
                else:
                    wait_time = backoff_factor**attempt
                    self.logger.warning(
                        f"Upload attempt {attempt} failed for {local_file}, retrying in {wait_time}s: {upload_error}"
                    )
                    time.sleep(wait_time)

        return False

    def _process_files(self, ftp_host, local_dir, remote_dir, filenames):
        """
        Process files in a directory with concurrent uploads.

        Args:
            ftp_host: Connected FTP host
            local_dir: Local directory path
            remote_dir: Remote directory path
            filenames: List of filenames to process
        """
        # Prepare file upload tasks
        upload_tasks = []

        for filename in filenames:
            try:
                local_file = os.path.join(local_dir, filename)
                remote_file = os.path.join(remote_dir, filename)

                # Check if file needs to be uploaded
                if self._should_upload_file(ftp_host, local_file, remote_file):
                    upload_tasks.append((local_file, remote_file))
                else:
                    self.stats["skipped"] += 1
                    if self.stats["skipped"] <= 5:  # Limit log spam
                        self.logger.debug(f"Skipping (up to date): {remote_file}")
            except UnicodeEncodeError:
                self.logger.error(f"Encoding error with file: {filename}")
                continue
            except Exception as e:
                self.logger.error(f"Error preparing file {filename}: {e}")
                continue

        # If we have files to upload, do it sequentially for now
        # This will be updated to concurrent uploads in Phase 2
        for local_file, remote_file in upload_tasks:
            if self._upload_file(ftp_host, local_file, remote_file):
                self.stats["uploaded"] += 1
                if self.stats["uploaded"] <= 10:  # Limit log entries for larger uploads
                    self.logger.debug(f"Uploaded: {local_file} -> {remote_file}")
            else:
                self.stats["failed"] += 1
                self.logger.error(f"Failed to upload: {local_file}")

    def _process_directory(self, ftp_host, source_dir, remote_base_dir, preserve_parent):
        """
        Process a directory recursively, uploading all files.

        Args:
            ftp_host: Connected FTP host
            source_dir: Source directory path
            remote_base_dir: Base remote directory
            preserve_parent: Whether to preserve parent directory name
        """
        source_name = source_dir.name if preserve_parent else ""
        self.logger.info(
            f"Processing source directory: {source_dir}{' (preserving directory name)' if preserve_parent else ''}"
        )

        # Walk the local directory structure
        for dirpath, dirnames, filenames in os.walk(source_dir):
            self.logger.info(f"Processing directory: {dirpath}")
            # Create the corresponding remote path
            rel_path = os.path.relpath(dirpath, source_dir)

            # Build remote path based on preservation flag
            if preserve_parent:
                if rel_path == ".":
                    remote_path = os.path.join(remote_base_dir, source_name)
                else:
                    remote_path = os.path.join(remote_base_dir, source_name, rel_path)
            else:
                remote_path = (
                    os.path.join(remote_base_dir, rel_path) if rel_path != "." else remote_base_dir
                )

            # Ensure remote directory exists
            if not self._ensure_remote_dir(ftp_host, remote_path):
                continue

            # Process files in this directory
            self._process_files(ftp_host, dirpath, remote_path, filenames)

    def import_website(self, website_name, source_dirs=None, purge_remote=False):
        """
        Import a website to the remote server via FTP.

        Args:
            website_name: Name of the website
            source_dirs: List of tuples (directory_path, preserve_parent_flag)
                        If None, uses website output directory
            purge_remote: If True, purge remote directory before import

        Returns:
            bool: True if import succeeds
        """
        self.logger.info(f"Importing website {website_name}...")

        # Check if in dry run mode
        if self.config.get("dry_run"):
            self.logger.info(f"DRY RUN: Would import website {website_name}")
            return True

        # Get source directories
        if source_dirs is None:
            workspace = self.config["website"]["website"].get("workspace", website_name)
            output_dir = Path(self.config["paths"]["workspaces"]) / workspace / "output"

            if not output_dir.exists():
                self.logger.error(f"Output directory does not exist: {output_dir}")
                return False

            source_dirs = [(output_dir, False)]

        # Get remote directory
        website_config = self.config["website"]
        hostinger_config = website_config.get("hostinger", {})
        remote_dir = hostinger_config.get("remote_dir", "/")

        # Connect to FTP server
        try:
            ftp_host = self.connect(website_name)
        except Exception as e:
            self.logger.error(f"Failed to connect to FTP server: {e}")
            return False

        # Process FTP import
        try:
            with ftp_host:
                # Check/create remote directory
                if not ftp_host.path.exists(remote_dir):
                    self.logger.info(f"Creating remote directory {remote_dir}")
                    ftp_host.makedirs(remote_dir)
                elif purge_remote:
                    self.logger.warning(f"Purging all contents of remote directory: {remote_dir}")
                    self._purge_remote_dir(ftp_host, remote_dir)

                # Reset statistics
                self.stats = {"uploaded": 0, "skipped": 0, "failed": 0, "dirs_created": 0}

                # Process each source directory
                for source_dir, preserve_parent in source_dirs:
                    self._process_directory(ftp_host, source_dir, remote_dir, preserve_parent)

                # Log summary
                self.logger.info("FTP import completed successfully:")
                self.logger.info(f"  Directories created: {self.stats['dirs_created']}")
                self.logger.info(f"  Files uploaded: {self.stats['uploaded']}")
                self.logger.info(f"  Files skipped (up to date): {self.stats['skipped']}")
                self.logger.info(f"  Files failed: {self.stats['failed']}")

                return self.stats["failed"] == 0

        except Exception as e:
            self.logger.error(f"FTP import failed: {e}")
            return False


# Function to use the FTPImporter class with the same interface as before
def import_website(config, website_name, purge_remote=False):
    """
    Import a website to Hostinger using the optimized FTPImporter.

    Args:
        config: The loaded configuration
        website_name: Name of the website to import
        purge_remote: If True, purge all files in the remote directory before import

    Returns:
        True if successful, False otherwise
    """
    importer = FTPImporter(config)
    return importer.import_website(website_name, purge_remote=purge_remote)
