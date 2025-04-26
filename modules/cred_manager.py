"""
Credential Manager Module for secure FTP credential storage.

This module provides a secure way to store and retrieve FTP credentials
using pluggable backend storage mechanisms.
"""

import base64
import json
import logging
import os
import secrets
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Import cryptography for encryption


# Configure logging
logger = logging.getLogger(__name__)


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


class BackendManager:
    """Manages credential backend selection and configuration."""

    _backends = {}
    _current_backend = None
    _backend_instances = {}

    @classmethod
    def register_backend(cls, backend_type: str, backend_class, description: str = ""):
        """Register a backend type with the manager.

        Args:
            backend_type: String identifier for the backend
            backend_class: Class implementing CredentialBackend
            description: Human-readable description of the backend
        """
        cls._backends[backend_type] = {"class": backend_class, "description": description}

    @classmethod
    def get_backend(cls, backend_type: Optional[str] = None, **config) -> CredentialBackend:
        """Get or create a backend instance.

        Args:
            backend_type: Backend type to use (or None for current/default)
            **config: Configuration options for the backend

        Returns:
            CredentialBackend: The configured backend instance

        Raises:
            ValueError: If backend type is invalid
        """
        if backend_type is None:
            backend_type = cls._current_backend or "file"  # Default to file

        if backend_type not in cls._backends:
            raise ValueError(f"Unknown backend type: {backend_type}")

        # Create new instance with config if needed
        if backend_type not in cls._backend_instances or config:
            backend_class = cls._backends[backend_type]["class"]
            cls._backend_instances[backend_type] = backend_class(**config)
            cls._current_backend = backend_type

        return cls._backend_instances[backend_type]

    @classmethod
    def list_available_backends(cls) -> List[Dict[str, Any]]:
        """List all available backends.

        Returns:
            List[Dict[str, Any]]: Information about available backends
        """
        result = []
        for key, info in cls._backends.items():
            result.append(
                {
                    "name": key,
                    "description": info["description"],
                    "current": key == cls._current_backend,
                }
            )
        return result


