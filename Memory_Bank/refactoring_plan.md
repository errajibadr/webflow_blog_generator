# Refactoring Plan

## Overview

The codebase currently has two files that have grown too large and need to be refactored:
1. `modules/cred_manager.py` - Credential management module (~850 lines)
2. `main.py` - Main orchestration script (~500 lines)

This plan outlines a structured approach to break these files into smaller, more maintainable modules with clear responsibilities while maintaining backward compatibility.

## Goals

- Improve maintainability through better code organization
- Enhance separation of concerns
- Improve testability by isolating components
- Maintain backward compatibility
- Prepare the codebase for future extensibility

## Phase 1: Credential Manager Refactoring

### New Structure

```
modules/
├── credentials/
│   ├── __init__.py         # Re-exports key components
│   ├── types.py            # Enums, exceptions, abstract base classes
│   ├── manager.py          # BackendManager
│   ├── api.py              # Public API functions
│   ├── cli.py              # CLI functions
│   └── backends/
│       ├── __init__.py     # Backend registry
│       ├── file.py         # FileBackend
│       └── env.py          # EnvironmentBackend
```

### Implementation Tasks

1. **Create Directory Structure**
   - Create the `modules/credentials` package and submodules

2. **Implement `types.py`**
   - Move `CredentialType` enum
   - Move `CredentialBackend` abstract base class
   - Move exception classes (`CredentialValidationError`, `CredentialAccessError`, etc.)

3. **Implement Backend Modules**
   - Create `backends/file.py` for `FileBackend`
   - Create `backends/env.py` for `EnvironmentBackend`
   - Create `backends/__init__.py` for registration

4. **Implement `manager.py`**
   - Move `BackendManager` class
   - Implement backend discovery and registration

5. **Implement `api.py`**
   - Move public API functions (`store_credential`, `get_credential`, etc.)
   - Update to use the new module structure

6. **Implement `cli.py`**
   - Move CLI-related functions (`manage_credentials`, `configure_website_credentials`)
   - Ensure compatibility with main.py

7. **Create Comprehensive `__init__.py`**
   - Re-export all public components to maintain backward compatibility
   - Add any necessary documentation

8. **Update Other Modules**
   - Update imports in `exporter.py` and `importer.py`
   - Ensure compatibility checks (`CRED_MANAGER_AVAILABLE`)

## Phase 2: Main.py Refactoring

### New Structure

```
modules/
├── config/
│   ├── __init__.py         # Re-exports
│   ├── loader.py           # Configuration loading
│   └── processor.py        # Configuration processing
├── pipeline/
│   ├── __init__.py         # Re-exports
│   ├── orchestration.py    # Pipeline orchestration
│   └── steps.py            # Individual pipeline steps
└── cli/
    ├── __init__.py         # Re-exports
    ├── args.py             # Argument parsing
    └── commands.py         # Command execution
```

### Implementation Tasks

1. **Create Config Module**
   - Move `load_config` and related functions to `config/loader.py`
   - Move variable expansion to `config/processor.py`
   - Create exports in `config/__init__.py`

2. **Create Pipeline Module**
   - Move `run_pipeline` to `pipeline/orchestration.py`
   - Move individual step functions to `pipeline/steps.py`
   - Create exports in `pipeline/__init__.py`

3. **Create CLI Module**
   - Move `parse_args` to `cli/args.py`
   - Create command execution functions in `cli/commands.py`
   - Create exports in `cli/__init__.py`

4. **Simplify Main.py**
   - Keep only the essential coordination logic
   - Import and use the new modules
   - Maintain backward compatibility

5. **Update Documentation**
   - Update inline documentation
   - Update README if necessary

## Testing Strategy

1. **Unit Tests**
   - Add unit tests for each new module
   - Focus on testing public API boundaries

2. **Integration Tests**
   - Add tests for key integration points
   - Test credential management with real backends
   - Test configuration loading and processing

3. **Manual Verification**
   - Verify that all CLI commands still work
   - Verify that existing websites still export and import correctly

## Timeline

- Phase 1 (Credential Manager): 1-2 days
- Phase 2 (Main.py): 1-2 days
- Testing and Documentation: 1 day

## Risks and Mitigations

- **Risk**: Breaking existing functionality
  - **Mitigation**: Maintain backward compatibility through careful re-exports
  
- **Risk**: Incomplete refactoring of dependencies
  - **Mitigation**: Thorough testing and verification of each affected component

- **Risk**: Migration challenges for existing users
  - **Mitigation**: Provide clear documentation and maintain backward compatibility

## Success Criteria

