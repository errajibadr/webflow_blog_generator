# Website Blog Generator Orchestrator - Active Context

## Current Focus

- Implementing secure credential management for FTP accounts with container support
- Creating a pluggable backend system for credential storage
- Designing a flexible system for adding new websites in workspaces
- Improving the configuration system to support credential references
- Implementing container-friendly deployment options

## Environment

- OS: macOS (Darwin kernel version 23.3.0)
- Path separator: /
- Project root: /Users/badrou/repository/website_blog_generator

## Core Components

1. **Main Orchestrator** (main.py)
   - CLI interface
   - Pipeline coordination
   - Configuration management
   - *New: Credential management commands*
   - *New: Backend selection commands*
   
2. **Exporter Module** (modules/exporter.py)
   - Downloads site via FTP
   - Stores in workspace/export directory
   - *Update needed: Use credential manager for FTP auth*
   
3. **Content Generator** (modules/content_generator/)
   - Generates blog content via API
   - Based on topics from CSV files
   - Outputs JSON blog articles
   
4. **Enricher Module** (modules/enricher.py)
   - Integrates content into website
   - Uses Node.js tool (website_enricher/)
   - Creates SEO elements and sitemaps
   
5. **Importer Module** (modules/importer.py)
   - Uploads enriched site to Hostinger
   - FTP-based file transfer
   - *Update needed: Use credential manager for FTP auth*
   
6. **Credential Manager** (modules/cred_manager.py) - *New Component*
   - Secure storage of FTP credentials
   - Pluggable backend system
   - Backend-agnostic credential API
   - Integration with config system
   
7. **Credential Backends** - *New Components*
   - **File Backend**: Encrypted local storage for development
   - **Environment Backend**: Container-friendly environment variable storage
   - **Vault Backend** (future): External API integration for production

## Implementation Plan

### Phase 1: Core Credential Management
- Create credential manager module with backend abstraction
- Implement file and environment backends
- Add backend selection mechanism
- Build credential API

### Phase 2: Configuration Integration
- Extend configuration loading
- Update import/export modules
- Ensure backward compatibility
- Add migration utilities

### Phase 3: User Interface
- Add CLI commands for credential management
- Add backend selection commands
- Implement container-specific utilities
- Create clear error messages

### Phase 4: Documentation and Examples
- Update documentation with credential management
- Create containerization guides
- Add deployment examples for Docker/Kubernetes
- Document security best practices

## Security Considerations

- Credential encryption for file backend
- Container secrets best practices
- Separation of credentials from config files
- Secure handling of sensitive data in memory
- Backend-specific security documentation

## Container Support

- Environment backend for Docker/Kubernetes
- Support for container secrets
- Persistent credential storage options
- Data migration between backends
- Docker Compose and Kubernetes examples

## Open Questions

- Best approach for persistent credentials in short-lived containers
- Automatic credential rotation strategy
- Integration with orchestration platforms' secret management
- Multi-container credential sharing best practices 