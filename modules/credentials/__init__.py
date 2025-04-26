"""
Credential Management Package

This package provides secure credential storage and retrieval with multiple backend options.
It maintains backward compatibility with the original cred_manager module.
"""

# Register backends first to ensure they're available
from modules.credentials.backends import register_backends

registered_backends = register_backends()

# Import and re-export public API
from modules.credentials.api import (
    delete_credential,
    get_credential,
    get_current_backend,
    list_available_backends,
    list_credentials,
    set_backend,
    store_credential,
)

# Import and re-export CLI functions
from modules.credentials.cli import configure_website_credentials, manage_credentials

# Import and re-export types
from modules.credentials.types import (
    CredentialAccessError,
    CredentialBackend,
    CredentialStorageError,
    CredentialType,
    CredentialValidationError,
    EncryptionError,
)

# Maintain backward compatibility
# This allows existing imports to continue working without changes
__all__ = [
    # Types
    "CredentialType",
    "CredentialBackend",
    "CredentialValidationError",
    "CredentialAccessError",
    "CredentialStorageError",
    "EncryptionError",
    # API functions
    "store_credential",
    "get_credential",
    "delete_credential",
    "list_credentials",
    "set_backend",
    "get_current_backend",
    "list_available_backends",
    # CLI functions
    "manage_credentials",
    "configure_website_credentials",
]
