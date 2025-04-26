# Credential Manager Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for the FTP credential management system. The implementation will follow a phased approach to ensure minimal disruption to existing functionality while supporting containerization through pluggable credential storage backends.

## Phase 1: Core Credential Management Module

### Step 1: Set Up Dependencies
- [ ] Add cryptography package to requirements.txt
- [ ] Add hvac package (optional, for Vault backend)
- [ ] Create basic structure for cred_manager.py in modules directory
- [ ] Set up backend abstract base class

### Step 2: Implement Backend System
- [ ] Create abstract CredentialBackend base class
- [ ] Implement backend selection and configuration mechanism
- [ ] Set up backend manager to handle different backend types

### Step 3: Implement File Backend
- [ ] Create key generation and management functions
- [ ] Implement encryption and decryption utilities
- [ ] Add secure storage mechanism for file-based credentials
- [ ] Implement file backend class adhering to CredentialBackend interface

### Step 4: Implement Environment Backend
- [ ] Create environment variable naming convention
- [ ] Implement environment variable get/set methods
- [ ] Add environment backend class adhering to CredentialBackend interface
- [ ] Create helper function for Docker/Kubernetes environment setup

### Step 5: Implement Core Credential API
- [ ] Implement store_credential function
- [ ] Implement get_credential function
- [ ] Implement delete_credential function
- [ ] Implement list_credentials function
- [ ] Add backend-agnostic credential validation

### Deliverables:
- modules/cred_manager.py with complete implementation
- Backend system with File and Environment backends
- Support for backend configuration via config or environment
- Unit tests for credential management functions

## Phase 2: Configuration Integration

### Step 1: Extend Configuration Loading
- [ ] Modify expand_env_vars function in main.py to detect credential references
- [ ] Add credential resolution capability to config loading
- [ ] Add backend configuration support
- [ ] Ensure backward compatibility with existing env var format

### Step 2: Update Importer Module
- [ ] Modify FTP credential retrieval in importer.py
- [ ] Add error handling for missing credentials
- [ ] Update docstrings and logging
- [ ] Add backend-aware error messages

### Step 3: Update Exporter Module
- [ ] Modify FTP credential retrieval in exporter.py
- [ ] Add error handling for missing credentials
- [ ] Update docstrings and logging
- [ ] Add backend-aware error messages

### Step 4: Create Migration Utility
- [ ] Implement migrate_from_config function
- [ ] Add detection for hardcoded vs. referenced credentials
- [ ] Create utility function for config file conversion
- [ ] Create helpers for container environment setup

### Deliverables:
- Updated main.py with credential reference support
- Updated exporter.py and importer.py
- Migration utility for existing configurations
- Integration tests for the full export/import cycle
- Container environment setup helpers

## Phase 3: User Interface and Documentation

### Step 1: Add CLI Commands
- [ ] Add --credential-backend command to select backend
- [ ] Add --credential add command
- [ ] Add --credential remove command
- [ ] Add --credential list command
- [ ] Add --credential test command

### Step 2: Improve Error Handling
- [ ] Add user-friendly error messages for credential issues
- [ ] Implement validation for all credential inputs
- [ ] Add secure error logging (without exposing credentials)
- [ ] Add backend-specific error messages

### Step 3: Update Documentation
- [ ] Update README.md with credential management section
- [ ] Create security best practices documentation
- [ ] Add example configurations using credential references
- [ ] Create quick-start guide for credential setup
- [ ] Add containerization guide with examples

### Step 4: Containerization Examples
- [ ] Create Docker Compose example with environment backend
- [ ] Create Kubernetes manifest example with secrets
- [ ] Add documentation for container deployment options
- [ ] Create example workflow for credential management in containers

### Deliverables:
- Updated CLI interface with credential and backend commands
- Comprehensive documentation updates
- Example configurations and scripts
- Containerization guides and examples
- End-to-end workflow validation

## Phase 4: Future Backend Expansion (Optional)

### Step 1: Implement External API Backend
- [ ] Add Vault integration via hvac library
- [ ] Implement VaultBackend class
- [ ] Add authentication and connection management
- [ ] Create examples and documentation

### Step 2: Cloud Provider Integrations
- [ ] Add AWS Secrets Manager backend (optional)
- [ ] Add GCP Secret Manager backend (optional)
- [ ] Add Azure Key Vault backend (optional)
- [ ] Create cloud provider deployment examples

### Deliverables:
- Additional backend implementations
- Cloud provider deployment guides
- Advanced security documentation

## Testing Strategy

### Unit Tests
- [ ] Test backend interface and manager
- [ ] Test file backend implementation
- [ ] Test environment backend implementation
- [ ] Test configuration loading with credentials
- [ ] Test error handling and validation

