"""
Configuration management module for Website SEO Orchestrator.

This module handles loading, processing, and accessing configuration for the orchestrator.
"""

from .loader import ConfigDict, ensure_workspace_dirs, expand_env_vars, load_config
from .logging import set_verbosity, setup_logging

__all__ = [
    "load_config",
    "expand_env_vars",
    "ensure_workspace_dirs",
    "setup_logging",
    "set_verbosity",
    "ConfigDict",
]