class FileBackend(CredentialBackend):
    """File-based credential storage backend with encryption."""

    def __init__(self, file_path: str = ".env.encrypted", key_source: str = "env"):
        """Initialize the file backend.

        Args:
            file_path: Path to the encrypted credentials file
            key_source: Source for encryption key ("env", "file", or "generate")
        """

        self.file_path = os.path.expanduser(file_path)
        self.credentials = {}
        self.key = self._get_encryption_key(key_source)
        self.fernet = Fernet(self.key)
        self._load_credentials()

    def _get_encryption_key(self, key_source: str) -> bytes:
        """Get or generate the encryption key.

        Args:
            key_source: Source for the key ("env", "file", or "generate")

        Returns:
            bytes: The encryption key

        Raises:
            EncryptionError: If key cannot be obtained
        """
        if key_source == "env":
            # Get from environment variable
            key = os.environ.get("CRED_ENCRYPTION_KEY")
            if key:
                try:
                    # Add padding if needed
                    padding = len(key) % 4
                    if padding:
                        key += "=" * (4 - padding)
                    return key.encode()
                except Exception as e:
                    raise EncryptionError(f"Invalid encryption key format: {e}")

        elif key_source == "file":
            # Get from key file
            key_file = os.path.expanduser("~/.cred_key")
            if os.path.exists(key_file):
                try:
                    with open(key_file, "rb") as f:
                        return f.read().strip()
                except Exception as e:
                    raise EncryptionError(f"Error reading key file: {e}")

        # If we got here, generate a new key
        logger.info("Generating new encryption key")
        key = Fernet.generate_key()

        # Save the key
        if key_source == "env":
            logger.warning(
                "Generated new encryption key. Set CRED_ENCRYPTION_KEY environment "
                "variable to this value for future runs:\n%s",
                key.decode(),
            )
        elif key_source == "file":
            try:
                os.makedirs(os.path.dirname(os.path.expanduser("~/.cred_key")), exist_ok=True)
                with open(os.path.expanduser("~/.cred_key"), "wb") as f:
                    f.write(key)
                os.chmod(os.path.expanduser("~/.cred_key"), 0o600)  # Restrictive permissions
                logger.info("Saved encryption key to ~/.cred_key")
            except Exception as e:
                logger.error("Failed to save encryption key: %s", e)
                logger.warning(
                    "Store this encryption key manually for future use:\n%s", key.decode()
                )

        return key

    def _load_credentials(self) -> None:
        """Load credentials from the encrypted file.

        Raises:
            EncryptionError: If decryption fails
        """
        if not os.path.exists(self.file_path):
            self.credentials = {}
            return

        try:
            with open(self.file_path, "rb") as f:
                encrypted_data = f.read().strip()

            if not encrypted_data:
                self.credentials = {}
                return

            decrypted_data = self.fernet.decrypt(encrypted_data).decode("utf-8")
            self.credentials = json.loads(decrypted_data)
        except Exception as e:
            raise EncryptionError(f"Failed to load credentials: {e}")

    def _save_credentials(self) -> None:
        """Save credentials to the encrypted file.

        Raises:
            EncryptionError: If encryption or file write fails
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(self.file_path)), exist_ok=True)

            # Encrypt and save
            encrypted_data = self.fernet.encrypt(json.dumps(self.credentials).encode("utf-8"))

            with open(self.file_path, "wb") as f:
                f.write(encrypted_data)

            # Set restrictive file permissions
            os.chmod(self.file_path, 0o600)
        except Exception as e:
            raise EncryptionError(f"Failed to save credentials: {e}")

    def store_credential(self, website_name: str, cred_type: str, value: str) -> bool:
        """Store a credential in the file.

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
            # Initialize website dict if needed
            if website_name not in self.credentials:
                self.credentials[website_name] = {}

            # Store the credential
            self.credentials[website_name][cred_type] = value

            # Save to file
            self._save_credentials()
            return True
        except Exception as e:
            raise CredentialStorageError(f"Failed to store credential: {e}")

    def get_credential(self, website_name: str, cred_type: str) -> str:
        """Retrieve a credential from the file.

        Args:
            website_name: Name of the website
            cred_type: Type of credential

        Returns:
            str: The credential value

        Raises:
            KeyError: If credential not found
        """
        if website_name not in self.credentials:
            raise KeyError(f"Website '{website_name}' not found")

        if cred_type not in self.credentials[website_name]:
            raise KeyError(f"Credential '{cred_type}' not found for website '{website_name}'")

        return self.credentials[website_name][cred_type]

    def delete_credential(self, website_name: str, cred_type: str) -> bool:
        """Delete a credential from the file.

        Args:
            website_name: Name of the website
            cred_type: Type of credential

        Returns:
            bool: True if deletion successful, False if credential not found

        Raises:
            CredentialStorageError: If deletion fails
        """
        if website_name not in self.credentials:
            return False

        if cred_type not in self.credentials[website_name]:
            return False

        try:
            # Delete the credential
            del self.credentials[website_name][cred_type]

            # Remove empty website entry
            if not self.credentials[website_name]:
                del self.credentials[website_name]

            # Save changes
            self._save_credentials()
            return True
        except Exception as e:
            raise CredentialStorageError(f"Failed to delete credential: {e}")

    def list_credentials(self, website_name: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """List credentials in the file.

        Args:
            website_name: Optional website name to filter by

        Returns:
            Dict[str, Dict[str, str]]: Dictionary of credentials by website
        """
        if website_name:
            if website_name not in self.credentials:
                return {}
            return {website_name: self.credentials[website_name]}

        # Return a copy to prevent accidental modification
        return dict(self.credentials)


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

    def _parse_env_key(self, env_key: str) -> tuple:
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


# Register the backends
BackendManager.register_backend("file", FileBackend, "Encrypted file-based storage for credentials")

BackendManager.register_backend(
    "env", EnvironmentBackend, "Environment variable-based storage for credentials (non-persistent)"
)


# Factory functions for credential management


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


# Utility functions for CLI


def manage_credentials(
    action: str,
    website: Optional[str] = None,
    cred_type: Optional[str] = None,
    value: Optional[str] = None,
    interactive: bool = False,
    force: bool = False,
    show_values: bool = False,
    host: Optional[str] = None,
) -> str:
    """Manage credentials from the CLI.

    Args:
        action: Action to perform (add, remove, list, test)
        website: Website name
        cred_type: Credential type
        value: Credential value
        interactive: Whether to prompt for credential value
        force: Whether to skip confirmation for dangerous actions
        show_values: Whether to show credential values when listing
        host: Override host for testing

    Returns:
        str: Result message
    """
    try:
        if action == "add":
            if not website:
                return "Error: Website name is required"

            if not cred_type:
                return "Error: Credential type is required"

            if interactive and not value:
                import getpass

                prompt = f"Enter {cred_type} for {website}: "
                if cred_type and "PASSWORD" in cred_type.upper():
                    value = getpass.getpass(prompt)
                else:
                    value = input(prompt)

            if not value:
                return "Error: Credential value is required"

            store_credential(website, cred_type, value)
            return f"Credential {website}/{cred_type} stored successfully"

        elif action == "remove":
            if not website:
                return "Error: Website name is required"

            if not force:
                confirmation = input(
                    f"Are you sure you want to delete credential(s) for {website}"
                    + (f"/{cred_type}" if cred_type else "")
                    + "? (y/N): "
                )
                if confirmation.lower() not in ("y", "yes"):
                    return "Operation cancelled"

            if cred_type:
                # Delete specific credential
                if delete_credential(website, cred_type):
                    return f"Credential {website}/{cred_type} deleted successfully"
                else:
                    return f"Credential {website}/{cred_type} not found"
            else:
                # Delete all credentials for website
                credentials = list_credentials(website)
                if not credentials or website not in credentials:
                    return f"No credentials found for {website}"

                count = 0
                for cred_type_name in list(credentials[website].keys()):
                    if delete_credential(website, cred_type_name):
                        count += 1

                return f"Deleted {count} credential(s) for {website}"

        elif action == "list":
            credentials = list_credentials(website)

            if not credentials:
                return "No credentials found"

            lines = ["Available credentials:"]

            for site, creds in credentials.items():
                lines.append(f"- {site}:")
                for cred_type_name, cred_value in creds.items():
                    if show_values:
                        if not force:
                            confirmation = input(
                                "Show credential values? This is insecure and "
                                + "should only be done in a secure environment. (y/N): "
                            )
                            if confirmation.lower() not in ("y", "yes"):
                                return "Operation cancelled"

                        if "PASSWORD" in cred_type_name:
                            display_value = (
                                f"{cred_value[0]}{'*' * (len(cred_value) - 2)}{cred_value[-1]}"
                                if len(cred_value) > 2
                                else "****"
                            )
                        else:
                            display_value = cred_value

                        lines.append(f"  - {cred_type_name}: {display_value}")
                    else:
                        lines.append(f"  - {cred_type_name}")

            return "\n".join(lines)

        elif action == "test":
            if not website:
                return "Error: Website is required for testing"

            try:
                username = get_credential(website, "FTP_USERNAME")
                password = get_credential(website, "FTP_PASSWORD")

                # Get host from config if not provided
                if not host:
                    # This would need to be updated to get from config
                    return "Error: Host is required for testing (use --host)"

                # Test FTP connection
                import ftplib

                with ftplib.FTP() as ftp:
                    ftp.connect(host)
                    ftp.login(username, password)
                    ftp.quit()

                return f"FTP connection to {host} successful using credentials for {website}"

            except Exception as e:
                return f"FTP connection failed: {str(e)}"

        elif action == "configure":
            return configure_website_credentials(website, force)

        else:
            return f"Unknown action: {action}"

    except Exception as e:
        return f"Error: {str(e)}"


def configure_website_credentials(website_name: Optional[str] = None, force: bool = False) -> str:
    """Configure all necessary credentials for a website interactively.

    This function will prompt for FTP username and password for a website
    and store them securely in the credential manager.

    Args:
        website_name: Name of the website to configure
        force: Whether to overwrite existing credentials without confirmation

    Returns:
        str: Result message
    """
    import getpass

    if not website_name:
        return "Error: Website name is required"

    website_name = website_name.lower().strip()

    # Check if credentials already exist
    try:
        existing_creds = list_credentials(website_name)
        if existing_creds and website_name in existing_creds:
            if not force:
                confirmation = input(
                    f"Credentials already exist for {website_name}. Overwrite? (y/N): "
                )
                if confirmation.lower() not in ("y", "yes"):
                    return "Configuration cancelled"
    except Exception:
        # If there's an error checking credentials, proceed anyway
        pass

    print(f"\nConfiguring FTP credentials for {website_name}")
    print("============================================")

    # Prompt for username
    username = input(f"Enter FTP username for {website_name}: ")
    if not username:
        return "Error: Username cannot be empty"

    # Prompt for password
    password = getpass.getpass(f"Enter FTP password for {website_name}: ")
    if not password:
        return "Error: Password cannot be empty"

    # Store the credentials
    try:
        store_credential(website_name, "FTP_USERNAME", username)
        store_credential(website_name, "FTP_PASSWORD", password)

        return f"Successfully configured credentials for {website_name}"
    except Exception as e:
        return f"Error storing credentials: {str(e)}"