### Integration Tests
- [ ] Test full export/import cycle with file backend
- [ ] Test full export/import cycle with environment backend
- [ ] Test CLI commands for credential management
- [ ] Test backward compatibility scenarios
- [ ] Test error scenarios and recovery

### Container Tests
- [ ] Test Docker deployment with environment backend
- [ ] Test Docker Compose setup with shared credentials
- [ ] Test Kubernetes deployment with secrets (if applicable)
- [ ] Verify container restart credential persistence

### Security Tests
- [ ] Verify credential file permissions
- [ ] Check for potential credential leakage
- [ ] Validate encryption strength
- [ ] Test against common security threats
- [ ] Verify container security best practices

## Timeline

| Phase | Estimated Duration | Dependencies |
|-------|-------------------|--------------|
| Phase 1 | 2-3 days | None |
| Phase 2 | 2-3 days | Phase 1 |
| Phase 3 | 2-3 days | Phase 2 |
| Phase 4 | 3-5 days (optional) | Phase 3 |
| Testing | Ongoing throughout | All phases |

## Rollout Plan

1. **Development Environment**
   - Implement and test all changes
   - Validate with sample websites
   - Test with both file and environment backends
   - Document any issues found

2. **Testing Environment**
   - Deploy to testing environment
   - Migrate sample configurations
   - Test containerized deployment
   - Verify all functionality

3. **Production Release**
   - Create migration guide for users
   - Add safety checks for production use
   - Provide container deployment examples
   - Monitor initial deployments for issues

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Broken backward compatibility | Medium | High | Thorough testing, fallback mechanism |
| Security vulnerabilities | Low | Critical | Security review, best practices |
| Performance degradation | Low | Medium | Caching, optimization |
| User confusion | Medium | Medium | Clear documentation, examples |
| Container integration issues | Medium | High | Detailed examples, container-specific tests |

## Acceptance Criteria

- All unit and integration tests pass
- Existing workflows continue to function
- New credential management commands work as expected
- Container deployment examples function correctly
- Documentation is complete and clear
- Migration utility successfully converts existing configs 

# FTP Importer Implementation Plan

## Overview

This implementation plan details the steps to refactor the website import functionality in the `modules/importer.py` file. The goal is to consolidate duplicate FTP import functionality, improve performance through parallelization, and enhance error handling while maintaining all existing features.

## Phase 1: Function Consolidation

### Step 1.1: Create FTPImporter Class

Create a new class-based implementation that will replace both the `import_website` and `_import_via_ftp` functions.

```python
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
        self.stats = {
            'uploaded': 0,
            'skipped': 0,
            'failed': 0,
            'dirs_created': 0
        }
```

### Step 1.2: Implement Connection Logic

Extract and refactor the FTP connection logic from both existing functions:

```python
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
```

### Step 1.3: Implement Directory Management Functions

Extract directory management logic into dedicated methods:

```python
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
            self.stats['dirs_created'] += 1
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
```

### Step 1.4: Implement File Upload Logic

Create optimized file upload methods:

```python
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
    temp_remote_file = os.path.join(os.path.dirname(remote_file), f".in.{os.path.basename(remote_file)}")
    
    # Clean up temp file if it exists before upload
    if ftp_host.path.exists(temp_remote_file):
        try:
            self.logger.warning(f"Removing leftover temp file before upload: {temp_remote_file}")
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
                self.logger.error(f"Error during upload of {local_file} after {retries} attempts: {upload_error}")
                return False
            else:
                wait_time = backoff_factor ** attempt
                self.logger.warning(f"Upload attempt {attempt} failed for {local_file}, retrying in {wait_time}s: {upload_error}")
                time.sleep(wait_time)
    
    return False
```

### Step 1.5: Implement Main Import Method

Create the main import method that leverages all the above components:

```python
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
            self.stats = {
                'uploaded': 0,
                'skipped': 0,
                'failed': 0,
                'dirs_created': 0
            }
            
            # Process each source directory
            for source_dir, preserve_parent in source_dirs:
                self._process_directory(ftp_host, source_dir, remote_dir, preserve_parent)
            
            # Log summary
            self.logger.info("FTP import completed successfully:")
            self.logger.info(f"  Directories created: {self.stats['dirs_created']}")
            self.logger.info(f"  Files uploaded: {self.stats['uploaded']}")
            self.logger.info(f"  Files skipped (up to date): {self.stats['skipped']}")
            self.logger.info(f"  Files failed: {self.stats['failed']}")
            
            return self.stats['failed'] == 0
    
    except Exception as e:
        self.logger.error(f"FTP import failed: {e}")
        return False
```

### Step 1.6: Implement Directory Processing Method

```python
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
```

## Phase 2: Performance Optimization

### Step 2.1: Implement Concurrent File Upload

Add a method to handle concurrent uploads using ThreadPoolExecutor:

