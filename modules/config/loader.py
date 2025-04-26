"""
Configuration loading and processing for Website SEO Orchestrator.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from dotenv import load_dotenv

# Import credential manager
from modules.credentials import get_credential

# Load environment variables from .env file
load_dotenv()

# Configuration types
ConfigDict = Dict[str, Any]


def load_config(config_path: Union[str, Path], website_name: Optional[str] = None) -> ConfigDict:
    """
    Load main config and optionally a website-specific config.

    Args:
        config_path: Path to the main configuration file
        website_name: Name of the website to load config for

    Returns:
        Merged configuration dictionary

    Raises:
        FileNotFoundError: If the website config file doesn't exist
    """
    # Load main config
    with open(config_path, "r") as f:
        config: ConfigDict = yaml.safe_load(f)

    if website_name:
        # Load website config
        website_config_path = Path("website_configs") / f"{website_name}.yaml"
        if not website_config_path.exists():
            raise FileNotFoundError(f"Website config not found: {website_config_path}")

        with open(website_config_path, "r") as f:
            website_config = yaml.safe_load(f)

        # Merge website config with main config
        config["website"] = website_config

    # Expand environment variables in config
    config = expand_env_vars(config)

    return config


def expand_env_vars(value: Any) -> Any:
    """Recursively expand environment variables and credential references in the given value.

    Supports the formats:
    - ${ENV_VAR}
    - ${env:ENV_VAR}
    - ${cred:WEBSITE_CRED_TYPE}

    Args:
        value: The value to process (can be dict, list, or string)

    Returns:
        Any: The processed value with environment variables expanded
    """
    # Handle different value types
    if isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(v) for v in value]
    elif isinstance(value, str):
        # First try our specific formats
        def replace_var(match):
            full_match = match.group(0)
            var_type = match.group(1) if match.group(1) else "env"
            var_name = match.group(2)

            if var_type == "env":
                # Standard environment variable
                return os.environ.get(var_name, "")
            elif var_type == "cred":
                # Credential reference format: ${cred:WEBSITE_CRED_TYPE}
                parts = var_name.split("_", 1)
                if len(parts) != 2:
                    logging.warning(f"Invalid credential reference format: {full_match}")
                    return ""

                website, cred_type = parts
                try:
                    return get_credential(website, cred_type)
                except Exception as e:
                    logging.error(f"Error retrieving credential: {e}")
                    return ""

            return os.environ.get(var_name, "")

        # Match ${var}, ${env:var} or ${cred:var}
        pattern = r"\${(?:(env|cred):)?([A-Za-z0-9_]+)}"
        value = re.sub(pattern, replace_var, value)

        # Then try standard format as fallback
        return os.path.expandvars(value)
    else:
        return value


def ensure_workspace_dirs(config: ConfigDict, website_name: str) -> Path:
    """
    Create necessary workspace directories for a website.

    Args:
        config: The loaded configuration
        website_name: Name of the website

    Returns:
        Path to the workspace directory
    """
    logger = logging.getLogger("orchestrator")

    # Get workspace directory
    workspace_name = config["website"]["website"].get("workspace", website_name)
    workspace_dir = Path(config["paths"]["workspaces"]) / workspace_name

    # Create workspace subdirectories
    for subdir in ["export", "content", "output"]:
        dir_path = workspace_dir / subdir
        os.makedirs(dir_path, exist_ok=True)
        logger.debug(f"Ensured directory exists: {dir_path}")

    return workspace_dir
