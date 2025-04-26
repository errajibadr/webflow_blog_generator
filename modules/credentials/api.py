"""
Credential API Module

This module provides the high-level API for credential management.
"""

import logging
from typing import Any, Dict, List, Optional

from modules.credentials.manager import BackendManager
from modules.credentials.types import (
    CredentialAccessError,
    CredentialStorageError,
    CredentialValidationError,
)

# Configure logging
logger = logging.getLogger(__name__)


def store_credential(
    website_name: str,
    cred_type: str,
    value: str,
    backend_type: Optional[str] = None,
    **backend_config,
) -> bool:
    """Store a credential using the selected backend.

    Args:
        website_name: Name of the website
        cred_type: Type of credential (e.g., FTP_USERNAME, FTP_PASSWORD)
        value: The credential value to store
        backend_type: Optional backend type to use
        **backend_config: Configuration for the backend

    Returns:
        bool: True if storage successful

    Raises:
        CredentialValidationError: If validation fails
        CredentialStorageError: If storage fails
    """
    # Normalize inputs
    website_name = website_name.lower().strip()
    cred_type = cred_type.upper().strip()

    # Validate inputs
    if not website_name:
        raise CredentialValidationError("Website name cannot be empty")
    if not cred_type:
        raise CredentialValidationError("Credential type cannot be empty")
    if value is None:
        raise CredentialValidationError("Credential value cannot be None")

    try:
        backend = BackendManager.get_backend(backend_type, **backend_config)
        return backend.store_credential(website_name, cred_type, value)
    except Exception as e:
        logger.error(f"Error storing credential: {str(e)}")
        raise CredentialStorageError(f"Failed to store credential: {str(e)}")


def get_credential(
    website_name: str, cred_type: str, backend_type: Optional[str] = None, **backend_config
) -> str:
    """Retrieve a credential using the selected backend.

    Args:
        website_name: Name of the website
        cred_type: Type of credential to retrieve
        backend_type: Optional backend type to use
        **backend_config: Configuration for the backend

    Returns:
        str: The credential value

    Raises:
        CredentialAccessError: If credential cannot be accessed
    """
    # Normalize inputs
    website_name = website_name.lower().strip()
    cred_type = cred_type.upper().strip()

    try:
        backend = BackendManager.get_backend(backend_type, **backend_config)
        return backend.get_credential(website_name, cred_type)
    except KeyError:
        raise CredentialAccessError(f"Credential not found: {website_name}/{cred_type}")
    except Exception as e:
        logger.error(f"Error retrieving credential: {str(e)}")
        raise CredentialAccessError(f"Failed to retrieve credential: {str(e)}")


def delete_credential(
    website_name: str, cred_type: str, backend_type: Optional[str] = None, **backend_config
) -> bool:
    """Delete a credential using the selected backend.

    Args:
        website_name: Name of the website
        cred_type: Type of credential to delete
        backend_type: Optional backend type to use
        **backend_config: Configuration for the backend

    Returns:
        bool: True if deletion successful

    Raises:
        CredentialAccessError: If credential cannot be accessed
    """
    # Normalize inputs
    website_name = website_name.lower().strip()
    cred_type = cred_type.upper().strip()

    try:
        backend = BackendManager.get_backend(backend_type, **backend_config)
        return backend.delete_credential(website_name, cred_type)
    except Exception as e:
        logger.error(f"Error deleting credential: {str(e)}")
        raise CredentialAccessError(f"Failed to delete credential: {str(e)}")


def list_credentials(
    website_name: Optional[str] = None, backend_type: Optional[str] = None, **backend_config
) -> Dict[str, Dict[str, str]]:
    """List credentials using the selected backend.

    Args:
        website_name: Optional website name to filter by
        backend_type: Optional backend type to use
        **backend_config: Configuration for the backend

    Returns:
        Dict[str, Dict[str, str]]: Dictionary of credentials by website

    Raises:
        CredentialAccessError: If credentials cannot be accessed
    """
    if website_name:
        website_name = website_name.lower().strip()

    try:
        backend = BackendManager.get_backend(backend_type, **backend_config)
        return backend.list_credentials(website_name)
    except Exception as e:
        logger.error(f"Error listing credentials: {str(e)}")
        raise CredentialAccessError(f"Failed to list credentials: {str(e)}")


def set_backend(backend_type: str, **config) -> None:
    """Set the active credential backend.

    Args:
        backend_type: Backend type to use
        **config: Configuration for the backend

    Raises:
        ValueError: If backend type is invalid
    """
    BackendManager.get_backend(backend_type, **config)


def get_current_backend() -> str:
    """Get the current backend type.

    Returns:
        str: Current backend type or 'file' if none set
    """
    return BackendManager._current_backend or "file"


def list_available_backends() -> List[Dict[str, Any]]:
    """List all available credential backends.

    Returns:
        List[Dict[str, Any]]: Information about available backends
    """
    return BackendManager.list_available_backends()