```python
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
                self.stats['skipped'] += 1
                if self.stats['skipped'] <= 5:  # Limit log spam
                    self.logger.debug(f"Skipping (up to date): {remote_file}")
        except UnicodeEncodeError:
            self.logger.error(f"Encoding error with file: {filename}")
            continue
        except Exception as e:
            self.logger.error(f"Error preparing file {filename}: {e}")
            continue
    
    # If we have files to upload, do it concurrently
    if upload_tasks:
        self._upload_files_concurrently(ftp_host, upload_tasks)

def _upload_files_concurrently(self, ftp_host, file_list):
    """
    Upload multiple files concurrently.
    
    Args:
        ftp_host: Connected FTP host
        file_list: List of (local_file, remote_file) tuples
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
        # Submit all upload tasks
        futures = {
            executor.submit(self._upload_file, ftp_host, src, dst): (src, dst)
            for src, dst in file_list
        }
        
        # Process results as they complete
        for i, future in enumerate(as_completed(futures)):
            src, dst = futures[future]
            try:
                success = future.result()
                if success:
                    self.stats['uploaded'] += 1
                    if self.stats['uploaded'] <= 10:  # Limit log entries for larger uploads
                        self.logger.debug(f"Uploaded: {src} -> {dst}")
                else:
                    self.stats['failed'] += 1
                    self.logger.error(f"Failed to upload: {src}")
            except Exception as e:
                self.stats['failed'] += 1
                self.logger.error(f"Error uploading {src} to {dst}: {e}")
```

## Phase 3: Advanced Features

### Step 3.1: Add Checksum-Based File Comparison

```python
def _calculate_checksum(self, file_path, algorithm='md5'):
    """
    Calculate file checksum for change detection.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        str: Hexadecimal checksum
    """
    import hashlib
    
    hash_alg = getattr(hashlib, algorithm)()
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(self.chunk_size), b''):
            hash_alg.update(chunk)
            
    return hash_alg.hexdigest()

def _compare_files_by_checksum(self, ftp_host, local_file, remote_file):
    """
    Compare local and remote files by checksum.
    
    Args:
        ftp_host: Connected FTP host
        local_file: Path to local file
        remote_file: Path to remote file
        
    Returns:
        bool: True if files are different and need uploading
    """
    import tempfile
    
    # Calculate local checksum
    local_checksum = self._calculate_checksum(local_file)
    
    # Download remote file to temp location and calculate checksum
    with tempfile.NamedTemporaryFile() as temp_file:
        try:
            ftp_host.download(remote_file, temp_file.name)
            remote_checksum = self._calculate_checksum(temp_file.name)
            
            # Compare checksums
            return local_checksum != remote_checksum
        except Exception as e:
            self.logger.warning(f"Error comparing checksums, will upload: {e}")
            return True
```

### Step 3.2: Implement Chunked File Uploads

```python
def _upload_large_file(self, ftp_host, local_file, remote_file, chunk_size=None):
    """
    Upload a large file in chunks to improve reliability.
    
    Args:
        ftp_host: Connected FTP host
        local_file: Path to local file
        remote_file: Path to remote file
        chunk_size: Size of chunks in bytes
        
    Returns:
        bool: True if upload succeeds
    """
    chunk_size = chunk_size or self.chunk_size
    temp_file = f"{remote_file}.part"
    
    try:
        # Clean up any existing temp file
        if ftp_host.path.exists(temp_file):
            ftp_host.remove(temp_file)
            
        # Upload in chunks
        with open(local_file, 'rb') as f:
            # Set binary mode
            ftp_host._session.voidcmd("TYPE I")
            
            # Start a STOR command
            cmd = f"STOR {temp_file}"
            conn = ftp_host._session.transfercmd(cmd)
            
            # Send file in chunks
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                conn.sendall(chunk)
                
            # Complete the transfer
            conn.close()
            ftp_host._session.voidresp()
            
            # Rename temp file to final name
            ftp_host.rename(temp_file, remote_file)
            
        return True
    except Exception as e:
        self.logger.error(f"Error during chunked upload of {local_file}: {e}")
        
        # Try to clean up temp file on error
        try:
            if ftp_host.path.exists(temp_file):
                ftp_host.remove(temp_file)
        except:
            pass
            
        return False
```

## Implementation Approach

1. Create a new file `ftp_importer.py` in the modules directory with the FTPImporter class
2. Implement connection, directory management, and file upload methods
3. Add performance optimizations with concurrent uploads
4. Test the new implementation thoroughly
5. Update the main importer.py to use the new FTPImporter class
6. Remove the old duplicate functions once the new implementation is verified

## API Usage Example

```python
def import_website(config, website_name, purge_remote=False):
    """Updated import_website function that uses the new FTPImporter class."""
    from modules.ftp_importer import FTPImporter
    
    importer = FTPImporter(config)
    return importer.import_website(website_name, purge_remote=purge_remote)
``` 