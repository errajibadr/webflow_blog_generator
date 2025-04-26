# Credential Manager Architecture Design

## Overview

The Credential Manager will be a secure system for storing and accessing FTP credentials used by the Website Blog Generator Orchestrator. It will provide an interface for managing credentials while keeping sensitive information separate from regular configuration files, with pluggable backends to support various deployment scenarios including containerization.

## Architecture

```
┌─────────────────────┐      ┌─────────────────────┐
│                     │      │                     │
│  Main Orchestrator  │◄────►│ Credential Manager  │
│     (main.py)       │      │  (cred_manager.py)  │
│                     │      │                     │
└─────────────────────┘      └──────────┬──────────┘
         │                              │
         │                              │
         ▼                              ▼
┌─────────────────────┐      ┌─────────────────────┐
│                     │      │                     │
│  Import/Export      │◄────►│   Backend Manager   │
│  Modules            │      │                     │
│                     │      └──────────┬──────────┘
└─────────────────────┘                 │
                              ┌─────────┴─────────┐
                              │                   │
                  ┌───────────┴───────┐   ┌───────┴───────┐   ┌───────┴───────┐
                  │                   │   │               │   │               │
                  │  File Backend     │   │ Env Backend   │   │ Vault Backend │
                  │ (.env.encrypted)  │   │               │   │  (External)   │
                  │                   │   │               │   │               │
                  └───────────────────┘   └───────────────┘   └───────────────┘
```

## Core Components

1. **Credential Manager Module (modules/cred_manager.py)**
   - Main interface for credential operations
   - Provides methods for storing, retrieving, and validating credentials
   - Delegates storage operations to the configured backend
   - Abstracts backend details from other modules

2. **Backend Manager**
   - Manages different credential storage backends
   - Handles backend selection based on configuration
   - Provides unified interface for credential operations

3. **Storage Backends**
   - **File Backend** (Default)
     - Securely stores encrypted credentials in `.env.encrypted`
     - Uses Fernet symmetric encryption
     - Ideal for development and simple deployments
   
   - **Environment Backend**
     - Uses environment variables for credential storage
     - Suitable for containerized environments
     - No persistent storage required
   
   - **External API Backend** (Future)
     - Integrates with external secret management services (Vault, AWS Secrets Manager, etc.)
     - Supports advanced features like rotation and auditing
     - Ideal for production and multi-user scenarios

4. **Configuration Integration**
   - Website configs will store references to credential keys, not actual values
   - Example: `username: ${cred:WEBSITE_NAME_FTP_USERNAME}`
   - Extended environment variable syntax for credential references

5. **CLI Commands**
   - Commands for credential management through the main.py interface
   - Allows adding, updating, and removing credentials
   - Provides validation and security checks
   - Backend-aware operations

## Backend Selection

The credential backend can be selected through:

1. Configuration setting in `config.yaml`:
   ```yaml
   credential_manager:
     backend: "file"  # Options: file, env, vault
     backend_config:
       file:
         path: ".env.encrypted"
       vault:
         url: "https://vault.example.com"
         token_env: "VAULT_TOKEN"
   ```

2. Environment variable:
   ```
   CRED_BACKEND=env
   ```

3. Command-line flag:
   ```
   python main.py --credential-backend env
   ```

## Backend Interface

All backends will implement the same abstract interface:

```python
class CredentialBackend(ABC):
    @abstractmethod
    def store_credential(self, website_name: str, cred_type: str, value: str) -> bool:
        """Store a credential in the backend."""
        pass
        
    @abstractmethod
    def get_credential(self, website_name: str, cred_type: str) -> str:
        """Retrieve a credential from the backend."""
        pass
        
    @abstractmethod
    def delete_credential(self, website_name: str, cred_type: str) -> bool:
        """Delete a credential from the backend."""
        pass
        
    @abstractmethod
    def list_credentials(self, website_name: Optional[str] = None) -> List[Dict[str, str]]:
        """List credentials in the backend."""
        pass
```

## File Backend Implementation

The file backend will use Fernet encryption to store credentials securely:

