"""
Credential Types Module

This module defines the common types, abstract classes, and exceptions for the credential management system.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional


class CredentialType(str, Enum):
    """Standard credential types."""

    FTP_USERNAME = "FTP_USERNAME"
    FTP_PASSWORD = "FTP_PASSWORD"


class CredentialBackend(ABC):
    """Abstract base class for credential storage backends."""

    @abstractmethod
    def store_credential(self, website_name: str, cred_type: str, value: str) -> bool:
        """Store a credential in the backend.

        Args:
            website_name: Name of the website
            cred_type: Type of credential (e.g., FTP_USERNAME, FTP_PASSWORD)
            value: The credential value to store

        Returns:
            bool: True if storage successful, False otherwise
        """
        pass

    @abstractmethod
    def get_credential(self, website_name: str, cred_type: str) -> str:
        """Retrieve a credential from the backend.

        Args:
            website_name: Name of the website
            cred_type: Type of credential to retrieve

        Returns:
            str: The credential value

        Raises:
            KeyError: If credential not found
        """
        pass

    @abstractmethod
    def delete_credential(self, website_name: str, cred_type: str) -> bool:
        """Delete a credential from the backend.

        Args:
            website_name: Name of the website
            cred_type: Type of credential to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        pass

    @abstractmethod
    def list_credentials(self, website_name: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """List credentials in the backend.

        Args:
            website_name: Optional website name to filter by

        Returns:
            Dict[str, Dict[str, str]]: Dictionary of credentials by website
        """
        pass


class CredentialValidationError(Exception):
    """Exception raised for credential validation errors."""

    pass


class CredentialAccessError(Exception):
    """Exception raised for credential access errors."""

    pass


class CredentialStorageError(Exception):
    """Exception raised for credential storage errors."""

    pass


class EncryptionError(Exception):
    """Exception raised for encryption/decryption errors."""

    pass