- All existing functionality works as before
- Code is organized into logical modules with clear responsibilities
- Each module is 200 lines or less (with reasonable exceptions)
- Unit tests cover critical functionality
- Documentation is updated to reflect the new structure 

# FTP Importer Refactoring Plan

## Requirements Analysis

- Core Requirements:
  - [ ] Consolidate duplicate FTP import functionality into a single well-structured implementation
  - [ ] Preserve all existing functionality from the more complete `_import_via_ftp` function
  - [ ] Improve import speed through optimization techniques
  - [ ] Maintain robust error handling and logging
  - [ ] No need to maintain backward compatibility

- Technical Constraints:
  - [ ] Continue using ftputil library as the primary FTP client
  - [ ] Support credential retrieval from both config and credential manager
  - [ ] Ensure binary mode transfers for all file types
  - [ ] Implement file timestamp comparison to skip unchanged files

## Component Analysis

- Affected Components:
  - `modules/importer.py`
    - Changes needed:
      - Replace `import_website` function with improved implementation based on `_import_via_ftp`
      - Refactor FTP connection logic from both functions into a single utility
      - Update logging to use consistent approach across all FTP operations
      - Implement parallel upload capabilities for performance improvement
      - Add file checksum comparison option for more reliable file change detection
    - Dependencies:
      - `modules/credentials.py` for credential retrieval
      - ftputil and ftplib libraries for FTP operations

## Design Decisions

- Architecture:
  - [ ] Create a modular FTPImporter class to encapsulate all FTP functionality
  - [ ] Implement connection pooling for concurrent uploads
  - [ ] Separate connection, directory management, and file upload concerns
  - [ ] Add optional checksum-based file change detection

- Algorithms:
  - [ ] Implement concurrent file uploads using Python's concurrent.futures
  - [ ] Add chunked file uploads for large files to improve reliability
  - [ ] Implement retry mechanism with exponential backoff for failed uploads
  - [ ] Add file batching to reduce connection overhead

## Implementation Strategy

1. Phase 1: Function Consolidation
   - [ ] Create new unified import function combining features from both existing functions
   - [ ] Refactor credential and connection logic into separate utility functions
   - [ ] Update logging to use consistent naming and verbosity levels
   - [ ] Add comprehensive error handling for all FTP operations

2. Phase 2: Performance Optimization
   - [ ] Implement concurrent file uploads using ThreadPoolExecutor
   - [ ] Add file batching to reduce overhead for many small files
   - [ ] Implement retry logic for failed transfers
   - [ ] Add progress reporting for long-running uploads

3. Phase 3: Advanced Features
   - [ ] Add optional checksum comparison for more reliable file change detection
   - [ ] Implement chunked uploads for large files
   - [ ] Add bandwidth throttling option for constrained environments
   - [ ] Implement connection pooling for improved performance

## Testing Strategy

- Unit Tests:
  - [ ] Test FTP connection logic with mock FTP server
  - [ ] Test file change detection logic (timestamp and checksum)
  - [ ] Test path handling, especially with Unicode characters
  - [ ] Test retry and error handling mechanisms

- Integration Tests:
  - [ ] Test with actual FTP server in controlled environment
  - [ ] Test large file uploads and directory structures
  - [ ] Test performance with different concurrency settings
  - [ ] Test error recovery scenarios

## Implementation Detail Notes

### FTPImporter Class Structure

```python
class FTPImporter:
    """Handles FTP imports with optimized performance."""
    
    def __init__(self, config, max_workers=4, chunk_size=8192):
        self.config = config
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.logger = logging.getLogger("orchestrator.importer.ftp")
        
    def connect(self, website_name):
        """Establish FTP connection with credentials from config or credential manager."""
        # Connection logic here
        
    def import_website(self, website_name, source_dirs=None, purge_remote=False):
        """Main import method with optimized concurrent uploads."""
        # Implementation here
        
    def _upload_file(self, local_path, remote_path):
        """Upload a single file with retry logic."""
        # Implementation here
        
    def _calculate_checksum(self, file_path):
        """Calculate file checksum for change detection."""
        # Implementation here
```

### Concurrency Implementation

```python
from concurrent.futures import ThreadPoolExecutor

def _upload_files_concurrently(self, file_list, max_workers=None):
    """Upload multiple files concurrently."""
    workers = max_workers or self.max_workers
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(self._upload_file, src, dst): (src, dst) 
                  for src, dst in file_list}
        
        for future in as_completed(futures):
            src, dst = futures[future]
            try:
                success = future.result()
                if success:
                    self.stats['uploaded'] += 1
                else:
                    self.stats['failed'] += 1
            except Exception as e:
                self.logger.error(f"Error uploading {src} to {dst}: {e}")
                self.stats['failed'] += 1
``` 