```python
class FileBackend(CredentialBackend):
    def __init__(self, file_path: str = ".env.encrypted", key_source: str = "env"):
        self.file_path = file_path
        self.key = self._get_encryption_key(key_source)
        self.cache = {}
        
    def store_credential(self, website_name: str, cred_type: str, value: str) -> bool:
        """Encrypts and stores credential in file."""
        # Implementation details...
        
    def get_credential(self, website_name: str, cred_type: str) -> str:
        """Retrieves and decrypts credential from file."""
        # Implementation details...
```

## Environment Backend Implementation

The environment backend will use environment variables directly:

```python
class EnvironmentBackend(CredentialBackend):
    def __init__(self, prefix: str = "CRED_"):
        self.prefix = prefix
        
    def _make_env_key(self, website_name: str, cred_type: str) -> str:
        """Convert website name and credential type to environment variable name."""
        return f"{self.prefix}{website_name.upper()}_{cred_type.upper()}"
        
    def store_credential(self, website_name: str, cred_type: str, value: str) -> bool:
        """Sets environment variable with credential value."""
        # Implementation details...
        
    def get_credential(self, website_name: str, cred_type: str) -> str:
        """Retrieves credential from environment variable."""
        # Implementation details...
```

## Vault Backend Implementation (Future)

The Vault backend will integrate with external secret management services:

```python
class VaultBackend(CredentialBackend):
    def __init__(self, url: str, token: str, mount_point: str = "secret"):
        self.client = hvac.Client(url=url, token=token)
        self.mount_point = mount_point
        
    def store_credential(self, website_name: str, cred_type: str, value: str) -> bool:
        """Stores credential in Vault."""
        # Implementation details...
        
    def get_credential(self, website_name: str, cred_type: str) -> str:
        """Retrieves credential from Vault."""
        # Implementation details...
```

## Data Flow

1. **Credential Storage Flow:**
   ```
   User input → Validation → Backend Manager → Selected Backend → Storage
   ```

2. **Credential Retrieval Flow:**
   ```
   Config reference → Backend Manager → Selected Backend → Retrieval → Use in module
   ```

3. **Backend Selection Flow:**
   ```
   Check CLI args → Check Environment → Check Config → Default to File Backend
   ```

## API Design

```python
# Core credential management (backend-agnostic)
def store_credential(website_name: str, cred_type: str, value: str) -> bool
def get_credential(website_name: str, cred_type: str) -> str
def delete_credential(website_name: str, cred_type: str) -> bool
def list_credentials(website_name: Optional[str] = None) -> List[Dict[str, str]]

# Backend management
def get_backend() -> CredentialBackend
def set_backend(backend_type: str, **config) -> None
def list_available_backends() -> List[str]
```

## Configuration Format Changes

Current format:
```yaml
hostinger:
  host: ftp.sample-website.com
  username: ${HOSTINGER_FTP_USERNAME}  
  password: ${HOSTINGER_FTP_PASSWORD}
```

New format (unchanged from the original design):
```yaml
hostinger:
  host: ftp.sample-website.com
  username: ${cred:SAMPLE_WEBSITE_FTP_USERNAME}  
  password: ${cred:SAMPLE_WEBSITE_FTP_PASSWORD}
```

## Implementation Considerations

1. **Backward Compatibility**
   - Support both direct env vars and credential references
   - Migration utility for existing configurations
   - Graceful fallback for missing credential manager

2. **Performance Optimization**
   - Caching mechanism for frequently used credentials
   - Lazy loading of backends
   - Connection pooling for external services

3. **Containerization Support**
   - Environment backend for Docker/Kubernetes
   - External API backend for production deployments
   - Configuration examples for container deployment

4. **Testing Approach**
   - Mock backends for automated testing
   - Backend-specific tests
   - Security audit tests

## Next Steps

1. Implement core Credential Manager module with backend abstraction
2. Implement File Backend and Environment Backend
3. Extend configuration loading to support credential references
4. Update import/export modules to use credential manager
5. Add CLI commands for credential management
6. Create documentation with examples for different deployment scenarios 