"""
Credential Manager Module for secure FTP credential storage.

This module provides a secure way to store and retrieve FTP credentials
using pluggable backend storage mechanisms.

Note: This module is maintained for backward compatibility.
New code should import directly from the modules.credentials package.
"""

# Import all public components from the credentials package
from modules.credentials import (  # Types; API functions; CLI functions
    CredentialAccessError,
    CredentialBackend,
    CredentialStorageError,
    CredentialType,
    CredentialValidationError,
    EncryptionError,
    configure_website_credentials,
    delete_credential,
    get_credential,
    get_current_backend,
    list_available_backends,
    list_credentials,
    manage_credentials,
    set_backend,
    store_credential,
)

# Ensure the backends are registered
from modules.credentials.backends import register_backends

# Re-register backends for this module's context
register_backends()

# Re-export all public components
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
