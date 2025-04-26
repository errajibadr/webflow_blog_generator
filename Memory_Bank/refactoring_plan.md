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