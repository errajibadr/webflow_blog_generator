"""
File-based Credential Backend

This module provides a file-based backend for credential storage with encryption.
"""

import base64
import json
import logging
import os
import secrets
from pathlib import Path
from typing import Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from modules.credentials.manager import BackendManager
from modules.credentials.types import CredentialBackend, CredentialStorageError, EncryptionError

# Configure logging
logger = logging.getLogger(__name__)


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


def register_backend():
    """Register the file backend with the BackendManager."""
    BackendManager.register_backend(
        "file", FileBackend, "Encrypted file-based storage for credentials"
    )
