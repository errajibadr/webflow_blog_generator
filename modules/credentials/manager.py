"""
Credential Backend Manager Module

This module provides the BackendManager class for managing different credential storage backends.
"""

import logging
from typing import Any, Dict, List, Optional, Type

from modules.credentials.types import CredentialBackend

# Configure logging
logger = logging.getLogger(__name__)


class BackendManager:
    """Manages credential backend selection and configuration."""

    _backends = {}
    _current_backend = None
    _backend_instances = {}

    @classmethod
    def register_backend(
        cls, backend_type: str, backend_class: Type[CredentialBackend], description: str = ""
    ):
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
