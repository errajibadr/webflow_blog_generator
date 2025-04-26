"""
Command Line Interface module for Website SEO Orchestrator.

This module handles command line argument parsing and provides CLI utilities.
"""

from .parser import (
    get_steps_from_args,
    handle_credential_backend,
    handle_credential_management,
    parse_args,
)

__all__ = [
    "parse_args",
    "get_steps_from_args",
    "handle_credential_backend",
    "handle_credential_management",
]
