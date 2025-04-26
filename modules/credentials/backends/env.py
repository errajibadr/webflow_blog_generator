"""
Environment-based Credential Backend

This module provides an environment variable-based backend for credential storage.
"""

import logging
import os
from typing import Dict, Optional, Tuple

from modules.credentials.manager import BackendManager
from modules.credentials.types import CredentialBackend, CredentialStorageError

# Configure logging
logger = logging.getLogger(__name__)


class EnvironmentBackend(CredentialBackend):
    """Environment variable-based credential storage backend."""

    def __init__(self, prefix: str = "CRED_"):
        """Initialize the environment backend.

        Args:
            prefix: Prefix for environment variables
        """
        self.prefix = prefix

    def _make_env_key(self, website_name: str, cred_type: str) -> str:
        """Create environment variable name from website and credential type.

        Args:
            website_name: Name of the website
            cred_type: Type of credential

        Returns:
            str: Environment variable name
        """
        return f"{self.prefix}{website_name.upper()}_{cred_type.upper()}"

    def _parse_env_key(self, env_key: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse website name and credential type from environment variable name.

        Args:
            env_key: Environment variable name

        Returns:
            tuple: (website_name, cred_type) or (None, None) if invalid
        """
        if not env_key.startswith(self.prefix):
            return None, None

        parts = env_key[len(self.prefix) :].split("_", 1)
        if len(parts) != 2:
            return None, None

        return parts[0].lower(), parts[1]

    def store_credential(self, website_name: str, cred_type: str, value: str) -> bool:
        """Store a credential in environment variables.

        Note: This will only affect the current process and its children.
        The credential will not persist after the process exits.

        Args:
            website_name: Name of the website
            cred_type: Type of credential
            value: The credential value

        Returns:
            bool: True if storage successful

        Raises:
            CredentialStorageError: If storage fails
        """
        try:
            env_key = self._make_env_key(website_name, cred_type)
            os.environ[env_key] = value
            return True
        except Exception as e:
            raise CredentialStorageError(f"Failed to store credential in environment: {e}")

    def get_credential(self, website_name: str, cred_type: str) -> str:
        """Retrieve a credential from environment variables.

        Args:
            website_name: Name of the website
            cred_type: Type of credential

        Returns:
            str: The credential value

        Raises:
            KeyError: If credential not found
        """
        env_key = self._make_env_key(website_name, cred_type)
        if env_key not in os.environ:
            raise KeyError(f"Environment variable '{env_key}' not found")

        return os.environ[env_key]

    def delete_credential(self, website_name: str, cred_type: str) -> bool:
        """Delete a credential from environment variables.

        Args:
            website_name: Name of the website
            cred_type: Type of credential

        Returns:
            bool: True if deletion successful, False if credential not found
        """
        env_key = self._make_env_key(website_name, cred_type)
        if env_key not in os.environ:
            return False

        del os.environ[env_key]
        return True

    def list_credentials(self, website_name: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """List credentials from environment variables.

        Args:
            website_name: Optional website name to filter by

        Returns:
            Dict[str, Dict[str, str]]: Dictionary of credentials by website
        """
        result = {}

        for env_key, value in os.environ.items():
            site_name, cred_type = self._parse_env_key(env_key)

            if not site_name or not cred_type:
                continue

            if website_name and site_name != website_name.lower():
                continue

            if site_name not in result:
                result[site_name] = {}

            result[site_name][cred_type] = value

        return result


def register_backend():
    """Register the environment backend with the BackendManager."""
    BackendManager.register_backend(
        "env",
        EnvironmentBackend,
        "Environment variable-based storage for credentials (non-persistent)",
    )
