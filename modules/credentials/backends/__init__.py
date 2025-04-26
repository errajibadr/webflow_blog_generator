"""
Credential Backend Package

This package contains various credential backend implementations.
The __init__ file handles backend registration and discovery.
"""

import importlib
import logging
import os
from typing import List

from modules.credentials.manager import BackendManager

# Configure logging
logger = logging.getLogger(__name__)

# List of built-in backend modules that should be automatically loaded
_BUILTIN_BACKENDS = ["file", "env"]


def register_backends() -> List[str]:
    """Discover and register all available credential backends.

    Returns:
        List[str]: List of registered backend types
    """
    registered = []

    # Register built-in backends
    for backend_name in _BUILTIN_BACKENDS:
        try:
            module_name = f"modules.credentials.backends.{backend_name}"
            module = importlib.import_module(module_name)

            # Each backend module should have a register_backend function
            if hasattr(module, "register_backend"):
                module.register_backend()
                registered.append(backend_name)
                logger.debug(f"Registered built-in backend: {backend_name}")
            else:
                logger.warning(f"Backend module {module_name} has no register_backend function")
        except ImportError as e:
            logger.warning(f"Failed to import backend {backend_name}: {e}")
        except Exception as e:
            logger.warning(f"Error registering backend {backend_name}: {e}")

    return registered


# Register backends when the module is imported
registered_backends = register_backends()
